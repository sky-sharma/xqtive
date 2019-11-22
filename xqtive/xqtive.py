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
        self.priority_values = {"HIGHEST": 0, "HIGH": 1, "INTERNAL": 2, "NORMAL": 3}
        self.hi_priorities = {"SHUTDOWN": "HIGH"}
        try:
            # See if there are any custom states with hi priorities
            cust_hi_priorities = self.cust_hi_priorities
            if cust_hi_priorities == None:
                cust_hi_priorities = {}
        except:
            cust_hi_priorities = {}
            pass

        # Make sure all priority entries are upper case
        cust_hi_priorities.update((key, val.upper()) for key, val in cust_hi_priorities.items())

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
    def __init__(self, priority_values, hi_priorities):
        """
        Create managed Priority queue shared between processes
        """
        XqtiveSyncMgr.register("PriorityQueue", PriorityQueue)
        states_queue_mgr = XqtiveSyncMgr()
        states_queue_mgr.start()

        self.queue = states_queue_mgr.PriorityQueue()
        self.put_count = 0
        self.priority_values = priority_values

        # All predefined priorities are ABOVE normal.
        self.hi_priorities = hi_priorities

    def put(self, state_and_params, **optional):
        # If state_to_exec is one of the ones in self.priority_per_state then retrieve
        # corresponding priority. Otherwise priority is normal_state_priority.
        state_to_exec = state_and_params[0]

        # Check if an optional priority_to_use was sent. If not see if this state has a predefined hi_priority. Else use normal priority.
        priority = optional.get("priority_to_use", self.hi_priorities.get(state_to_exec, "NORMAL"))

        self.put_count += 1
        self.queue.put((self.priority_values[priority], self.put_count, state_and_params))

    def get(self):
        gotten_item = self.queue.get()
        self.last_state_priority = gotten_item[0]
        gotten_item_data = gotten_item[2]    # Skip element 1 which is put_count

        # If gotten item is of High (1) or Highest (0)
        # then none of the other items already in the queue are to be handled. So Flush queue.
        if self.last_state_priority in [0, 1]:
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
    #publish_topic = object["publish_topic"]
    iot_rw_queue = object["iot_rw_queue"]
    while True:
        # Get dict containing both the state to execute and parameters needed by that state.
        # Then separate the state to execute from the parameters.
        state_and_params = states_queue.get()    # Get highest priority item without priority number
        state_to_exec = state_and_params[0]
        params = state_and_params[1:]    # params may be missing depending on the type of state
        # Run the state using the parameters and decide if the state machine is to continue running or not.
        # NONE of the states return anything EXCEPT the "Shutdown" state which returns a True
        #print(f"1; {publish_topic}; {str(state_and_params)}")
        iot_rw_queue.put(state_and_params)
        #iot_comm.publish(publish_topic, "blahdi", QoS=0)
        #print("2")
        if params == []:
            returned = eval(f"sm.{state_to_exec}()")
        else:
            returned = eval(f"sm.{state_to_exec}(params)")
        if returned != None:
            if returned == "SHUTDOWN":
                # If SHUTDOWN received then SHUTDOWN state was the last to run
                iot_rw_queue.put("SHUTDOWN")
                break
            elif type(returned).__name__ == "list":
                if type(returned[0]).__name__ == "list":
                    # If returned contains list of lists
                    next_states_params = returned
                else:
                    # If returned does not contain list of lists, it probably contains only one list.
                    # Turn that into list of lists to be consistent
                    next_states_params = [returned]
                # If a list of states_params was returned, enqueue them
                for state_and_params in next_states_params:
                    states_queue.put(state_and_params, priority_to_use="INTERNAL")
