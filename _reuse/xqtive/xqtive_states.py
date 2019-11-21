# xqtive_state.py
import time

class States(object):
    """
    This class defines a generic state machine. Each method is a state.
    Child classes can be created which extend or override these states.
    States named in all caps are public (can be called from outside). States
    not named in all caps are private (can only be called by other states)
    """

    def __init__(self, config):
        """
        Defines private data that all states share
        """

        # Set hi_priority values for important states
        self.hi_priorities = {"SHUTDOWN": 1, "WAIT": 2}
        try:
            # See if there are any custom states with hi priorities
            cust_hi_priorities = self.cust_hi_priorities
            if cust_hi_priorities == None:
                cust_hi_priorities = {}
        except:
            cust_hi_priorities = {}
            pass

        # Merge existing hi_priorities dict with custom ones
        self.hi_priorities.update(cust_hi_priorities)

        # wait_resolution is the minimum amount of sleep time
        # while executing a Wait. Needed to avoid hogging the CPU.
        # If one is not provided in the config, use default
        default_wait_resolution = 0.1
        states_cfg = config.get("states")
        if states_cfg != None:
            self.wait_resolution = states_cfg.get("wait_resolution", default_wait_resolution)
        else:
            self.wait_resolution = default_wait_resolution

    def SLEEP(self, params):
        """
        Method using time.sleep
        """
        print(f"Sleeping {params}")
        time.sleep(float(params[0]))

    def WAIT(self, params):
        """
        Non-blocking Wait. Achieved by offloading to WaitUntilDeadline state
        """
        self.wait_deadline = time.time() + float(params[0])
        next_states = [["WaitUntilDeadline"]]    # Send as list of lists
        return next_states

    def WaitUntilDeadline(self):
        """
        Offloaded from WAIT state. Non-blocking.
        """
        if time.time() >= self.wait_deadline:
            # Waiting is done
            self.wait_deadline = 0
        else:
            time.sleep(self.wait_resolution)
            next_states_params = [["WaitUntilDeadline"]]    # Send as list of lists
            return next_states_params

    def SHUTDOWN(self):
        return "SHUTDOWN"
