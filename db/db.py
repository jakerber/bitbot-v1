"""BitBot database operations module."""
import constants
import flask_pymongo
import logger
import os

class BitBotDB:
    """Object to communication with the BitBot database."""
    def __init__(self, app):
        self.app = app
        self.logger = logger.BitBotLogger("MongoDB")

        # initialize mongo connection
        app.config["MONGO_URI"] = constants.MONGODB_URI
        self.mongo = flask_pymongo.PyMongo(app)

    def insert(self, model):
        """Insert single entry into a collection."""
        self.mongo.db[model.collectionName].insert_one(model.__dict__)
        self.logger.log("inserted 1 entry into %s collection" % model.collectionName)

    def insertMany(self, models):
        """Insert many entries into a collection."""
        self.mongo.db[models[0].collectionName].insert([model.__dict__ for model in models])
        self.logger.log("inserted %s entries into %s collection" % (len(models), models[0].collectionName))

    def find(self, collectionName, filter={}, sort=()):
        """Find an entry based on a data point."""
        if sort:
            return list(self.mongo.db[collectionName].find(filter).sort(*sort))
        return list(self.mongo.db[collectionName].find(filter))
