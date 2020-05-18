"""Simple flask app to send requests to BitBot."""
import datetime
import flask
import logger
import manager
import math
import os
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

@app.route("/mre/<ticker>/<days>")
def average(ticker, days):
	"""Average price of a cryptocurrency."""
	try:
		days = int(days)
		1 / days
	except (ValueError, ZeroDivisionError):
		return _failedResp("invalid number of days provided: %s" % days)

	# collect dates from past number of days
	dates = []
	now = datetime.datetime.now()
	for daysAgo in range(days):
		delta = datetime.timedelta(days=daysAgo)
		dateDaysAgo = now - delta
		dates.append(dateDaysAgo.strftime("%Y-%m-%d"))

	# sum prices from dates
	priceSum = 0.0
	datesUnused = set(dates)
	queryFilter = {"datetime": {"$in": dates}, "ticker": ticker}
	entries = list(mongodb.find("price", queryFilter))
	for entry in entries:
		datesUnused.remove(entry["datetime"])
		priceSum += float(entry["open"])

	# calculate average price and standard deviation
	averagePrice = priceSum / float(days)
	deviationsSquaredSum = 0.0
	for entry in entries:
		price = float(entry["open"])
		deviation = abs(price - averagePrice)
		deviationsSquaredSum += deviation ** 2
	standardDeviation = math.sqrt(deviationsSquaredSum / float(days))

	# determine how far the current price deviates from the mean
	currentPrice = manager.getPrice("BTC", "ask")
	if standardDeviation:
		currentPriceDeviation = abs(currentPrice - averagePrice) / standardDeviation
	else:
		currentPriceDeviation = 0

	return _successResp({"days": days,
						 "ticker": ticker,
						 "average price": averagePrice,
						 "days used": len(dates) - len(datesUnused),
						 "dates unused": list(datesUnused),
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
