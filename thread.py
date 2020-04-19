"""Thread module."""
import threading

import logger

THREAD_LOCK = threading.Lock()

class Thread(threading.Thread):
    """Thread object."""
    def __init__(self, name, targetMethod, killMethod):
        super(Thread, self).__init__()
        self.targetMethod = targetMethod
        self.killMethod = killMethod
        self.logger = logger.Logger("%s THREAD" % name)

    def run(self):
        """Execute target method."""
        self.logger.log("executing target method")
        self.targetMethod()  # call method

    def kill(self):
        """Kill target method."""
        self.logger.log("killing thread")
        self.killMethod()
