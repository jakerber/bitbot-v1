"""Script to call app endpoints via the Heroku scheduler."""
import app
import sys


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError("method name must be provided")
    methodName = sys.argv[1]
    method = getattr(app, methodName)
    args = sys.argv[2:]
    method(*args)
