"""Mean reversion algo module."""
import constants
import math

class PriceDeviation:
    """Object to store results from price deviation analysis."""
    def __init__(self, averagePrice, currentDeviation, currentPercentDeviation, currentPrice, standardDeviation, targetPrice):
        self.average_price = averagePrice
        self.current_deviation = currentDeviation
        self.current_percent_deviation = currentPercentDeviation
        self.current_price = currentPrice
        self.lookback_days = constants.LOOKBACK_DAYS
        self.standard_deviation = standardDeviation
        self.target_price = targetPrice

class MeanReversion:
    """Object to analyze price deviation from the mean."""
    def __init__(self, currentPrice, pastPrices):
        self.currentPrice = currentPrice
        self.pastPrices = pastPrices

        # validate past prices exist
        if not self.pastPrices:
            raise RuntimeError("price history is empty")

    def analyze(self):
        """Analyze the current price deviation from the mean."""
        # calculate averages and sum the deviations squared
        priceSum = 0.0
        movingAverage = 0.0
        deviationsSquaredSum = 0.0
        for i, price in enumerate(self.pastPrices, 1):
            priceSum += price
            movingAverage = priceSum / i
            priceDeviation = abs(price - movingAverage)
            deviationsSquaredSum += priceDeviation ** 2

        # calculate standard and current price deviations
        averagePrice = movingAverage
        standardDeviation = math.sqrt(deviationsSquaredSum / len(self.pastPrices))
        currentDeviation = abs(self.currentPrice - averagePrice)
        currentPercentDeviation = currentDeviation / standardDeviation if standardDeviation else 0.0
        targetPrice = self.currentPrice + standardDeviation if self.currentPrice < averagePrice else self.currentPrice - standardDeviation

        # return price deviation instance
        return PriceDeviation(averagePrice, currentDeviation, currentPercentDeviation, self.currentPrice, standardDeviation, targetPrice)
