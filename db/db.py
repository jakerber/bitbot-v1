"""Database operations for BitBot."""
import constants
import flask_pymongo
import logger
import os

class BitBotDB:
    """BitBot database object."""
    def __init__(self, app):
        self.app = app
        self.logger = logger.Logger("MongoDB")

        # initialize mongo connection
        app.config["MONGO_URI"] = constants.MONGODB_URI
        self.mongo = flask_pymongo.PyMongo(app)

    def insert(self, model):
        """Insert single entry into a collection."""
        self.logger.log("inserting 1 model into %s collection" % model.collectionName)
        self.mongo.db[model.collectionName].insert_one(model.__dict__)

    def insertMany(self, models):
        """Insert many entries into a collection."""
        self.logger.log("inserting %s models into %s collection" % (len(models), models[0].collectionName))
        self.mongo.db[models[0].collectionName].insert([model.__dict__ for model in models])

    def find(self, collectionName, filter):
        """Find an entry based on a data point."""
        self.logger.log("searching %s collection by filter %s" % (collectionName, str(filter)))
        return self.mongo.db[collectionName].find(filter)
