"""Simple flask app to send requests to BitBot."""
import constants
import datetime
import flask
import manager
import math
import os
from algos import mean_reversion
from db import db
from db import models

# initialize flask app
app = flask.Flask(__name__)

# initialize mongodb
mongodb = db.BitBotDB(app)

@app.route("/balance")
def accountBalance():
	"""Get current Kraken account balance in USD."""
	try:
		balance = manager.getAccountBalance()
	except Exception as err:
		return _failedResp(err)
	return _successResp({"balance": balance})

@app.route("/backfill/<filename>")
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
	entries = list(mongodb.find("price", queryFilter))
	if entries:
		return _failedResp("unable to backfill: %i price snapshots already exist for %s" % (len(entries), ticker), 400)  # 400 bad request

	# save to database
	try:
		mongodb.insertMany(newPriceModels)
	except Exception as err:
		return _failedResp("unable to insert price models: %s" % repr(err))
	else:
		return _successResp("successfully backfilled %i prices" % len(newPriceModels))

@app.route("/balance/<ticker>")
def balance(ticker):
	"""Get current balance of a cryptocurrency."""
	try:
		balance = manager.getBalance(ticker)
	except Exception as err:
		return _failedResp(err)
	return _successResp({"ticker": ticker, "balance": balance})

@app.route("/crunch/<ticker>")
def crunch(ticker):
	"""Crunch numbers to decide if a cryptocurrency should be bought."""
	# ensure bitbot supports this crypto
	if ticker not in constants.KRAKEN_CRYPTO_TICKERS.keys():
		return _failedResp("ticker not supported: %s" % ticker, 400)  # 400 bad request

	# determine if crypto should be bought
	mreNumbers = _getMRENumbers(ticker)
	shouldBuy = mreNumbers["current_price_deviation"] >= constants.DEVIATION_THRESHOLD
	confidence = round(min(abs((1.0 / constants.DEVIATION_THRESHOLD * mreNumbers["current_price_deviation"]) - 1.0), constants.MAX_CONFIDENCE), constants.CONFIDENCE_DECIMALS)

	# add alert to db if should buy
	if shouldBuy:
		currentPrice = mreNumbers["current_price"]
		newAlert = models.Alert(ticker, currentPrice, alertType="buy")
		mongodb.insert(newAlert)

	return _successResp({"should_buy": shouldBuy,
						 "confidence": confidence,
						 "deviation_threshold": constants.DEVIATION_THRESHOLD,
						 "numbers": mreNumbers})


@app.route("/mre/<ticker>")
def meanReversion(ticker):
	"""Average price of a cryptocurrency."""
	# ensure bitbot supports this crypto
	if ticker not in constants.KRAKEN_CRYPTO_TICKERS.keys():
		return _failedResp("ticker not supported: %s" % ticker, 400)  # 400 bad request

	# return mean reversion numbers
	return _successResp(_getMRENumbers(ticker))

@app.route("/")
def root():
	"""Root endpoint of the app."""
	return "Hello, world!"

@app.route("/snapshot/<ticker>")
def snapshot(ticker):
	"""Store the price of a cryptocurrency."""
	# ensure bitbot supports this crypto
	if ticker not in constants.KRAKEN_CRYPTO_TICKERS.keys():
		return _failedResp("ticker not supported: %s" % ticker, 400)  # 400 bad request

	# ensure price snapshot doesn't already exist for today
	currentDate = datetime.datetime.now().strftime("%Y-%m-%d")
	queryFilter = {"date": currentDate, "ticker": ticker}
	entry = list(mongodb.find("price", queryFilter))
	if entry:
		return _failedResp("%s price snapshot already exists for %s: %s" % (ticker, currentDate, repr(entry[0])), 400)  # 400 bad request

	# fetch relevant prices
	try:
		allPrices = manager.getAllPrices(ticker)
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
	entries = list(mongodb.find("price", queryFilter))

	# calculate standard and current price deviations
	prices = [entry["open"] for entry in entries]
	currentPrice = manager.getPrice(ticker, "ask")
	meanReversion = mean_reversion.MeanReversion(currentPrice, prices)
	averagePrice, standardDeviation, currentDeviation = meanReversion.getPriceDeviation()
	currentPriceDeviation = currentDeviation / standardDeviation

	return {"lookback_days": constants.LOOKBACK_DAYS,
			"ticker": ticker,
			"average_price": averagePrice,
			"standard_deviation": standardDeviation,
			"current_price": currentPrice,
			"current_price_deviation": currentPriceDeviation}

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
