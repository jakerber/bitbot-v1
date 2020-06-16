"""BitBot data visualization module."""
import constants
import datetime
import matplotlib
import numpy
from matplotlib import pyplot
from algos import mean_reversion
from algos import linear_regression

SECONDS_IN_DAY = 3600 * 24
CHROME_IMAGE_BACKGROUND_COLOR_HEX = "#0e0e0e"

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
    pyplot.grid(color="silver", linestyle="--", linewidth=0.5, alpha=0.5)

    # plot price history with VWAP and trend line
    pyplot.plot(regression.timestamps, regression.prices, linewidth=3, label=("price ($%.3f)" % currentPrice))
    pyplot.plot(regression.timestamps, regression.trend, color="red", linewidth=1.25, linestyle="--", label="price trend")
    pyplot.plot(regression.timestamps, meanReversion.vwapPrices, color="darkorange", label="VWAP ($%.3f)" % currentVWAP)

    # plot present day
    currentTimestamp = datetime.datetime.utcnow().timestamp()
    pyplot.axvline(x=currentTimestamp, color="grey", label="now")

    # set x-axis ticks to incrementing hours
    labels = []
    startingTimestamp = regression.timestamps[0][0]
    ticks = numpy.arange(startingTimestamp, currentTimestamp, step=SECONDS_IN_DAY)
    for tickTimestamp in ticks:
        daysFromStart = (tickTimestamp - startingTimestamp) / SECONDS_IN_DAY
        labels.append("%i" % daysFromStart)

    # add tick for now and display labels
    ticks = numpy.append(ticks, currentTimestamp)
    currentDaysFromStart = (currentTimestamp - startingTimestamp) / SECONDS_IN_DAY
    labels.append("%.2f" % currentDaysFromStart)
    pyplot.xticks(ticks, labels)

    # generate visualization
    pyplot.legend()
    figure = pyplot.gcf()
    figure.patch.set_facecolor(CHROME_IMAGE_BACKGROUND_COLOR_HEX)  # dark theme
    return matplotlib.backends.backend_agg.FigureCanvasAgg(figure)
