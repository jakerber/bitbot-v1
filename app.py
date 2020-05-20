"""Simple flask app to send requests to BitBot."""
import constants
import datetime
import flask
import logger
import manager
import math
import os
from algos import mre
from db import db
from db import models

# initialize flask app
app = flask.Flask(__name__)

# initialize mongodb
mongodb = db.BitBotDB(app)

# initialize logger
logger = logger.Logger("app")

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
	"""Backfill price history based on CSV dataset."""
	filepath = "datasets/%s" % filename
	if not os.path.exists(filepath):
		return _failedResp("dataset does not exist: %s" % filename)

	# parse prices from dataset
	headerLine = True
	entriesAdded = 0
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
			newPriceModel.time = "00:00:00.000000"

			# save to database
			try:
				mongodb.insert(newPriceModel)
			except Exception as err:
				logger.log(repr(err))
				return _failedResp("unable to insert price model: %s" % repr(err))
			else:
				entriesAdded += 1

		return _successResp("successfully backfilled %i prices" % entriesAdded)


@app.route("/mre/<ticker>/<days>")
def meanReversion(ticker, days):
	"""Average price of a cryptocurrency."""
	try:
		days = int(days)
		1 / days
	except (ValueError, ZeroDivisionError):
		return _failedResp("invalid number of days provided: %s" % days)

	# ensure bitbot supports this crypto
	if ticker not in constants.KRAKEN_CRYPTO_TICKERS.keys():
		return _failedResp("ticker not supported: %s" % ticker)

	# collect dates from past number of days
	dates = []
	now = datetime.datetime.now()
	for daysAgo in range(days):
		delta = datetime.timedelta(days=daysAgo)
		dateDaysAgo = now - delta
		dates.append(dateDaysAgo.strftime("%Y-%m-%d"))

	# fetch prices on dates
	queryFilter = {"date": {"$in": dates}, "ticker": ticker}
	entries = list(mongodb.find("price", queryFilter))
	if not entries:
		return _failedResp("no price data for %s" % ticker)

	# calculate standard and current price deviations
	prices = [entry["open"] for entry in entries]
	currentPrice = manager.getPrice(ticker, "ask")
	meanReversion = mre.MeanReversion(currentPrice, prices)
	averagePrice, standardDeviation, currentDeviation = meanReversion.getPriceDeviation()
	currentPriceDeviation = currentDeviation / standardDeviation

	return _successResp({"lookback days": days,
						 "ticker": ticker,
						 "average price": averagePrice,
						 "standard deviation": standardDeviation,
						 "current price": currentPrice,
						 "current price deviation": currentPriceDeviation})

@app.route("/balance/<ticker>")
def balance(ticker):
	"""Get current balance of a cryptocurrency."""
	try:
		balance = manager.getBalance(ticker)
	except Exception as err:
		return _failedResp(err)
	return _successResp({"ticker": ticker, "balance": balance})

@app.route("/")
def root():
	"""Root endpoint of the app."""
	return "Hello, world!"

@app.route("/snapshot/<ticker>")
def snapshot(ticker):
	"""Store the price of a cryptocurrency."""
	try:
		allPrices = manager.getAllPrices(ticker)
	except Exception as err:
		return _failedResp(err)

	# fetch and relevant prices
	openPrice = float(allPrices["o"])
	highPrice = float(allPrices["h"][0])
	lowPrice = float(allPrices["l"][0])

	# store relevant prices in database
	priceModel = models.Price(ticker, openPrice, highPrice, lowPrice)
	try:
		mongodb.insert(priceModel)
	except Exception as err:
		logger.log(repr(err))
		return _failedResp(err)

	logger.log("successfully inserted %s price snapshot: %s" % (ticker, repr(priceModel)))
	return _successResp(eval(repr(priceModel)))

def _successResp(resp):
	"""Successful request response."""
	return {"success": True, "resp": resp}

def _failedResp(error):
	"""Failed request response from an error."""
	if isinstance(error, Exception):
		error = repr(error)
	return {"success": False, "error": error}


if __name__ == "__main__":
	app.run()
