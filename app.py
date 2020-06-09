"""BitBot APIs module."""
import assistant
import base64
import constants
import datetime
import flask
import io
import json
import logger
import math
import notifier
import os
import visualizer
from algos import mean_reversion
from db import db
from db import models

# initialize flask app
app = flask.Flask(__name__)

# initialize logger
logger = logger.Logger("BitBot")

# initialize mongodb connection
mongodb = db.BitBotDB(app)

# initialize assistant
assistant = assistant.Assistant(mongodb)

# initialize notifier
notifier = notifier.Notifier()

#################################
##  Public APIs
#################################

@app.route("%s/analyze" % constants.API_ROOT)
def analyze():
    """Analyze the price deviations of all supported cryptocurrencies."""
    analysis = []
    for ticker in constants.SUPPORTED_CRYPTOS:
        try:
            currentPrice = assistant.getPrice(ticker, "ask")
            priceHistory = assistant.getPriceHistory(ticker)
            analysis.append({"ticker": ticker, "analysis": mean_reversion.MeanReversion(currentPrice, priceHistory).analyze().__dict__})
        except Exception as err:
            analysis.append({"ticker": ticker, "error": repr(err)})
    return _successResp(analysis)

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

@app.route("%s/equity" % constants.API_ROOT)
def equity():
    """Get current account balance in USD."""
    try:
        balances = assistant.getAccountBalances()
        value = assistant.getAccountValue()
        marginUsed = assistant.getMarginUsed()
    except Exception as err:
        return _failedResp(err)
    return _successResp({"balances": balances, "value_usd": value, "margin_used_usd": marginUsed})

@app.route("%s/visualize/<ticker>" % constants.API_ROOT)
def visualize(ticker):
    """View visualization of current price prediction."""
    if ticker not in constants.SUPPORTED_CRYPTOS:
        return _failedResp("ticker not supported: %s" % ticker, statusCode=400)  # 400 bad request

    # generate visualization
    currentPrice = assistant.getPrice(ticker, "ask")
    priceHistory = assistant.getPriceHistory(ticker)
    visualization = visualizer.visualize(ticker, currentPrice, priceHistory)

    # display visualization
    image = io.BytesIO()
    visualization.print_png(image)
    return flask.Response(image.getvalue(), mimetype="image/png")

@app.route("/")
def root():
    """Root endpoint of the app."""
    return "<h1>bleep bloop<h1>"

@app.route("%s/" % constants.API_ROOT)
def rootApi():
    """Root endpoint of the api."""
    return "<h1>api root<h1>"

#################################
##  Private APIs
#################################

def trade():
    """Trade cryptocurrency to achieve profit."""
    # analyze price deviation from the mean for all supported cryptos
    ordersExecuted = {}
    for ticker in constants.SUPPORTED_CRYPTOS:
        try:
            currentPrice = assistant.getPrice(ticker, "ask")
            priceHistory = assistant.getPriceHistory(ticker)
            analysis = mean_reversion.MeanReversion(currentPrice, priceHistory).analyze()
        except Exception as err:
            continue

        # trade if price deviation thresholds are met
        if shouldTrade(analysis.current_percent_deviation):
            if analysis.target_price > analysis.current_price:
                tradeFunc = assistant.buy
            else:
                tradeFunc = assistant.short

                # ensure margin trading is allowed before shorting
                if not constants.ALLOW_MARGIN_TRADING:
                    logger.log("unable to short %s: margin trading is not allowed" % ticker)
                    continue

            # determine amount to trade
            tradeAmountUSD = getTradeAmountUSD(analysis.current_percent_deviation)
            tradeAmount = tradeAmountUSD / analysis.current_price

            # safetly execute trade
            try:
                orderDescription = tradeFunc(ticker, tradeAmount, priceTarget=analysis.target_price)
                logger.log("trade executed successfully")
                logger.log(orderDescription, moneyExchanged=True)
            except Exception as err:
                logger.log("unable to execute %s trade: %s" % (ticker, str(err)))

def sendDailySummary():
    """Sends a daily activity summary email."""
    accountBalances = assistant.getAccountBalances()
    accountValue = assistant.getAccountValue()
    marginUsed = assistant.getMarginUsed()

    # fetch trades that were executed today
    datetimeDayAgo = datetime.datetime.now() - datetime.timedelta(days=1)
    tradesExecuted = assistant.getTradeHistory(startDatetime=datetimeDayAgo)

    # notify via email
    emailSubject = "Daily Summary: %s" % datetime.datetime.now().strftime("%Y-%m-%d")
    emailBody = "Account value:"
    emailBody += "\n$%f" % accountValue
    emailBody += "\n\nMargin used:"
    emailBody += "\n$%f" % marginUsed
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

def getTradeAmountUSD(currentPercentDeviation):
    """Determine how much of the cryptocurrency should be traded."""
    deviationAboveThreshold = currentPercentDeviation - constants.PERCENT_DEVIATION_THRESHOLD
    multiplier = min(deviationAboveThreshold, constants.TRADE_MULTIPLIER_MAX)
    return constants.BASE_BUY_USD + (constants.BASE_BUY_USD * multiplier)

def shouldTrade(currentPercentDeviation):
    """Determine if a cryptocurrency should be traded."""
    return currentPercentDeviation >= constants.PERCENT_DEVIATION_THRESHOLD

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
