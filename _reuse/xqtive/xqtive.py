# xqtive.py
import time
from queue import PriorityQueue
from multiprocessing.managers import SyncManager

# Create XqtiveSyncMgr
class XqtiveSyncMgr(SyncManager):
    pass

class XqtiveStates(object):
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

class XqtiveQueue():
    """
    A class that takes care of putting / getting unique items in a PriorityQueue.
    The class wraps the functionality of including a priority with the put item AND
    it takes care of adding a unique count as the second element in the three-element tuple
    to break any ties between multiple items with the same priority. This is because we DON'T
    want comparisons between the actual items in case the priorities are the same.
    """
    def __init__(self, hi_priorities, normal_priority):
        """
        Create managed Priority queue shared between processes
        """
        XqtiveSyncMgr.register("PriorityQueue", PriorityQueue)
        states_queue_mgr = XqtiveSyncMgr()
        states_queue_mgr.start()
        self.queue = states_queue_mgr.PriorityQueue()

        self.put_count = 0

        # All predefined priorities are ABOVE normal.
        self.hi_priorities = hi_priorities
        self.normal_priority = normal_priority

    def put(self, state_and_params, **optional):
        # If state_to_exec is one of the ones in self.priority_per_state then retrieve
        # corresponding priority. Otherwise priority is normal_state_priority.
        state_to_exec = state_and_params[0]

        # See if an optional param was passed requesting for this state to be enqueued with the
        # same priority as the last state dequeued. If so this state was internally called.
        use_last_state_priority = optional.get("use_last_state_priority")
        if use_last_state_priority:
            priority = self.last_state_priority
        else:
            # If no priority was requested, see if the state has a predefined hi_priority and use that.
            # If no predefined priority exists then use normal_priority
            priority = self.hi_priorities.get(state_to_exec, self.normal_priority)

        self.put_count += 1
        print(f"putting; priority: {priority}; put_count: {self.put_count}; state_and_params: {state_and_params}; state_priority: {self.hi_priorities.get(state_to_exec)}")
        self.queue.put((priority, self.put_count, state_and_params))

    def get(self):
        gotten_item = self.queue.get()
        self.last_state_priority = gotten_item[0]
        gotten_item_data = gotten_item[2]    # Skip element 1 which is put_count

        # If gotten item is of HIGHEST priority (i.e. 0)
        # then no subsequent items are to be handled. So Flush queue.
        if self.last_state_priority == 0:
            while not self.queue.empty():
                try:
                    self.queue.get(False)
                except Exception as e:
                    if e.__str__ == "Empty":
                        # If queue is empty exit this while loop
                        continue
                self.queue.task_done()
        return gotten_item_data

def xqtive_state_machine(object):
    sm = object["state_machine"]
    states_queue = object["states_queue"]
    while True:
        # Get dict containing both the state to execute and parameters needed by that state.
        # Then separate the state to execute from the parameters.
        state_and_params = states_queue.get()    # Get highest priority item without priority number
        print(f" got: {state_and_params}")
        state_to_exec = state_and_params[0]
        params = state_and_params[1:]    # params may be missing depending on the type of state
        # Run the state using the parameters and decide if the state machine is to continue running or not.
        # NONE of the states return anything EXCEPT the "Shutdown" state which returns a True
        if params == []:
            returned = eval(f"sm.{state_to_exec}()")
        else:
            returned = eval(f"sm.{state_to_exec}(params)")
        if returned != None:
            if returned == "SHUTDOWN":
                # If a True was returned then the SHUTDOWN state was the last to run
                break
            elif type(returned).__name__ == "list":
                # If a list of states was returned, enqueue them
                for state_and_params in returned:
                    states_queue.put(state_and_params, use_last_state_priority=True)
