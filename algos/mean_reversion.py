"""Mean reversion algo module."""
import constants
import math
from algos import linear_regression

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
        # calculate moving averages
        priceSum = 0.0
        movingAverage = 0.0
        self.movingAverages = []  # expose for visualization
        for i, price in enumerate(self.priceHistory, 1):
            priceSum += price
            movingAverage = priceSum / i
            self.movingAverages.append([movingAverage])  # aggregate for visualization

        # determine average price using moving averages
        priceSum += self.currentPrice
        averagePrice = priceSum / constants.LOOKBACK_DAYS
        self.movingAverages.append([averagePrice])  # aggregate for visualization

        # generate linear regression model
        model = linear_regression.LinearRegression(self.currentPrice, self.priceHistory)

        # calculate standard deviation using linear regression model
        deviationsSquaredSum = 0.0
        for i, historicalPrice in enumerate(self.priceHistory):
            trendPrice = model.trend[i][0]
            priceDeviation = abs(historicalPrice - trendPrice)
            deviationsSquaredSum += priceDeviation ** 2
        standardDeviation = math.sqrt(deviationsSquaredSum / len(self.priceHistory))

        # calculate current price deviation from current trend price
        trendPrice = model.trend[-1][0]
        currentDeviation = abs(self.currentPrice - trendPrice)
        currentPercentDeviation = currentDeviation / standardDeviation

        # determine target price from percent deviation
        if self.currentPrice < trendPrice:
            targetPrice = min(self.currentPrice + standardDeviation, trendPrice)
        else:
            targetPrice = max(self.currentPrice - standardDeviation, trendPrice)

        # return analysis
        return MeanReversionAnalysis(averagePrice, currentDeviation, currentPercentDeviation, self.currentPrice, standardDeviation, targetPrice)
