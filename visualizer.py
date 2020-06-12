"""BitBot data visualization module."""
import datetime
import matplotlib
import numpy
from matplotlib import pyplot
from algos import mean_reversion

SECONDS_IN_DAY = 3600 * 24

# ensure Flask doesn't try to create GUI windows
matplotlib.use("Agg")

def visualize(ticker, currentPrices, priceHistory):
    """Generate a visualization of cryptocurrency price analysis."""
    # analyze price data
    meanReversion = mean_reversion.MeanReversion(currentPrices, priceHistory)
    currentPrice = meanReversion.currentPrice
    currentVWAP = meanReversion.currentVWAP
    regression = meanReversion.linearRegression
    analysis = meanReversion.analyze()

    # clear any previous visualizations
    pyplot.clf()
    pyplot.cla()
    pyplot.close()

    # generate historical price visualization
    pyplot.title("%s History" % ticker)
    pyplot.ylabel("Price ($)")
    pyplot.xlabel("Time (days)")
    pyplot.grid(color="silver", linestyle="--", linewidth=0.5, alpha=0.5)

    # plot price history with VWAP and trend line
    pyplot.plot(regression.timestamps, regression.prices, linewidth=3, label=("price ($%.3f)" % currentPrice))
    pyplot.plot(regression.timestamps, regression.trend, color="red", linewidth=1, linestyle="--", label="price trend")
    pyplot.plot(regression.timestamps, meanReversion.vwapPrices, color="darkorange", label="VWAP ($%.3f)" % currentVWAP)

    # plot present day
    currentTimestamp = datetime.datetime.utcnow().timestamp()
    pyplot.axvline(x=currentTimestamp, color="black", label="now")

    # set x-axis ticks to incrementing hours
    labels = []
    startingTimestamp = regression.timestamps[0][0]
    ticks = numpy.arange(startingTimestamp, currentTimestamp, step=SECONDS_IN_DAY)
    ticks = numpy.append(ticks, currentTimestamp)
    for tickTimestamp in ticks:
        daysFromStart = (tickTimestamp - startingTimestamp) / SECONDS_IN_DAY
        labels.append("%.2f" % daysFromStart)
    pyplot.xticks(ticks, labels)

    # generate visualization
    pyplot.legend()
    figure = pyplot.gcf()
    return matplotlib.backends.backend_agg.FigureCanvasAgg(figure)
