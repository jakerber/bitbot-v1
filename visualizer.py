"""BitBot data visualization module."""
import constants
import datetime
import matplotlib
import numpy
from matplotlib import pyplot
from algos import mean_reversion
from algos import linear_regression

CHROME_IMAGE_BACKGROUND_COLOR_HEX = "#0e0e0e"
SECONDS_IN_DAY = 3600 * 24

# ensure Flask doesn't try to create GUI windows
matplotlib.use("Agg")

def visualize(ticker, currentPrices, priceHistory):
    """Generate a visualization of cryptocurrency price analysis."""
    # analyze price data
    meanReversion = mean_reversion.MeanReversion(currentPrices, priceHistory)
    currentPrice = meanReversion.currentPrice
    currentVWAP = meanReversion.currentVWAP
    regression = linear_regression.LinearRegression(meanReversion.currentPrice, meanReversion.priceHistory)
    analysis = meanReversion.analyze()

    # clear any previous visualizations
    pyplot.clf()
    pyplot.cla()
    pyplot.close()

    # dark theme
    pyplot.rc("text", color="lightgrey")
    pyplot.rc("axes", facecolor=CHROME_IMAGE_BACKGROUND_COLOR_HEX)
    pyplot.rc("axes", edgecolor=CHROME_IMAGE_BACKGROUND_COLOR_HEX)
    pyplot.rc("axes", labelcolor="lightgrey")
    pyplot.rc("xtick", color="lightgrey")
    pyplot.rc("ytick", color="lightgrey")

    # generate historical price visualization
    name = constants.KRAKEN_CRYPTO_CONFIGS.get(ticker).get("name")
    pyplot.title("%s History" % name)
    pyplot.ylabel("Price ($)")
    pyplot.xlabel("Time (days)")
    pyplot.grid(color="silver", linestyle="--", linewidth=0.65, alpha=0.2)

    # plot bollinger bands
    pyplot.plot(regression.timestamps, meanReversion.upperBollinger, color="dimgrey", linewidth=1.25, alpha=0.5, label="bollinger bands")
    pyplot.plot(regression.timestamps, meanReversion.lowerBollinger, color="dimgrey", linewidth=1.25, alpha=0.5)

    # plot price history with VWAP and trend line
    pyplot.plot(regression.timestamps, regression.trend, color="red", linewidth=1, linestyle="--", label="price trend")
    pyplot.plot(regression.timestamps, regression.prices, color="cornflowerblue", linewidth=1.5, label=("price ($%.3f)" % currentPrice))
    pyplot.plot(regression.timestamps, meanReversion.vwaps, color="orange", linewidth=1.5, label="VWAP ($%.3f)" % currentVWAP)

    # set x-axis ticks to incrementing days
    labels = []
    startingTimestamp = regression.timestamps[0][0]
    currentTimestamp = datetime.datetime.utcnow().timestamp()
    ticks = numpy.arange(startingTimestamp, currentTimestamp, step=(SECONDS_IN_DAY * 2))
    for tickTimestamp in ticks:
        daysFromStart = (tickTimestamp - startingTimestamp) / SECONDS_IN_DAY
        labels.append("%i" % daysFromStart)

    # add tick for now and display labels
    ticks = numpy.append(ticks, currentTimestamp)
    currentDaysFromStart = (currentTimestamp - startingTimestamp) / SECONDS_IN_DAY
    labels.append("%.1f (now)" % currentDaysFromStart)
    pyplot.xticks(ticks, labels)

    # generate visualization
    pyplot.legend()
    figure = pyplot.gcf()
    figure.patch.set_facecolor(CHROME_IMAGE_BACKGROUND_COLOR_HEX)  # dark theme
    return matplotlib.backends.backend_agg.FigureCanvasAgg(figure)
