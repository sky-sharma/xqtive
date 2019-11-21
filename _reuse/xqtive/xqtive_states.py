# xqtive_state.py
import time

class States(object):
    """
    This class defines a generic state machine. Each method is a state.
    Child classes can be created which extend or override these states.
    """

    def __init__(self, config):
        """
        Defines private data that all states share
        """
        self.hi_priorities = {"Shutdown": 1, "Wait": 2}

        # wait_resolution is the minimum amount of sleep time
        # while executing a Wait. Needed to avoid hogging the CPU
        self.wait_resolution = config.get("wait_resolution", 0.1)

    def Sleep(self, params):
        """
        Method using time.sleep
        """
        print(f"Sleeping {params}")
        time.sleep(float(params[0]))

    def Wait(self, params):
        """
        Non-blocking Wait
        """

    def Shutdown(self):
        return True    # Returning 'True' causes state machine to NOT continue
