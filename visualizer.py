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

def visualize(ticker, currentPrices, priceHistory):
    """Generate a visualization of a target price prediction."""
    # analyze price data
    meanReversion = mean_reversion.MeanReversion(currentPrices, priceHistory)
    currentPrice = meanReversion.currentPrice
    regression = linear_regression.LinearRegression(currentPrice, priceHistory)
    analysis = meanReversion.analyze()

    # generate historical price visualization
    pyplot.clf()
    pyplot.title("%s History" % ticker)
    pyplot.ylabel("price ($)")
    pyplot.xlabel("unix timestamp (beginning %i days ago)" % constants.LOOKBACK_DAYS)
    pyplot.grid(color="silver", linestyle="--", linewidth=0.5, alpha=0.5)

    # plot price history and trend lines
    trend = regression.model.predict(regression.timestamps)
    pyplot.plot(regression.timestamps, regression.prices, linewidth=3, label=("price ($%.3f)" % currentPrice))
    pyplot.plot(regression.timestamps, trend, color="red", label="linear regression")

    # plot 24-hour volume-weighted average price
    pyplot.plot(regression.timestamps, meanReversion.vwapPrices, color="darkorange", label="24-hour vwap")

    # plot target price
    label = "price target ($%.3f)" % analysis.target_price
    targetPriceLine = [[analysis.target_price]] * len(regression.timestamps)
    pyplot.plot(regression.timestamps, targetPriceLine, color="yellowgreen", linestyle="--", label=label)

    # plot present day
    presentDayLine = [[datetime.datetime.utcnow().timestamp()]] * len(regression.timestamps)
    pyplot.plot(presentDayLine, regression.prices, color="black", label="today")

    # generate visualization
    pyplot.legend()
    figure = pyplot.gcf()
    return matplotlib.backends.backend_agg.FigureCanvasAgg(figure)
