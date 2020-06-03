"""BitBot APIs."""
import constants
import datetime
import flask
import json
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

#################################
##  Public APIs
#################################

@app.route("%s/balance" % constants.API_ROOT)
def accountBalance():
	"""Get current Kraken account balance in USD."""
	try:
		balance = assistant.getAccountBalances()
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

@app.route("%s/analyze/<ticker>" % constants.API_ROOT)
def analyze(ticker):
	"""Analyze the price deviations of a cryptocurrency."""
	# ensure bitbot supports this crypto
	if ticker not in constants.SUPPORTED_CRYPTOS:
		return _failedResp("ticker not supported: %s" % ticker, 400)  # 400 bad request

	# return price deviation analysis
	return _successResp({"ticker": ticker, "analysis": getMeanReversionAnalysis(ticker).__dict__})

@app.route("%s/analyze" % constants.API_ROOT)
def analyzeAll():
	"""Analyze the price deviations of all supported cryptocurrencies."""
	analysis = []
	for ticker in constants.SUPPORTED_CRYPTOS:
		try:
			analysis.append({"ticker": ticker, "analysis": getMeanReversionAnalysis(ticker).__dict__})
		except Exception as err:
			analysis.append({"ticker": ticker, "error": repr(err)})

	# return price deviation analysis
	return _successResp(analysis)

@app.route("/")
def root():
	"""Root endpoint of the app."""
	return "<h4>bleep bloop<h4>"

@app.route("%s/" % constants.API_ROOT)
def rootApi():
	"""Root endpoint of the api."""
	return "<h4>api root<h4>"

#################################
##  Private APIs
#################################

def trade():
	"""Trade cryptocurrency to achieve profit."""
	# analyze price deviation from the mean for all supported cryptos
	ordersExecuted = {}
	for ticker in constants.SUPPORTED_CRYPTOS:
		try:
			analysis = getMeanReversionAnalysis(ticker)
		except Exception as err:
			continue

		# trade if price deviation thresholds are met
		if shouldTrade(analysis.current_percent_deviation):
			tradeAmount = constants.BASE_BUY_USD / analysis.current_price
			if analysis.average_price > analysis.current_price:
				tradeFunc = assistant.buy
				priceTarget = analysis.current_price + analysis.standard_deviation
			else:
				tradeFunc = assistant.short
				priceTarget = analysis.current_price - analysis.standard_deviation

			# safetly execute trade
			try:
				orderDescription = tradeFunc(ticker, tradeAmount, priceLimit=analysis.current_price, priceTarget=priceTarget)
				logger.log(orderDescription)
				logger.log("trade successfully executed", moneyExchanged=True)
			except Exception as err:
				logger.log("unable to execute %s trade: %s" % (ticker, str(err)))

def sendDailySummary():
	"""Sends a daily activity summary email."""
	accountBalances = assistant.getAccountBalances()
	accountValue = assistant.getAccountValue()

	# fetch trades that were executed today
	datetimeDayAgo = datetime.datetime.now() - datetime.timedelta(days=1)
	tradesExecuted = assistant.getTradeHistory(startDatetime=datetimeDayAgo)

	# only send summary email if trades were executed today
	if not tradesExecuted:
		return

	# notify via email
	emailSubject = "Daily Summary: %s" % datetime.datetime.now().strftime("%Y-%m-%d")
	emailBody = "Account value:"
	emailBody += "\n$%f" % accountValue
	emailBody += "\n\nAccount balances:"
	emailBody += "\n" + json.dumps(accountBalances, indent=6)
	emailBody += "\n\nTrades executed:"
	emailBody += "\n" + json.dumps(tradesExecuted, indent=6)
	notifier.email(emailSubject, emailBody)

def snapshotPrices():
	"""Store the prices of all supported cryptocurrency."""
	snapshots = []
	for ticker in constants.SUPPORTED_CRYPTOS:

		# ensure price doesn't already exist for today
		currentDate = datetime.datetime.now().strftime("%Y-%m-%d")
		queryFilter = {"date": currentDate, "ticker": ticker}
		entry = mongodb.find("price", queryFilter)
		if entry:
			logger.log("%s price snapshot already exists for %s: %s" % (ticker, currentDate, repr(entry[0])))
			continue

		# fetch relevant prices
		try:
			allPrices = assistant.getAllPrices(ticker)
		except Exception as err:
			logger.log("unable to fetch prices of %s: %s" % (ticker, repr(err)))
			continue
		openPrice = float(allPrices["o"])
		highPrice = float(allPrices["h"][0])
		lowPrice = float(allPrices["l"][0])

		# store relevant prices in database
		priceModel = models.Price(ticker, openPrice, highPrice, lowPrice)
		try:
			mongodb.insert(priceModel)
		except Exception as err:
			logger.log("unable to add %s price snapshot to the database: %s" % (ticker, repr(err)))

###############################
##  Helper functions
###############################

def getMeanReversionAnalysis(ticker):
	"""Get mean reversion analysis (standard deviation, etc.)."""
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

	# calculate and return price deviations
	prices = [entry["open"] for entry in entries]
	currentPrice = assistant.getPrice(ticker, "ask")
	return mean_reversion.MeanReversion(currentPrice, prices).analyze()

def shouldTrade(currentPercentDeviation):
	"""Determine if a cryptocurrency should be traded."""
	return constants.PERCENT_DEVIATION_THRESHOLD_MAX >= currentPercentDeviation >= constants.PERCENT_DEVIATION_THRESHOLD_MIN

###############################
##  Response formatting
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
	app.run(debug=True)
