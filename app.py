"""Simple flask app to send requests to BitBot."""
import constants
import datetime
import flask
import logger
import assistant
import math
import notifier
import os
import simulator
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

@app.route("%s/crunch" % constants.API_ROOT)
def crunch():
	"""Crunch numbers to decide if cryptocurrency should be bought."""
	# determine which cryptos should be bought
	actionableMres = []
	for ticker in constants.SUPPORTED_CRYPTOS:
		try:
			mreNumbers = getMRENumbers(ticker)
		except Exception as err:
			continue
		if mreNumbers["current_percent_deviation"] >= constants.PERCENT_DEVIATION_THRESHOLD:
			actionableMres.append({"ticker": ticker, "mre": mreNumbers})

	# alert of actionable mean reversions
	for actionableMre in actionableMres:
		mreNumbers = actionableMre["mre"]
		ticker = actionableMre["ticker"]
		currentPrice = mreNumbers["current_price"]
		averagePrice = mreNumbers["average_price"]
		standardDeviation = mreNumbers["standard_deviation"]

		# set price target to half of threshold away from average
		if averagePrice > currentPrice:
			alertType = "buy"
			priceTarget = currentPrice + (standardDeviation * constants.PERCENT_DEVIATION_THRESHOLD * constants.PRICE_TARGET_MULTIPLIER)
		else:
			alertType = "sell"
			priceTarget = currentPrice - (standardDeviation * constants.PERCENT_DEVIATION_THRESHOLD * constants.PRICE_TARGET_MULTIPLIER)
		logger.log("%s alert: %s @ %f" % (alertType, ticker, currentPrice), seperate=True)
		mreNumbers["action"] = alertType

		# add alert to db
		newAlert = models.Alert(ticker, currentPrice, alertType, priceTarget)
		mongodb.insert(newAlert)

		# send email notification
		emailSubject = "%s %s alert!" % (ticker, alertType)
		emailBody = "This is an automated %s %s alert. %s is currently priced at $%f with a price target of $%f. Please visit https://bit-bot-ai.herokuapp.com/api/mre/%s or check alerts in the BitBot database for more info." % (ticker, alertType, ticker, currentPrice, averagePrice, ticker)
		notifier.email(emailSubject, emailBody)

	return _successResp({"actionable": actionableMres,
						 "percent_deviation_threshold": constants.PERCENT_DEVIATION_THRESHOLD})

@app.route("%s/mre/<ticker>" % constants.API_ROOT)
def meanReversion(ticker):
	"""Get mean reversion data for a cryptocurrency."""
	# ensure bitbot supports this crypto
	if ticker not in constants.SUPPORTED_CRYPTOS:
		return _failedResp("ticker not supported: %s" % ticker, 400)  # 400 bad request

	# return mean reversion numbers
	return _successResp({"ticker": ticker, "mre": getMRENumbers(ticker)})

@app.route("%s/mre" % constants.API_ROOT)
def meanReversionAll():
	"""Get mean reversion data for all supported cryptocurrencies."""
	mreNumbers = []
	for ticker in constants.SUPPORTED_CRYPTOS:
		try:
			mreNumbers.append({"ticker": ticker, "mre": getMRENumbers(ticker)})
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

@app.route("%s/simulate" % constants.API_ROOT)
def simulateDocs():
	"""Display arguments for simulate API."""
	return _successResp({"name": "BitBot simulation API documentation",
						 "api_path": "/simulate/<days>/<lookback_days>/<percent_deviation_threshold>/<price_target_multiplier>",
						 "parameters": {"days": "numbers of days back from today to begin the simulation",
										"lookback_days": "number of days back to look when calculating average price each day",
										"percent_deviation_threshold": "percentage of the standard deviation the price needs to move to trigger a trade",
										"price_target_multiplier": "number between 0 - 1 to multiply percent_deviation_threshold by when calculating target price"}})

@app.route("%s/simulate/<days>/<lookbackDays>/<deviationThreshold>/<targetMultiplier>" % constants.API_ROOT)
def simulate(days, lookbackDays, deviationThreshold, targetMultiplier):
	"""Run a simulation using historical price data."""
	# validate inputs
	try:
		days = int(days)
		lookbackDays = int(lookbackDays)
		deviationThreshold = float(deviationThreshold)
		targetMultiplier = float(targetMultiplier)
		1 / days
		1 / lookbackDays
		1 / deviationThreshold
		1 / targetMultiplier
	except (ValueError, ZeroDivisionError) as err:
		return _failedResp("input invalid: %s" % repr(err), 400)  # 400 bad request

	# initialize and run simulation
	startingDatetime = datetime.datetime.now() - datetime.timedelta(days=days)
	return _successResp(simulator.Simulator(startingDatetime, lookbackDays, deviationThreshold, targetMultiplier).run())

@app.route("%s/snapshot" % constants.API_ROOT)
def snapshot():
	"""Store the prices of all supported cryptocurrency."""
	snapshots = []
	for ticker in constants.SUPPORTED_CRYPTOS:

		# ensure price doesn't already exist for today
		currentDate = datetime.datetime.now().strftime("%Y-%m-%d")
		queryFilter = {"date": currentDate, "ticker": ticker}
		entry = mongodb.find("price", queryFilter)
		if entry:
			error = "%s price snapshot already exists for %s: %s" % (ticker, currentDate, repr(entry[0]))
			snapshots.append({"ticker": ticker, "success": False, "error": error})
			continue

		# fetch relevant prices
		try:
			allPrices = assistant.getAllPrices(ticker)
		except Exception as err:
			snapshots.append({"ticker": ticker, "success": False, "error": repr(err)})
			continue
		openPrice = float(allPrices["o"])
		highPrice = float(allPrices["h"][0])
		lowPrice = float(allPrices["l"][0])

		# store relevant prices in database
		priceModel = models.Price(ticker, openPrice, highPrice, lowPrice)
		try:
			mongodb.insert(priceModel)
		except Exception as err:
			snapshots.append({"ticker": ticker, "success": False, "error": repr(err)})
		else:
			snapshots.append({"ticker": ticker, "success": True, "snapshot": repr(priceModel)})

	return _successResp(snapshots)

###############################
##  helper functions
###############################

def getMRENumbers(ticker, now=None):
	"""Get mean reversion numbers (standard deviation, etc.)."""
	# collect dates from past number of days
	dates = []
	now = now or datetime.datetime.now()  # allow sim to override current datetime
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
	return mean_reversion.MeanReversion(currentPrice, prices).calculate()

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
	app.run(debug=True)
