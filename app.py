"""Simple flask app to send requests to BitBot."""
import flask
import logger
import manager
import os
from db import db
from db import models

# initialize flask app
app = flask.Flask(__name__)

# initialize mongodb
mongodb = db.BitBotDB(app)

# initialize logger
logger = logger.Logger("app")

@app.route("/")
def home():
	"""Root endpoint of the app."""
	return "Hello, world!"

@app.route("/snapshot/<ticker>")
def snapshot(ticker):
	"""Store the price of a cryptocurrency."""
	try:
		allPrices = manager.getAllPrices(ticker)
	except Exception as err:
		return {"error": repr(err)}

	# fetch and relevant prices
	openPrice = float(allPrices["o"])
	highPrice = float(allPrices["h"][0])
	lowPrice = float(allPrices["l"][0])

	# store relevant prices in database
	priceModel = models.Price(ticker, openPrice, highPrice, lowPrice)
	try:
		mongodb.insert(priceModel)
	except Exception as err:
		return {"error": repr(err)}

	logger.log("successfully inserted %s price snapshot: %s" % (ticker, repr(priceModel)))
	return {"success": True, "repr": eval(repr(priceModel))}


if __name__ == "__main__":
	app.run()
