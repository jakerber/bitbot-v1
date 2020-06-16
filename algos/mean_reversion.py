"""Mean reversion algo module."""
import constants
import logger
import math
import statistics

class MeanReversionAnalysis:
    """Object to store results from price deviation analysis."""
    def __init__(self, currentVWAP, currentDeviation, currentPercentDeviation, currentPrice, standardDeviation):
        self.current_volume_weighted_average_price = currentVWAP
        self.current_deviation = currentDeviation
        self.current_percent_deviation = currentPercentDeviation
        self.current_price = currentPrice
        self.lookback_days = constants.LOOKBACK_DAYS
        self.standard_deviation = standardDeviation

class MeanReversion:
    """Object to analyze price deviation from the mean."""
    def __init__(self, currentPrices, priceHistory):
        self.logger = logger.Logger("MeanReversion")
        self.currentPrice = self.calculatePrice(currentPrices)
        self.currentVWAP = currentPrices.get("vwap")
        self.priceHistory = priceHistory

        # expose for visualizations
        self.vwaps = []

    def analyze(self):
        """Analyze the current price deviation from the mean."""
        # calculate standard deviation from volume-weighted average prices
        deviationsSquaredSum = 0.0
        for historicalPrices in self.priceHistory:
            price = self.calculatePrice(historicalPrices)
            vwap = historicalPrices.get("vwap")
            self.vwaps.append([vwap])  # aggregate for visualizations
            priceDeviation = abs(price - vwap)
            deviationsSquaredSum += priceDeviation ** 2
        standardDeviation = math.sqrt(deviationsSquaredSum / len(self.priceHistory))

        # calculate current price deviation from current weighted average
        self.vwaps.append([self.currentVWAP])  # aggregate for visualizations
        currentDeviation = abs(self.currentPrice - self.currentVWAP)
        currentPercentDeviation = currentDeviation / standardDeviation

        # log and return analysis
        self.logger.log("analyzed %i price deviations" % len(self.vwaps))
        return MeanReversionAnalysis(self.currentVWAP,
                                     currentDeviation,
                                     currentPercentDeviation,
                                     self.currentPrice,
                                     standardDeviation)

    def calculatePrice(self, allPrices):
        """Calculate the price given all price types."""
        return statistics.mean([allPrices.get("ask"), allPrices.get("bid")])
