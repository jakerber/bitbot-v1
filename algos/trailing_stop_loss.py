"""Trailing stop-loss algo module."""
import logger

class TrailingStopLossAnalysis:
    """Object to store results from trailing stop-loss analysis."""
    def __init__(self, ticker, initialOrderType, leverage, volume, currentPrice, currentVWAP, initialPrice, trailingPercentage, actionablePrice, actionableDatetime, unrealizedProfit):
        self.ticker = ticker
        self.initial_order_type = initialOrderType
        self.leverage = leverage
        self.volume = volume
        self.current_price = currentPrice
        self.current_volume_weighted_average_price = currentVWAP
        self.initial_price = initialPrice
        self.trailing_percentage = trailingPercentage
        self.actionable_price = actionablePrice
        self.actionable_datetime_utc = actionableDatetime
        self.unrealized_profit_usd = unrealizedProfit

class TrailingStopLoss:
    """Object to perform trailing stop-loss analysis on open positons."""
    def __init__(self, ticker, initialOrderType, leverage, volume, currentPrice, currentVWAP, initialPrice, priceHistory):
        self.logger = logger.Logger("TrailingStopLoss")
        self.ticker = ticker
        self.initialOrderType = initialOrderType
        self.leverage = leverage
        self.volume = volume
        self.currentPrice = currentPrice
        self.currentVWAP = currentVWAP
        self.initialPrice = initialPrice
        self.priceHistory = priceHistory

    def analyze(self):
        """Determine price deviation from extreme (peak / valley)."""
        # determine actionable price
        # actionable price: most profitable price since position was opened
        actionablePrice = self.initialPrice
        actionableDatetime = None
        for price in self.priceHistory:

            # if initial buy: actionable price = peak since buy
            if self.initialOrderType == "buy":
                _price = price.get("bid")
                _datetime = price.get("utc_datetime")
                if not actionablePrice or _price > actionablePrice:
                    actionablePrice = _price
                    actionableDatetime = str(_datetime)

            # if initial sell: actionable price = valley since sell
            else:
                _price = price.get("ask")
                _datetime = price.get("utc_datetime")
                if not actionablePrice or _price < actionablePrice:
                    actionablePrice = _price
                    actionableDatetime = str(_datetime)

        # calulate trailing percentage between current and actionable prices
        # if initial buy: trailing percentage = how much price has fallen from max
        # if initial sell: trailing percentage = how much price has risen from min
        if self.initialOrderType == "buy":
            trailingPercentage = (actionablePrice - self.currentPrice) / actionablePrice
            unrealizedProfit = (self.currentPrice - self.initialPrice) * self.volume
        else:
            trailingPercentage = (self.currentPrice - actionablePrice) / actionablePrice
            unrealizedProfit = (self.initialPrice - self.currentPrice) * self.volume

        # price trailing stop-loss analysis
        self.logger.log("analyzed trailing stop-loss over %i prices" % len(self.priceHistory))
        return TrailingStopLossAnalysis(self.ticker,
                                        self.initialOrderType,
                                        self.leverage,
                                        self.volume,
                                        self.currentPrice,
                                        self.currentVWAP,
                                        self.initialPrice,
                                        trailingPercentage,
                                        actionablePrice,
                                        actionableDatetime,
                                        unrealizedProfit)
