"""Entry point for BitBot."""
import argparse
import bitbot
import constants
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="trade cryptos with BitBot")
    parser.add_argument("--sim", action="store_true", help="use simulation instead of real trade execution.")
    args = parser.parse_args()

    # set constant if simulation
    if args.sim:
        constants.IS_SIMULATION = True

    # initialize and startup BitBot
    bitbot = bitbot.BitBot()
    bitbot.start()
