import random

import constants

def crunchNumbers(crypto):
    """Crunch the numbers and determine if buying this cryptocurrency is a smart move."""
    if constants.IS_SIMULATION:
        # for now- 20% chance of always buy 1 with +1 dollar price target
        # TODO: remove this- number crunching should be the same regardless of simulation
        if not random.randint(0, 4):
            return True, 1.0, crypto.buyPrice + 1.0
        else:
            return False, None, None
    else:
        raise NotImplementedError
