"""Simple Flask app to keep server instance from crashing."""
import os
import flask

# https://stackoverflow.com/questions/39139165/running-simple-python-script-continuously-on-heroku
app = flask.Flask(__name__)
app.run(os.environ.get("PORT"))
