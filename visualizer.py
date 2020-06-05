"""Data visualization module."""
import constants
import datetime
import matplotlib
from matplotlib import pyplot
from algos import linear_regression
from algos import mean_reversion

VISUALIZATION_FILE = "visualization.png"

# ensure Flask doesn't try to create GUI windows
matplotlib.use("Agg")

def visualize(ticker, currentPrice, priceHistory):
    """Generate a visualization of a target price prediction."""
    # analyze price data
    regression = linear_regression.LinearRegression(currentPrice, priceHistory)
    meanReversion = mean_reversion.MeanReversion(currentPrice, priceHistory)
    analysis = meanReversion.analyze()

    # generate historical price visualization
    pyplot.clf()
    pyplot.title("%s History" % ticker)
    pyplot.ylabel("price ($)")
    startingDate = (datetime.datetime.now() - datetime.timedelta(days=constants.LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    pyplot.xlabel("days after %s" % startingDate)

    # plot price history and trend lines
    trend = regression.model.predict(regression.days)
    pyplot.plot(regression.days, regression.prices, linewidth=3, label="price")
    pyplot.plot(regression.days, trend, color="red", label="linear regression")
    pyplot.plot(regression.days, meanReversion.movingAverages, color="darkorange", label="moving average")

    # plot target price
    label = "price target ($%.2f)" % analysis.target_price
    targetPriceLine = [[analysis.target_price]] * len(regression.days)
    pyplot.plot(regression.days, targetPriceLine, color="yellowgreen", linestyle="--", label=label)

    # plot present day
    presentDayLine = [[constants.LOOKBACK_DAYS]] * len(regression.days)
    pyplot.plot(presentDayLine, regression.prices, color="black", label="today")

    # generate visualization
    pyplot.legend()
    figure = pyplot.gcf()
    return matplotlib.backends.backend_agg.FigureCanvasAgg(figure)
