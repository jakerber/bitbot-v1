"""Custom errors module."""

class UnsupportedCryptoError(RuntimeError):
    def __init__(self, ticker):
        super(UnsupportedCryptoError, self).__init__("BitBot does not support cryptocurrency %s" % ticker)
