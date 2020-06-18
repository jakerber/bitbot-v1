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
        self.upperBollinger = []
        self.lowerBollinger = []

    def analyze(self):
        """Analyze the current price deviation from the mean."""
        # collect price deviations from the volume-weighted average price
        deviationsSquaredSum = 0.0
        for i, historicalPrices in enumerate(self.priceHistory, 1):
            price = self.calculatePrice(historicalPrices)
            vwap = historicalPrices.get("vwap")
            priceDeviation = abs(price - vwap)
            deviationsSquaredSum += priceDeviation ** 2

            # aggregate bollinger bands for visualizations
            movingStandardDeviation = math.sqrt(deviationsSquaredSum / i)
            self.upperBollinger.append([vwap + (movingStandardDeviation * constants.PERCENT_DEVIATION_OPEN_THRESHOLD)])
            self.lowerBollinger.append([vwap - (movingStandardDeviation * constants.PERCENT_DEVIATION_OPEN_THRESHOLD)])

        # calculate standard deviation
        standardDeviation = math.sqrt(deviationsSquaredSum / len(self.priceHistory))

        # add final bollinger band
        self.upperBollinger.append([self.currentVWAP + (standardDeviation * constants.PERCENT_DEVIATION_OPEN_THRESHOLD)])
        self.lowerBollinger.append([self.currentVWAP - (standardDeviation * constants.PERCENT_DEVIATION_OPEN_THRESHOLD)])

        # calculate current price deviation from current weighted average
        currentDeviation = abs(self.currentPrice - self.currentVWAP)
        currentPercentDeviation = currentDeviation / standardDeviation

        # log and return analysis
        self.logger.log("analyzed %i price deviations" % len(self.priceHistory))
        return MeanReversionAnalysis(self.currentVWAP,
                                     currentDeviation,
                                     currentPercentDeviation,
                                     self.currentPrice,
                                     standardDeviation)

    def calculatePrice(self, allPrices):
        """Calculate the price given all price types."""
        return statistics.mean([allPrices.get("ask"), allPrices.get("bid")])
