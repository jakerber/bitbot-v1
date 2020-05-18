"""Database operations for BitBot."""
import constants
import flask_pymongo
import os

class BitBotDB:
    """BitBot database object."""
    def __init__(self, app):
        self.app = app

        # initialize mongo connection
        app.config["MONGO_URI"] = constants.MONGODB_URI
        self.mongo = flask_pymongo.PyMongo(app)

    def insert(self, model):
        """Insert data into a collection."""
        self.mongo.db[model.collectionName].insert_one(model.__dict__)
