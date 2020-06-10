"""Linear regression algo module."""
import constants
import datetime
import pandas
import statistics
from sklearn import linear_model

class LinearRegression:
    """Object to represent a linear regression model."""
    def __init__(self, currentPrice, priceHistory):
        self.currentPrice = currentPrice
        self.priceHistory = priceHistory

        # generate model
        self.generate()

    def generate(self):
        """Generate a linear regression model from historical price data."""
        # format dataset
        self.dataset = {"unix_timestamp": [], "price": []}
        for prices in self.priceHistory:
            unixTimestamp = prices.get("utc_datetime").timestamp()
            price = statistics.mean([prices.get("ask"), prices.get("bid")])
            self.dataset["unix_timestamp"].append(unixTimestamp)
            self.dataset["price"].append(price)

        # add current price to dataset
        self.dataset["unix_timestamp"].append(datetime.datetime.utcnow().timestamp())
        self.dataset["price"].append(self.currentPrice)

        # instantiate pandas dataframe
        self.dataframe = pandas.DataFrame.from_dict(self.dataset)
        self.timestamps = self.dataframe.iloc[:, 0].values.reshape(-1, 1)
        self.prices = self.dataframe.iloc[:, 1].values.reshape(-1, 1)

        # generate sklearn linear regression model
        self.model = linear_model.LinearRegression()
        self.model.fit(self.timestamps, self.prices)
        self.trend = self.model.predict(self.timestamps)
