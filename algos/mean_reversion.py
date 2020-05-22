"""Mean reversion algos."""
import constants
import math


class PriceDeviation:
    """Price Deviation object."""
    def __init__(self, averagePrice, currentDeviation, currentPercentDeviation, currentPrice, standardDeviation):
        self.average_price = averagePrice
        self.current_deviation = currentDeviation
        self.current_percent_deviation = currentPercentDeviation
        self.current_price = currentPrice
        self.lookback_days = constants.LOOKBACK_DAYS
        self.standard_deviation = standardDeviation


class MeanReversion:
    """Mean reversion object."""
    def __init__(self, currentPrice, pastPrices):
        self.currentPrice = currentPrice
        self.pastPrices = pastPrices

        # validate past prices exist
        if not self.pastPrices:
            raise RuntimeError("price history is empty")

    def calculate(self):
        """Calculate standard and current price deviation."""
        # calculate average
        priceSum = 0.0
        for price in self.pastPrices:
            priceSum += price
        averagePrice = priceSum / len(self.pastPrices)

        # calculate price deviations
        deviationsSquaredSum = 0.0
        for price in self.pastPrices:
            deviation = abs(price - averagePrice)
            deviationsSquaredSum += deviation ** 2
        standardDeviation = math.sqrt(deviationsSquaredSum / len(self.pastPrices))

        # return price deviations
        currentDeviation = abs(self.currentPrice - averagePrice)
        currentPercentDeviation = currentDeviation / standardDeviation if standardDeviation else 0.0
        return PriceDeviation(averagePrice, currentDeviation, currentPercentDeviation, self.currentPrice, standardDeviation).__dict__
