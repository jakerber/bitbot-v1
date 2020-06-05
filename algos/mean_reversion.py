"""Mean reversion algo module."""
import constants
import math

class MeanReversionAnalysis:
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
    def __init__(self, currentPrice, priceHistory):
        self.currentPrice = currentPrice
        self.priceHistory = priceHistory

    def analyze(self):
        """Analyze the current price deviation from the mean."""
        # calculate averages and sum the deviations squared
        priceSum = 0.0
        movingAverage = 0.0
        self.movingAverages = []  # expose for visualization
        deviationsSquaredSum = 0.0
        for i, price in enumerate(self.priceHistory, 1):
            priceSum += price
            movingAverage = priceSum / i
            self.movingAverages.append([movingAverage])  # aggregate for visualization
            priceDeviation = abs(price - movingAverage)
            deviationsSquaredSum += priceDeviation ** 2

        # finalize average price using moving average
        priceSum += self.currentPrice
        averagePrice = priceSum / constants.LOOKBACK_DAYS
        self.movingAverages.append([averagePrice])  # aggregate for visualization

        # calculate standard and current price deviations
        standardDeviation = math.sqrt(deviationsSquaredSum / len(self.priceHistory))
        currentDeviation = abs(self.currentPrice - averagePrice)
        currentPercentDeviation = currentDeviation / standardDeviation if standardDeviation else 0.0
        targetPrice = self.currentPrice + standardDeviation if self.currentPrice < averagePrice else self.currentPrice - standardDeviation

        # return analysis
        return MeanReversionAnalysis(averagePrice, currentDeviation, currentPercentDeviation, self.currentPrice, standardDeviation, targetPrice)
