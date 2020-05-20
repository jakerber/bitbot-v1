"""Mean reversion algos."""
import math

class MeanReversion:
    """Mean reversion object."""
    def __init__(self, currentPrice, pastPrices):
        self.currentPrice = currentPrice
        self.pastPrices = pastPrices

        # validate past prices exist
        if not self.pastPrices:
            raise RuntimeError("price history is required")

    def getPriceDeviation(self):
        """Calculate standard and current price deviation."""
        # calculate average
        priceSum = 0.0
        for price in self.pastPrices:
            priceSum += price
        averagePrice = priceSum / len(self.pastPrices)

        # calculate deviation
        deviationsSquaredSum = 0.0
        for price in self.pastPrices:
            deviation = abs(price - averagePrice)
            deviationsSquaredSum += deviation ** 2
        standardDeviation = math.sqrt(deviationsSquaredSum / len(self.pastPrices))

        # return average price and deviations
        currentDeviation = abs(self.currentPrice - averagePrice)
        return averagePrice, standardDeviation, currentDeviation
