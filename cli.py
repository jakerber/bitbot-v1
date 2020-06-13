"""BitBot dynamic command-line interface module."""
import app
import sys

USAGE = "usage: python cli.py [api] [arguments]"

if __name__ == "__main__":
    """Execute BitBot APIs."""
    if len(sys.argv) < 2:
        raise RuntimeError(USAGE)

    # fetch requested API method and call with provided arguments
    methodName = sys.argv[1].replace("-", "_")
    args = sys.argv[2:]
    api = getattr(app, methodName)
    api(*args)
