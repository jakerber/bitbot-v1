"""Data visualization module."""
import constants
import datetime
import matplotlib
import numpy
from matplotlib import pyplot
from algos import linear_regression
from algos import mean_reversion

X_AXIS_TICKS = 4

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
    pyplot.xlabel("timestamp (UTC)")
    pyplot.grid(color="silver", linestyle="--", linewidth=0.5, alpha=0.5)

    # plot price history and trend lines
    pyplot.plot(regression.timestamps, regression.prices, linewidth=3, label=("price ($%.3f)" % currentPrice))
    pyplot.plot(regression.timestamps, regression.trend, color="red", label="linear regression")

    # plot 24-hour volume-weighted average price
    pyplot.plot(regression.timestamps, meanReversion.vwapPrices, color="darkorange", label="24-hour VWAP")

    # plot target price
    label = "price target ($%.3f)" % analysis.target_price
    targetPriceLine = [[analysis.target_price]] * len(regression.timestamps)
    pyplot.plot(regression.timestamps, targetPriceLine, color="yellowgreen", linestyle="--", label=label)

    # plot present day
    currentTimestamp = datetime.datetime.utcnow().timestamp()
    pyplot.axvline(x=currentTimestamp, color="black", label="now")

    # set x-axis labels to readable datetimes
    labels = []
    startingTimestamp = regression.timestamps[0][0]
    endingTimestamp = currentTimestamp
    step = (endingTimestamp - startingTimestamp) / X_AXIS_TICKS
    ticks = numpy.arange(startingTimestamp, endingTimestamp, step=step)
    for timestamp in ticks:
        tickDatetime = datetime.datetime.fromtimestamp(timestamp)
        labels.append(tickDatetime.strftime("%m-%d %H:%M"))
    pyplot.xticks(ticks, labels)

    # generate visualization
    pyplot.legend()
    figure = pyplot.gcf()
    return matplotlib.backends.backend_agg.FigureCanvasAgg(figure)
