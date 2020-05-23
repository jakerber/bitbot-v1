"""Simulator module to run trading simulations."""
import app
import assistant
import constants
import datetime
import logger
from algos import mean_reversion
from db import models


class SimulationResult:
    """Simulation result object."""
    def __init__(self, startingDate, startingBalanceUsd, endingBalanceUsd, profit, tradesExecuted,
                 balances, marginUsed, lookbackDays, deviationThreshold, targetMultiplier):
        self.starting_date = str(startingDate)
        self.starting_balance_usd = startingBalanceUsd
        self.ending_balance_usd = endingBalanceUsd
        self.profit = profit
        self.trades_executed = tradesExecuted
        self.balances = balances
        self.margin_used = marginUsed
        self.lookback_days = lookbackDays
        self.percent_deviation_threshold = deviationThreshold
        self.price_target_multiplier = targetMultiplier
        self.base_buy_usd = constants.BASE_BUY_USD


class Simulator:
    """Trade simulator object."""
    def __init__(self, startingDatetime, lookbackDays, deviationThreshold, targetMultiplier):
        self.logger = logger.Logger("Simulator")

        # provided arguments
        self.startingDatetime = startingDatetime
        self.lookbackDays = lookbackDays
        self.percentDeviationThreshold = deviationThreshold

        # static properties
        self.mongodb = app.mongodb
        self.startingBalanceUsd = constants.SIM_ACCOUNT_BALANCE_USD
        self.endingDatetime = datetime.datetime.now()
        self.priceTargetMultiplier = targetMultiplier

        # dynamic properties
        self.balances = {"USD": self.startingBalanceUsd}
        self.currentDatetime = startingDatetime
        self.marginUsed = 0.0
        self.priceHistory = {}
        self.tradesExecuted = {}
        self.cryptos = set()  # cryptos used in simulation

        # store price history
        for ticker in constants.SUPPORTED_CRYPTOS:
            queryFilter = {"ticker": ticker}
            priceHistory = self.mongodb.find("price", queryFilter)
            if priceHistory:
                self.priceHistory[ticker] = priceHistory
                self.tradesExecuted[ticker] = []
                self.balances[ticker] = 0.0
                self.cryptos.add(ticker)

        # log initialization
        self.logger.log("initializing simulation starting %s" % str(startingDatetime), seperate=True)

    def run(self):
        """Run trading simulation."""
        while self.currentDatetime.strftime("%Y-%m-%d") != self.endingDatetime.strftime("%Y-%m-%d"):
            self.logger.log("simulating trades on %s" % self.currentDatetime.strftime("%Y-%m-%d"))
            for ticker in self.cryptos:
                try:
                    mreNumbers = self._getMRENumbersSim(ticker)
                except Exception as err:
                    self.logger.log("unable to calculate mean reversion for %s: %s" % (ticker, repr(err)))
                    continue

                # simulate trade if percent deviation threshold is met
                if mreNumbers["current_percent_deviation"] >= self.percentDeviationThreshold:
                    price = mreNumbers["current_price"]
                    averagePrice = mreNumbers["average_price"]
                    standardDeviation = mreNumbers["standard_deviation"]
                    if price < averagePrice:
                        tradeType = "buy"
                        priceTarget = price + (standardDeviation * self.priceTargetMultiplier)
                    else:
                        tradeType = "sell"
                        priceTarget = price - (standardDeviation * self.priceTargetMultiplier)
                    quantity = constants.BASE_BUY_USD / price
                    self.trade(ticker, quantity, price, tradeType, priceTarget=priceTarget)

                # determine if limits have been met on any pending trades
                for pendingTrade in [trade for trade in self.tradesExecuted[ticker] if not trade["limit_met"]]:
                    if pendingTrade["trade"]["tradeType"] == "buy":
                        priceType = "bid"
                        newTradeType = "sell"
                        limitMet = lambda price: price >= pendingTrade["trade"]["priceTarget"]
                    else:
                        priceType = "ask"
                        newTradeType = "buy"
                        limitMet = lambda price: price <= pendingTrade["trade"]["priceTarget"]

                    # execute follow-up trade if price target is met
                    pendingTradeTicker = pendingTrade["trade"]["ticker"]
                    currentPrice = self._getCurrentPriceFromHistory(pendingTradeTicker)
                    if limitMet(currentPrice):
                        pendingTradeQuantity = pendingTrade["trade"]["quantity"]
                        self.trade(pendingTradeTicker, pendingTradeQuantity, currentPrice, newTradeType)
                        pendingTrade["limit_met"] = True

            # proceed to next day
            self.currentDatetime += datetime.timedelta(days=1)

        endingBalanceUsd = self._calculateBalanceUSD()
        profit = endingBalanceUsd - self.startingBalanceUsd
        return SimulationResult(self.startingDatetime,
                                self.startingBalanceUsd,
                                endingBalanceUsd,
                                profit,
                                self.tradesExecuted,
                                self.balances,
                                self.marginUsed,
                                self.lookbackDays,
                                self.percentDeviationThreshold,
                                self.priceTargetMultiplier).__dict__

    def trade(self, ticker, quantity, price, tradeType, priceTarget=None):
        """Simulate a trade."""
        logMessage = "%sing %f %s @ $%f" % (tradeType, quantity, ticker, price)
        if priceTarget:
            logMessage += ", target=$%f" % priceTarget
        self.logger.log(logMessage)

        # instantiate trade
        newTrade = models.Trade(ticker, quantity, price, tradeType, priceTarget)
        newTrade.date = self.currentDatetime.strftime("%Y-%m-%d")

        # adjust balances based on funds used to trade
        amountUsd = price * quantity
        if tradeType == "buy":
            if amountUsd > self.balances["USD"]:
                self.logger.log("unable to buy %s: insufficient funds" % ticker)  # insufficient funds
                return
            self.balances["USD"] -= amountUsd
            self.balances[ticker] += quantity
        else:
            self.balances["USD"] += amountUsd

            # sell from margin if no cryptocurrency available
            if quantity > self.balances[ticker]:
                self.marginUsed += amountUsd
            else:
                self.balances[ticker] -= quantity

        # store executed trade
        limitMet = priceTarget is None
        self.tradesExecuted[ticker].append({"trade": newTrade.__dict__, "limit_met": limitMet})

    def _calculateBalanceUSD(self):
        """Calculate current account balance in USD given all cryptocurrency balances."""
        totalBalanceUsd = self.balances["USD"]
        for ticker in [ticker for ticker in self.balances if ticker != "USD"]:
            currentPrice = assistant.getPrice(ticker, "ask")
            totalBalanceUsd += self.balances[ticker] * currentPrice
        return totalBalanceUsd - self.marginUsed

    def _getCurrentPriceFromHistory(self, ticker):
        """Fetch current price based on current datetime."""
        currentDate = self.currentDatetime.strftime("%Y-%m-%d")

        # fetch price from price history
        for pricePoint in self.priceHistory[ticker]:
            if pricePoint["date"] == currentDate:
                return pricePoint["open"]

        # raise exception if no price exists for current datetime
        raise RuntimeError("missing price point: %s on %s" % (ticker, currentDate))

    def _getMRENumbersSim(self, ticker):
        """Simulator version of app.getMRENumbers."""
        # collect dates from past number of days
        dates = []
        for daysAgo in range(self.lookbackDays):
            delta = datetime.timedelta(days=daysAgo)
            dateDaysAgo = self.currentDatetime - delta
            dates.append(dateDaysAgo.strftime("%Y-%m-%d"))

        # fetch prices on dates from price history dict
        priceHistory = self.priceHistory[ticker]
        entries = [entry for entry in priceHistory if entry["date"] in dates]

        # calculate and return price deviations
        prices = [entry["open"] for entry in entries]
        currentPrice = self._getCurrentPriceFromHistory(ticker)
        return mean_reversion.MeanReversion(currentPrice, prices).calculate()
