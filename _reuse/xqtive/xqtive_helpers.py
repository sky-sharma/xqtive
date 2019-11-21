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
    def __init__(self, states_priorities, normal_state_priority):
        """

        """
        XqtiveSyncMgr.register("PriorityQueue", PriorityQueue)
        states_queue_mgr = XqtiveSyncMgr()
        states_queue_mgr.start()
        self.queue = states_queue_mgr.PriorityQueue()

        self.put_count = 0

        # All predefined priorities are ABOVE normal.
        self.priority_per_state = states_priorities
        self.normal_state_priority = normal_state_priority

    def put(self, state_and_params):
        # If state_to_exec is one of the ones in self.priority_per_state then retrieve
        # corresponding priority. Otherwise priority is normal_state_priority.
        state_to_exec = state_and_params[0]
        priority = self.priority_per_state.get(state_to_exec, self.normal_state_priority)
        self.put_count += 1
        print(f"putting; priority: {priority}; put_count: {self.put_count}; state_and_params: {state_and_params}; state_prio: {self.priority_per_state.get(state_to_exec)}")
        self.queue.put((priority, self.put_count, state_and_params))

    def get(self):
        return self.queue.get()[2]    # Skip priority and put_count to get just the item

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
