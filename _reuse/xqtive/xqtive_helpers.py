import json
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
from queue import PriorityQueue
from multiprocessing.managers import SyncManager

# Create XqtiveSyncMgr
class XqtiveSyncMgr(SyncManager):
    pass

class StatesQueue():
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

def read_config(config_filepath):
    with open(config_filepath) as cfgFile:
        config = json.load(cfgFile)
    return(config)

def iot_onmsg(msg):
    msg_payload = msg.payload
    dict_payload = json.loads(msg_payload)
    message = dict_payload["message"]
    print(message)
    message_array = message.split(";")
    states_queue.put(message_array)

def iot_connect(obj):
    certs_dir = obj["certs_dir"]
    global states_queue
    states_queue = obj["states_queue"]
    config = obj["config"]
    # Configure connection to IoT broker
    iot_broker = config["iot"]["broker_address"]
    iot_port = config["iot"]["broker_port"]
    subscribe_topic = config["iot"]["subscribe_topic"]
    iot_ca_cert_path = f"{certs_dir}/{config['iot']['ca_cert']}"
    iot_client_cert_path = f"{certs_dir}/{config['iot']['client_cert']}"
    iot_client_key_path = f"{certs_dir}/{config['iot']['client_key']}"

    # A connection to iot is established at the beginning and if publish fails
    iot_comm = AWSIoTMQTTClient("xqtive")
    iot_comm.onMessage = iot_onmsg
    iot_comm.configureEndpoint(iot_broker, iot_port)
    iot_comm.configureCredentials(iot_ca_cert_path, iot_client_key_path, iot_client_cert_path)
    iot_comm.connect()
    iot_comm.subscribe(subscribe_topic, 1, None)
    return iot_comm

def iot_close(iot_comm):
    iot_comm.disconnect()
