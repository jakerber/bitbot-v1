"""Entry point for BitBot."""
import argparse
import sys

import bitbot
import bitbot_sim

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="trade cryptos with BitBot")
    parser.add_argument("dropThreshold", type=float, help="percent drop that triggers a buy")
    parser.add_argument("timeWindow", type=float, help="window that drop_threshold has to occur in to trigger a buy")
    parser.add_argument("maxBuy", type=float, help="max amount in USD to spend per buy")
    parser.add_argument("--sim", action="store_true", help="use BitBot simulator instead of real trade execution.")
    args = parser.parse_args()

    # initialize BitBot
    if args.sim:
        bitbot = bitbot.BitBot(args.dropThreshold, args.timeWindow, args.maxBuy)
    else:
        bitbot = bitbot_sim.BitBotSimulator(args.dropThreshold, args.timeWindow, args.maxBuy)

    # startup bitbot
    bitbot.start()
