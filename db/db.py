"""Database operations for BitBot."""
import flask_pymongo
import os

MONGO_URI_DEV = "mongodb://127.0.0.1:27017/bitbot"

class BitBotDB:
    """BitBot database object."""
    def __init__(self, app):
        self.app = app

        # set mongodb uri
        self.mongoUri = os.environ.get("MONGO_URI")
        if not self.mongoUri:
            self.mongoUri = "mongodb://127.0.0.1:27017/bitbot"

        # initialize mongo connection
        app.config["MONGO_URI"] = self.mongoUri
        self.mongo = flask_pymongo.PyMongo(app)

    def insert(self, model):
        """Insert data into a collection."""
        self.mongo.db[model.collectionName].insert_one(model.__dict__)
