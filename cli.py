"""BitBot dynamic command-line interface module."""
import app
import sys

USAGE = "usage: python cli.py [api] [arguments]"

if __name__ == "__main__":
    """Execute BitBot APIs."""
    if len(sys.argv) < 2:
        raise RuntimeError(USAGE)

    # parse requested API method and arguments
    commandName = sys.argv[1]
    methodName = commandName.replace("-", "_")
    args = sys.argv[2:]

    # safely execute command
    try:
        api = getattr(app, methodName)
    except AttributeError:
        print("command not found: %s" % commandName)
        sys.exit()
    else:
        api(*args)
