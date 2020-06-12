"""BitBot APIs module."""
import assistant
import constants
import datetime
import flask
import io
import json
import logger
import notifier
import trader
import visualizer
from algos import mean_reversion
from db import db
from db import models

# initialize flask app
app = flask.Flask(__name__)

# initialize logger
logger = logger.BitBotLogger("BitBot")

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
            currentPrices = assistant.getAllPrices(ticker)
            priceHistory = assistant.getPriceHistory(ticker)
            analysis.append({"ticker": ticker, "analysis": mean_reversion.MeanReversion(currentPrices, priceHistory).analyze().__dict__})
        except Exception as err:
            raise
            analysis.append({"ticker": ticker, "error": repr(err)})
    return _successResp(analysis)

@app.route("%s/equity" % constants.API_ROOT)
def equity():
    """Get current account balance in USD."""
    try:
        balances = assistant.getAssetBalances()
        value = assistant.getAccountValue()
        marginLevel = assistant.getMarginLevel()
    except Exception as err:
        return _failedResp(err)
    return _successResp({"balances": balances, "value_usd": value, "margin_level_percent": marginLevel})

@app.route("%s/visualize/<ticker>" % constants.API_ROOT)
def visualize(ticker):
    """View visualization of current price prediction."""
    if ticker not in constants.SUPPORTED_CRYPTOS:
        return _failedResp("ticker not supported: %s" % ticker, statusCode=400)  # 400 bad request

    # generate visualization
    currentPrices = assistant.getAllPrices(ticker)
    priceHistory = assistant.getPriceHistory(ticker)
    visualization = visualizer.visualize(ticker, currentPrices, priceHistory)

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
    tickersTraded = []
    for ticker in constants.SUPPORTED_CRYPTOS:
        try:
            currentPrices = assistant.getAllPrices(ticker)
            priceHistory = assistant.getPriceHistory(ticker)
            analysis = mean_reversion.MeanReversion(currentPrices, priceHistory).analyze()
        except Exception as err:
            continue

        # consult trader on potential trade
        _trader = trader.Trader(ticker, analysis, assistant)
        logger.log("consulting trader on potential %s trade" % ticker)
        if _trader.approvesTrade():

            # execute trade
            success, order = _trader.executeTrade()
            if success:
                tickersTraded.append(ticker)
                logger.log("trade executed successfully", moneyExchanged=True)

                # add new order to the database
                transactionId = order.get("transactionId")
                description = order.get("description")
                margin = order.get("margin")
                orderModel = models.Order(transactionId, description, margin)
                mongodb.insert(orderModel)

    # log trading session summary
    numTrades = len(tickersTraded)
    sessionSummary = "traded %i cryptocurrenc%s" % (numTrades, "y" if numTrades == 1 else "ies")
    if numTrades:
        sessionSummary += ": %s" % str(tickersTraded)
    logger.log(sessionSummary)

def summarize():
    """Sends a daily activity summary notification."""
    assetBalances = assistant.getAssetBalances()
    accountValue = assistant.getAccountValue()
    marginLevel = assistant.getMarginLevel()

    # fetch trades that were executed in the past day
    datetimeDayAgo = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    tradesExecuted = assistant.getTradeHistory(startDatetime=datetimeDayAgo)

    # notify via email
    emailSubject = "Daily Summary: %s" % datetime.datetime.now().strftime("%Y-%m-%d")
    emailBody = "Account value:"
    emailBody += "\n$%.2f" % accountValue
    emailBody += "\n\nMargin level:"
    emailBody += "\n%.2f%%" % marginLevel
    emailBody += "\n\nAsset balances:"
    emailBody += "\n" + json.dumps(assetBalances, indent=6)
    emailBody += "\n\nTrades executed:"
    emailBody += "\n" + json.dumps(tradesExecuted, indent=6)
    notifier.email(emailSubject, emailBody)

def snapshot():
    """Store the relevant prices of all supported cryptocurrencies."""
    snapshots = []
    for ticker in constants.SUPPORTED_CRYPTOS:
        try:
            allPrices = assistant.getAllPrices(ticker)
            ask = allPrices.get("ask")
            bid = allPrices.get("bid")
            vwap = allPrices.get("vwap")
        except Exception as err:
            logger.log("unable to fetch price snapshot of %s: %s" % (ticker, repr(err)))
            continue

        # store relevant prices in database
        priceModel = models.Price(ticker, ask, bid, vwap)
        try:
            mongodb.insert(priceModel)
        except Exception as err:
            logger.log("unable to add %s price snapshot to the database: %s" % (ticker, repr(err)))

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
