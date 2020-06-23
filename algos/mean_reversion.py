"""Mean reversion algo module."""
import constants
import datetime
import logger
import math
import statistics

SECONDS_IN_HOUR = 3600

class MeanReversionAnalysis:
    """Object to store results from price deviation analysis."""
    def __init__(self, currentVWAP, currentDeviation, currentPercentDeviation, currentPrice, standardDeviation, priceChange24Hours, vwapChange24Hours):
        self.current_volume_weighted_average_price = currentVWAP
        self.current_deviation = currentDeviation
        self.current_percent_deviation = currentPercentDeviation
        self.current_price = currentPrice
        self.lookback_days = constants.LOOKBACK_DAYS
        self.standard_deviation = standardDeviation
        self.price_change_24_hours = priceChange24Hours
        self.vwap_change_24_hours = vwapChange24Hours

class MeanReversion:
    """Object to analyze price deviation from the mean."""
    def __init__(self, currentPrices, priceHistory):
        self.logger = logger.Logger("MeanReversion")
        self.currentPrice = self.calculatePrice(currentPrices)
        self.currentVWAP = currentPrices.get("vwap")
        self.currentDatetimeUTC = datetime.datetime.utcnow()
        self.priceHistory = priceHistory

        # expose for visualizations
        self.upperBollinger = []
        self.lowerBollinger = []

    def analyze(self):
        """Analyze the current price deviation from the mean."""
        price24HoursAgo = None
        vwap24HoursAgo = None

        # collect price deviations from the volume-weighted average price
        deviationsSquaredSum = 0.0
        for i, entry in enumerate(self.priceHistory, 1):
            price = self.calculatePrice(entry)
            vwap = entry.get("vwap")
            priceDeviation = abs(price - vwap)
            deviationsSquaredSum += priceDeviation ** 2

            # store prices from 24 hours ago
            if not price24HoursAgo:
                hoursAgo = (self.currentDatetimeUTC - entry.get("utc_datetime")).total_seconds() / SECONDS_IN_HOUR
                if hoursAgo <= 24.0:
                    price24HoursAgo = price
                    vwap24HoursAgo = vwap

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

        # determine price and vwap 24 hours ago
        if not price24HoursAgo:
            raise RuntimeError("unable to determine price 24 hours ago")
        priceChange24Hours = self.currentPrice - price24HoursAgo
        vwapChange24Hours = self.currentVWAP - vwap24HoursAgo

        # log and return analysis
        self.logger.log("analyzed %i price deviations" % len(self.priceHistory))
        return MeanReversionAnalysis(self.currentVWAP,
                                     currentDeviation,
                                     currentPercentDeviation,
                                     self.currentPrice,
                                     standardDeviation,
                                     priceChange24Hours,
                                     vwapChange24Hours)

    def calculatePrice(self, allPrices):
        """Calculate the price given all price types."""
        return statistics.mean([allPrices.get("ask"), allPrices.get("bid")])
