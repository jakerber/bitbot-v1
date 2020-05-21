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

        # email notifications
        self.myEmail = constants.MY_EMAIL
        self.emailSubjectTemplate = "BitBot %s alert!"
        self.mailgunFrom = "BitBot Notifier <bitbotnotifier@%s>" % constants.MAILGUN_DOMAIN

    def email(self, alertName, body):
        """Send an email notification."""
        self.logger.log("sending %s alert via email to %s" % (alertName, constants.MY_EMAIL))
        resp = requests.post(constants.MAILGUN_API_URL + "/messages",
                             auth=("api", constants.MAILGUN_API_KEY),
                             data={"from": self.mailgunFrom,
                                   "to": [constants.MY_EMAIL],
                                   "subject": self.emailSubjectTemplate % alertName,
                                   "text": body})

        # log failures, if any
        if resp.status_code != 200:
            try:
                errorMessage = resp.json()["message"]
            except Exception:
                errorMessage = "error unknown"
            self.logger.log("unable to send email notification: %s" % errorMessage)
