"""Linear regression algo module."""
import constants
import pandas
from sklearn import linear_model

class LinearRegression:
    """Object to represent a linear regression model."""
    def __init__(self, currentPrice, priceHistory):
        self.currentPrice = currentPrice
        self.priceHistory = priceHistory

        # generate model
        self.generate()

    def generate(self):
        """Analyze current price predictions from the linear regression model."""
        # format dataset
        self.dataset = {"day": [], "price": []}
        for i, price in enumerate(self.priceHistory):
            self.dataset["day"].append(i)
            self.dataset["price"].append(price)

        # add current price to dataset
        self.dataset["day"].append(len(self.priceHistory))
        self.dataset["price"].append(self.currentPrice)

        # instantiate pandas dataframe
        self.dataframe = pandas.DataFrame.from_dict(self.dataset)
        self.days = self.dataframe.iloc[:, 0].values.reshape(-1, 1)
        self.prices = self.dataframe.iloc[:, 1].values.reshape(-1, 1)

        # generate sklearn linear regression model
        self.model = linear_model.LinearRegression()
        self.model.fit(self.days, self.prices)
        self.trend = self.model.predict(self.days)

    def predict(self, daysFromNow=0):
        """Predict future prices."""
        daysFromNow += constants.LOOKBACK_DAYS
        return self.model.predict([[daysFromNow]])[0][0]
