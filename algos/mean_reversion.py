"""Mean reversion algo module."""
import constants
import math
from algos import linear_regression

class MeanReversionAnalysis:
    """Object to store results from price deviation analysis."""
    def __init__(self, movingAveragePrice, currentDeviation, currentPercentDeviation, currentPrice, standardDeviation, targetPrice):
        self.moving_average_price = movingAveragePrice
        self.current_deviation = currentDeviation
        self.current_percent_deviation = currentPercentDeviation
        self.current_price = currentPrice
        self.lookback_days = constants.LOOKBACK_DAYS
        self.moving_average_window = constants.MOVING_AVERAGE_WINDOW_DAYS
        self.standard_deviation = standardDeviation
        self.target_price = targetPrice

class MeanReversion:
    """Object to analyze price deviation from the mean."""
    def __init__(self, currentPrice, priceHistory):
        self.currentPrice = currentPrice
        self.priceHistory = priceHistory

        # use to calculate moving average
        self.movingAveragePrices = []

    def analyze(self):
        """Analyze the current price deviation from the mean."""
        # calculate moving averages
        priceSum = 0.0
        movingAverage = 0.0
        self.movingAverages = []  # expose for visualizations
        for price in self.priceHistory:
            movingAverage = self.calculateMovingAverage(price)
            self.movingAverages.append(movingAverage)

        # determine current moving average price
        currentMovingAveragePrice = self.calculateMovingAverage(self.currentPrice)
        self.movingAverages.append(currentMovingAveragePrice)

        # generate linear regression model for visualization
        model = linear_regression.LinearRegression(self.currentPrice, self.priceHistory)

        # calculate standard deviation using moving averages
        deviationsSquaredSum = 0.0
        for i, historicalPrice in enumerate(self.priceHistory):
            movingAverage = self.movingAverages[i]
            priceDeviation = abs(historicalPrice - movingAverage)
            deviationsSquaredSum += priceDeviation ** 2
        standardDeviation = math.sqrt(deviationsSquaredSum / len(self.priceHistory))

        # calculate current price deviation from current moving average
        currentDeviation = abs(self.currentPrice - currentMovingAveragePrice)
        currentPercentDeviation = currentDeviation / standardDeviation

        # determine target price based on current price and standard deviation
        # cap target price at current moving average price
        if self.currentPrice < currentMovingAveragePrice:
            targetPrice = min(self.currentPrice + standardDeviation, currentMovingAveragePrice)
        else:
            targetPrice = max(self.currentPrice - standardDeviation, currentMovingAveragePrice)

        # return analysis
        return MeanReversionAnalysis(currentMovingAveragePrice, currentDeviation, currentPercentDeviation, self.currentPrice, standardDeviation, targetPrice)

    def calculateMovingAverage(self, price):
        """Calculate the moving average price within the window."""
        self.movingAveragePrices.append(price)
        while len(self.movingAveragePrices) > constants.MOVING_AVERAGE_WINDOW_DAYS:
            self.movingAveragePrices.pop(0)
        return sum(self.movingAveragePrices) / len(self.movingAveragePrices)
