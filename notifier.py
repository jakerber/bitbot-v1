"""Module for sending BitBot notifications."""
import constants
import logger
import requests

# initialize logger
logger = logger.Logger("Notifier")


class Notifier:
    """Notifier object."""
    def __init__(self):
        self.logger = logger

    def email(self, subject, body):
        """Send an email notification."""
        self.logger.log("sending notification via email to %s: %s" % (constants.MY_EMAIL, subject))

        # request email notification via mailgun API
        resp = requests.post(constants.MAILGUN_API_URL + "/messages",
                             auth=("api", constants.MAILGUN_API_KEY),
                             data={"from": "BitBot Notifier <bitbotnotifier@%s>" % constants.MAILGUN_DOMAIN,
                                   "to": [constants.MY_EMAIL],
                                   "subject": subject,
                                   "text": body})

        # log success
        if resp.status_code == 200:
            self.logger.log("email notification sent successfully")
            return

        # log failure, if any
        try:
            errorMessage = resp.json()["message"]
        except Exception:
            errorMessage = "error unknown"
        self.logger.log("unable to send email notification: %s" % errorMessage)
