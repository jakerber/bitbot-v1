"""BitBot APIs module."""
import assistant
import constants
import datetime
import flask
import io
import json
import logger
import notifier
import visualizer
from algos import mean_reversion
from algos import trailing_stop_loss
from trading import opener
from trading import closer
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
    currentPrices = assistant.getPrices()
    analysis = []
    for ticker in constants.SUPPORTED_TICKERS:
        _currentPrices = currentPrices.get(ticker)
        priceHistory = assistant.getPriceHistory(ticker)
        analysis.append({"ticker": ticker,
                         "analysis": mean_reversion.MeanReversion(_currentPrices, priceHistory).analyze().__dict__})
    return _successResp(analysis)

@app.route("%s/equity" % constants.API_ROOT)
def equity():
    """Get current account balances."""
    balances = assistant.getAssetBalances()
    balances = {asset: balance for asset, balance in balances.items() if balance}  # filter out empty balances
    accountBalances = assistant.getAccountBalances()
    equity = accountBalances.get("equivalent_balance") + accountBalances.get("unrealized_net_profit")
    marginLevel = accountBalances.get("margin_level")
    return _successResp({"balances": balances, "equity_usd": equity, "margin_level_percent": marginLevel})

@app.route("%s/positions" % constants.API_ROOT)
def positions():
    """Analyze the profit and trailing stop-loss of open positions."""
    positions = {}
    total = 0
    combinedProfit = 0
    for ticker, transactionId, analysis in analyzeOpenPositions():
        if ticker not in positions:
            positions[ticker] = []
        positions[ticker].append({"transaction_id": transactionId, "analysis": analysis.__dict__})
        total += 1
        combinedProfit += analysis.unrealized_profit_usd
    return _successResp({"positions": positions, "total": total, "net_unrealized_profit_usd": combinedProfit})

@app.route("%s/visualize" % constants.API_ROOT)
def visualize_equity():
    """View visualization of account equity balance."""
    # generate visualization
    currentBalanceUSD = assistant.getAssetBalances().get("USD")
    currentBalances = assistant.getAccountBalances()
    currentEquity = currentBalances.get("equivalent_balance") + currentBalances.get("unrealized_net_profit")
    equityHistory = assistant.getEquityHistory()
    visualization = visualizer.visualizeEquity(currentEquity, currentBalanceUSD, equityHistory)

    # display visualization
    image = io.BytesIO()
    visualization.print_png(image)
    return flask.Response(image.getvalue(), mimetype="image/png")

@app.route("%s/visualize/<ticker>" % constants.API_ROOT)
def visualize_price(ticker):
    """View visualization of price analysis."""
    if ticker not in constants.SUPPORTED_TICKERS:
        return _failedResp("ticker not supported: %s" % ticker, statusCode=400)  # 400 bad request

    # generate visualization
    currentPrices = assistant.getPrices().get(ticker)
    priceHistory = assistant.getPriceHistory(ticker)
    visualization = visualizer.visualizePrice(ticker, currentPrices, priceHistory)

    # display visualization
    image = io.BytesIO()
    visualization.print_png(image)
    return flask.Response(image.getvalue(), mimetype="image/png")

@app.route("/")
def root():
    """Root endpoint of the app."""
    return "<h1>bleep bloop<h1>"

@app.route("%s/" % constants.API_ROOT)
def root_api():
    """Root endpoint of the api."""
    return "<h1>api root<h1>"

#################################
##  Private APIs
#################################

def clean():
    """Remove outdated database entries."""
    retentionDatetime = datetime.datetime.utcnow() - datetime.timedelta(days=constants.HISTORY_RETENTION_DAYS)
    filter = {"utc_datetime": {"$lt": retentionDatetime}}
    mongodb.deleteMany("price", filter)
    mongodb.deleteMany("equity", filter)

def snapshot_equity():
    """Store relevant account balances."""
    currentBalances = assistant.getAccountBalances()
    currentAssetBalances = assistant.getAssetBalances()
    balanceUSD = currentAssetBalances.get("USD")
    equity = currentBalances.get("equivalent_balance") + currentBalances.get("unrealized_net_profit")
    marginUsed = currentBalances.get("margin_used")

    # store relevant account balances in database
    mongodb.insert(models.Equity(balanceUSD, equity, marginUsed))

def snapshot_price():
    """Store the relevant prices of all supported cryptocurrencies."""
    snapshots = []
    currentPrices = assistant.getPrices()
    for ticker in constants.SUPPORTED_TICKERS:
        ask = currentPrices.get(ticker).get("ask")
        bid = currentPrices.get(ticker).get("bid")
        high = currentPrices.get(ticker).get("high")
        low = currentPrices.get(ticker).get("low")
        vwap = currentPrices.get(ticker).get("vwap")
        snapshots.append(models.Price(ticker, ask, bid, high, low, vwap))

    # store relevant prices in database
    mongodb.insertMany(snapshots)

def notify():
    """Sends a daily activity summary notification."""
    assetBalances = assistant.getAssetBalances()
    accountBalances = assistant.getAccountBalances()
    accountValue = accountBalances.get("equivalent_balance") + accountBalances.get("unrealized_net_profit")
    marginLevel = accountBalances.get("margin_level")

    # fetch positions opened in the past day
    openPositions = {}
    for position in assistant.getOpenPositions():
        ticker = position.get("ticker")
        position = {prop: str(position[prop]) for prop in position
                    if prop not in constants.MONGODB_EXCLUDE_PROPS}

        # group positions by ticker
        if ticker not in openPositions:
            openPositions[ticker] = []
        openPositions[ticker].append(position)

    # notify via email
    emailSubject = "Daily Summary: %s" % datetime.datetime.now().strftime("%Y-%m-%d")
    emailBody = "Account equity:"
    emailBody += "\n$%.2f" % accountValue
    emailBody += "\n\nMargin level:"
    emailBody += "\n%.2f%%" % marginLevel if marginLevel else "\nNone"
    emailBody += "\n\nAsset balances:"
    emailBody += "\n" + json.dumps(assetBalances, indent=6)
    emailBody += "\n\nOpen positions:"
    emailBody += "\n" + json.dumps(openPositions, indent=6)
    notifier.email(emailSubject, emailBody)

def trade_close():
    """Close qualified cryptocurrency trading positions."""
    tickersClosed = set()

    # fetch analysis on all open positions
    openPositions = analyzeOpenPositions()
    logger.log("found %i open positions" % len(openPositions))
    for ticker, transactionId, analysis in openPositions:

        # consult closer on the potential close of position
        _trader = closer.Closer(ticker, analysis, assistant)
        logger.log("consulting closer on potential %s close" % ticker)
        if _trader.approves:

            # close position
            success, order, profit = _trader.execute()
            if success:
                tickersClosed.add(ticker)
                logger.log("position closed successfully (profit=$%.3f)" % profit, moneyExchanged=True)

                # delete open position from the database
                mongodb.delete("position", filter={"transaction_id": transactionId})

    # log clossing session summary
    numCloses = len(tickersClosed)
    sessionSummary = "closed positions for %i cryptocurrenc%s" % (numCloses, "y" if numCloses == 1 else "ies")
    if numCloses:
        sessionSummary += ": %s" % str(list(tickersClosed))
    logger.log(sessionSummary)

def trade_open():
    """Open qualified cryptocurrency trading positions."""
    tickersOpened = set()
    currentPrices = assistant.getPrices()
    logger.log("found %i tradeable cryptocurrencies" % len(constants.SUPPORTED_TICKERS))
    for ticker in constants.SUPPORTED_TICKERS:

        # analyze price deviation from the mean for all supported cryptos
        try:
            _currentPrices = currentPrices.get(ticker)
            priceHistory = assistant.getPriceHistory(ticker)
            analysis = mean_reversion.MeanReversion(_currentPrices, priceHistory).analyze()
        except Exception as err:
            logger.log("unable to analyze %s mean reversion: %s" % (ticker, repr(err)))
            continue

        # consult trader on potential position
        _trader = opener.Opener(ticker, analysis, assistant)
        logger.log("consulting opener on potential %s position" % ticker)
        if _trader.approves:

            # execute trade
            success, position = _trader.execute()
            if success:
                tickersOpened.add(ticker)
                logger.log("position opened successfully", moneyExchanged=True)

                # add new position to the database
                transactionId = position.get("transaction_id")
                description = position.get("description")
                openPositionModel = models.Position(ticker, transactionId, description)
                mongodb.insert(openPositionModel)

    # log trading session summary
    numTrades = len(tickersOpened)
    sessionSummary = "opened positions for %i cryptocurrenc%s" % (numTrades, "y" if numTrades == 1 else "ies")
    if numTrades:
        sessionSummary += ": %s" % str(list(tickersOpened))
    logger.log(sessionSummary)

###############################
##  Helper methods
###############################

def analyzeOpenPositions():
    """Get analysis (e.g. unrealized profit, etc.) on open positions."""
    openPositionAnalysis = []

    # fetch open positions from the database
    transactionIds = []
    openPositions = assistant.getOpenPositions()
    for position in openPositions:
        transactionIds.append(position.get("transaction_id"))

    # skip analysis if no open positions
    if not openPositions:
        return []

    # fetch information on orders that opened positions
    currentPrices = assistant.getPrices()
    orders = assistant.getOrders(transactionIds)
    for position in openPositions:
        ticker = position.get("ticker")
        transactionId = position.get("transaction_id")
        order = orders.get(transactionId)

        # determine if action needs to be taken on the order
        # possible order statuses: ["pending", "open", "closed", "cancelled", "expired"]
        orderStatus = order.get("status")

        # delete open positions for failed orders
        if orderStatus == "cancelled" or orderStatus == "expired":
            mongodb.delete("position", filter={"transaction_id": transactionId})
            continue
        elif orderStatus != "closed":
            continue

        # gather relevant position information
        initialOrderType = order.get("descr").get("type")
        initialPrice = float(order.get("price"))
        initialOrderTimestamp = order.get("closetm")
        initialOrderDatetime = datetime.datetime.utcfromtimestamp(initialOrderTimestamp)
        volume = float(order.get("vol"))
        leverage = order.get("descr").get("leverage")
        leverage = None if leverage == "none" else int(leverage[0])

        # gather relevant price information
        currentPrice = currentPrices.get(ticker).get("bid") if initialOrderType == "buy" else currentPrices.get(ticker).get("ask")
        currentVWAP = currentPrices.get(ticker).get("vwap")

        # verify order type
        if initialOrderType not in ["buy", "sell"]:
            logger.log("unknown initial order type for %s: %s" % (transactionId, initialOrderType))
            continue

        # analyze trailing stop-loss order potential
        try:
            priceHistory = assistant.getPriceHistory(ticker, startingDatetime=initialOrderDatetime, verify=False)
            analysis = trailing_stop_loss.TrailingStopLoss(ticker,
                                                           initialOrderType,
                                                           leverage,
                                                           volume,
                                                           currentPrice,
                                                           currentVWAP,
                                                           initialPrice,
                                                           priceHistory).analyze()
        except Exception as err:
            logger.log("unable to analyze %s trailing stop loss potential: %s" % (ticker, repr(err)))
            continue
        else:
            openPositionAnalysis.append((ticker, transactionId, analysis))

    # return analysis on open positions
    return openPositionAnalysis

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
