"""BitBot database operations module."""
import constants
import flask_pymongo
import logger
import os

class BitBotDB:
    """Object to communication with the BitBot database."""
    def __init__(self, app):
        self.app = app
        self.logger = logger.Logger("MongoDB")

        # initialize mongo connection
        app.config["MONGO_URI"] = constants.MONGODB_URI
        self.mongo = flask_pymongo.PyMongo(app)

    def delete(self, collectionName, filter):
        """Delete an entry in the collection."""
        self.mongo.db[collectionName].delete_one(filter)
        self.logger.log("deleted 1 entry from the %s collection" % collectionName)

    def deleteMany(self, collectionName, filter):
        """Delete mutliple entries in the collection."""
        count = self.mongo.db[collectionName].delete_many(filter).deleted_count
        self.logger.log("deleted %i entries from the %s collection" % (count, collectionName))

    def insert(self, model):
        """Insert a single entry into the collection."""
        self.mongo.db[model.collectionName].insert_one(model.__dict__)
        self.logger.log("inserted 1 entry into the %s collection" % model.collectionName)

    def insertMany(self, models):
        """Insert mutliple entries into the collection."""
        self.mongo.db[models[0].collectionName].insert([model.__dict__ for model in models])
        self.logger.log("inserted %i entries into the %s collection" % (len(models), models[0].collectionName))

    def find(self, collectionName, filter={}, sort=()):
        """Find a single entry in the collection."""
        if sort:
            return list(self.mongo.db[collectionName].find(filter).sort(*sort))
        return list(self.mongo.db[collectionName].find(filter))

    def update(self, collectionName, filter, update):
        """Update a single entry in the collection."""
        update = {"$set": update}
        self.mongo.db[collectionName].update_one(filter, update)
        self.logger.log("updated 1 entry in the %s collection" % collectionName)
