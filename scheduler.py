"""Script to call bitbot endpoints via the Heroku scheduler."""
import app
import sys


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError("method name must be provided")

    # fetch requested method and call with provided arguments
    methodName = sys.argv[1]
    args = sys.argv[2:]
    method = getattr(app, methodName)
    method(*args)
