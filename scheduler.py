"""Script to call app endpoints via the Heroku scheduler."""
import app
import sys
from db import models

def store():
    firstLine = True
    with open("datasets/btc-usd-history.csv") as btcUsdChart:
        for line in btcUsdChart:
            if firstLine:
                firstLine = False
                continue

            dataSplit = line.strip().split(",")
            date, openP, high, low = dataSplit[1], float(dataSplit[3]), float(dataSplit[4]), float(dataSplit[5])

            newPriceModel = models.Price("BTC", openP, high, low)
            newPriceModel.datetime = date
            app.mongodb.insert(newPriceModel)






if __name__ == "__main__":
    if sys.argv[1] == "jackpot":
        store()
    sys.exit()

    if len(sys.argv) < 2:
        raise RuntimeError("function name must be provided")
    methodName = sys.argv[1]
    method = getattr(app, methodName)
    args = sys.argv[2:]
    method(*args)
