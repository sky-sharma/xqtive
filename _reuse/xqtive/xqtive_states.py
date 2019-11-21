# xqtive_state.py
import time

class States(object):
    """
    This class defines a generic state machine. Each method is a state.
    Child classes can be created which extend or override these states.
    """

    def __init__(self):
        """
        Defines private data that all states
        """
        self.state_priorities = {"Shutdown": 1}

    def Wait(self, params):
        """
        Simple wait using time.sleep
        """
        print(f"Waiting {params}")
        time.sleep(float(params[0]))

    def Shutdown(self):
        return True    # Returning 'True' causes state machine to NOT continue
