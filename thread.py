"""Thread module for spawning threads."""
import threading

import logger

# lock/unlock with THREAD_LOCK.acquire() / .release()
THREAD_LOCK = threading.Lock()

class Thread(threading.Thread):
    """Thread object."""
    def __init__(self, inst, targetMethod, killMethod):
        super(Thread, self).__init__()
        self.targetMethod = targetMethod
        self.killMethod = killMethod
        self.logger = logger.Logger("%s THREAD" % inst)

    def run(self):
        """Execute target method."""
        self.logger.log("executing target method")
        self.targetMethod()  # call method

    def kill(self):
        """Kill target method."""
        self.logger.log("killing thread")
        self.killMethod()
