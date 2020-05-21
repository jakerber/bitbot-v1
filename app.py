"""Simple flask app to send requests to BitBot."""
import constants
import datetime
import flask
import logger
import assistant
import math
import notifier
import os
from algos import mean_reversion
from db import db
from db import models

# initialize flask app
app = flask.Flask(__name__)

# initialize mongodb
mongodb = db.BitBotDB(app)

# initialize logger
logger = logger.Logger("BitBot")

# initialize notifier
notifier = notifier.Notifier()

@app.route("%s/balance" % constants.API_ROOT)
def accountBalance():
	"""Get current Kraken account balance in USD."""
	try:
		balance = assistant.getAccountBalance()
	except Exception as err:
		return _failedResp(err)
	return _successResp({"balance": balance})

@app.route("%s/backfill/<filename>" % constants.API_ROOT)
def backfillCsv(filename):
	"""Backfill price history based on CSV dataset (https://coindesk.com/price/bitcoin)."""
	filepath = "datasets/%s" % filename
	if not os.path.exists(filepath):
		return _failedResp("dataset does not exist: %s" % filename, 400)  # 400 bad request

	# aggregate prices from dataset
	headerLine = True
	newPriceModels = []
	with open(filepath) as priceHistoryFile:
		for line in priceHistoryFile:
			if headerLine:
				headerLine = False
				continue

			# split fields in CSV
			fields = line.split(",")
			ticker = fields[0]
			date = fields[1]
			openPrice = float(fields[3])
			highPrice = float(fields[4])
			lowPrice = float(fields[5])

			# initialize new price model
			newPriceModel = models.Price(ticker, openPrice, highPrice, lowPrice)
			newPriceModel.date = date
			newPriceModels.append(newPriceModel)

	# ensure prices don't already exist for this crypto
	queryFilter = {"ticker": ticker}
	entries = mongodb.find("price", queryFilter)
	if entries:
		return _failedResp("unable to backfill: %i price snapshots already exist for %s" % (len(entries), ticker), 400)  # 400 bad request

	# save to database
	try:
		mongodb.insertMany(newPriceModels)
	except Exception as err:
		return _failedResp("unable to insert price models: %s" % repr(err))
	else:
		return _successResp("successfully backfilled %i prices" % len(newPriceModels))

@app.route("%s/balance/<ticker>" % constants.API_ROOT)
def balance(ticker):
	"""Get current balance of a cryptocurrency."""
	try:
		balance = assistant.getBalance(ticker)
	except Exception as err:
		return _failedResp(err)
	return _successResp({"ticker": ticker, "balance": balance})

@app.route("%s/crunch/<ticker>" % constants.API_ROOT)
def crunch(ticker):
	"""Crunch numbers to decide if a cryptocurrency should be bought."""
	# ensure bitbot supports this crypto
	if ticker not in constants.SUPPORTED_CRYPTOS:
		return _failedResp("ticker not supported: %s" % ticker, 400)  # 400 bad request

	# determine if crypto should be bought
	mreNumbers = _getMRENumbers(ticker)
	shouldBuy = mreNumbers["current_percent_deviation"] >= constants.PERCENT_DEVIATION_THRESHOLD

	# add alert to db if should buy
	if shouldBuy:
		currentPrice = mreNumbers["current_price"]
		logger.log("buy alert: %s @ %f" % (ticker, currentPrice), seperate=True)
		newAlert = models.Alert(ticker, currentPrice, alertType="buy", priceTarget=mreNumbers["average_price"])
		mongodb.insert(newAlert)

		# send email notification
		emailSubject = "%s buy alert!" % ticker
		emailBody = "This is an automated %s buy alert. %s is currently priced at $%f with a price target of $%f. Please visit https://bit-bot-ai.herokuapp.com/api/mre/%s or check alerts in the BitBot database for more info." % (ticker, ticker, currentPrice, mreNumbers["average_price"], ticker)
		notifier.email(emailSubject, emailBody)

	return _successResp({"should_buy": shouldBuy,
						 "percent_deviation_threshold": constants.PERCENT_DEVIATION_THRESHOLD,
						 "numbers": mreNumbers})

@app.route("%s/mre/<ticker>" % constants.API_ROOT)
def meanReversion(ticker):
	"""Get mean reversion data for a cryptocurrency."""
	# ensure bitbot supports this crypto
	if ticker not in constants.SUPPORTED_CRYPTOS:
		return _failedResp("ticker not supported: %s" % ticker, 400)  # 400 bad request

	# return mean reversion numbers
	return _successResp(_getMRENumbers(ticker))

@app.route("%s/mre" % constants.API_ROOT)
def meanReversionAll():
	"""Get mean reversion data for all supported cryptocurrencies."""
	mreNumbers = []
	for ticker in constants.SUPPORTED_CRYPTOS:
		try:
			mreNumbers.append(_getMRENumbers(ticker))
		except Exception as err:
			mreNumbers.append({"ticker": ticker, "error": repr(err)})

	# return all mean reversion numbers
	return _successResp(mreNumbers)

@app.route("/")
def root():
	"""Root endpoint of the app."""
	return "<h4>bleep bloop<h4>"

@app.route("%s/" % constants.API_ROOT)
def rootApi():
	"""Root endpoint of the api."""
	return "<h4>api root<h4>"

@app.route("%s/snapshot/<ticker>" % constants.API_ROOT)
def snapshot(ticker):
	"""Store the price of a cryptocurrency."""
	# ensure bitbot supports this crypto
	if ticker not in constants.SUPPORTED_CRYPTOS:
		return _failedResp("ticker not supported: %s" % ticker, 400)  # 400 bad request

	# ensure price snapshot doesn't already exist for today
	currentDate = datetime.datetime.now().strftime("%Y-%m-%d")
	queryFilter = {"date": currentDate, "ticker": ticker}
	entry = mongodb.find("price", queryFilter)
	if entry:
		return _failedResp("%s price snapshot already exists for %s: %s" % (ticker, currentDate, repr(entry[0])), 400)  # 400 bad request

	# fetch relevant prices
	try:
		allPrices = assistant.getAllPrices(ticker)
	except Exception as err:
		return _failedResp(err)
	openPrice = float(allPrices["o"])
	highPrice = float(allPrices["h"][0])
	lowPrice = float(allPrices["l"][0])

	# store relevant prices in database
	priceModel = models.Price(ticker, openPrice, highPrice, lowPrice)
	try:
		mongodb.insert(priceModel)
	except Exception as err:
		return _failedResp(err)

	return _successResp(eval(repr(priceModel)))

###############################
##  helper functions
###############################

def _getMRENumbers(ticker):
	"""Get mean reversion numbers (standard deviation, etc.)."""
	# collect dates from past number of days
	dates = []
	now = datetime.datetime.now()
	for daysAgo in range(constants.LOOKBACK_DAYS):
		delta = datetime.timedelta(days=daysAgo)
		dateDaysAgo = now - delta
		dates.append(dateDaysAgo.strftime("%Y-%m-%d"))

	# fetch prices on dates
	queryFilter = {"date": {"$in": dates}, "ticker": ticker}
	entries = mongodb.find("price", queryFilter)

	# calculate standard and current price deviations
	prices = [entry["open"] for entry in entries]
	currentPrice = assistant.getPrice(ticker, "ask")
	meanReversion = mean_reversion.MeanReversion(currentPrice, prices)
	averagePrice, standardDeviation, currentDeviation = meanReversion.getPriceDeviation()
	currentPercentDeviation = currentDeviation / standardDeviation

	return {"average_price": averagePrice,
			"current_deviation": currentDeviation,
			"current_percent_deviation": currentPercentDeviation,
			"current_price": currentPrice,
			"lookback_days": constants.LOOKBACK_DAYS,
			"standard_deviation": standardDeviation,
			"ticker": ticker}

###############################
##  response formatting
###############################

def _failedResp(error, statusCode=500):  # 500 internal server error
	"""Failed request response from an error."""
	if isinstance(error, Exception):
		error = repr(error)
	return {"success": False, "error": error}, statusCode

def _successResp(resp):
	"""Successful request response."""
	return {"success": True, "resp": resp}, 200


if __name__ == "__main__":
	app.run()
