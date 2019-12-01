import os
import json
import time
import logging
import xqtive
from queue import Queue
from multiprocessing import Process
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from paho.mqtt.client import Client as MosQuiTToClient
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT

class IotProvider():
    def __init__(self, iot_provider_cfg):
        self.sm_name = iot_provider_cfg["sm_name"]
        self.iot_broker = iot_provider_cfg["iot_broker"]
        self. iot_port = iot_provider_cfg["iot_port"]
        self.iot_ca_cert_path = iot_provider_cfg["iot_ca_cert_path"]
        self.iot_client_key_path = iot_provider_cfg["iot_client_key_path"]
        self.iot_client_cert_path = iot_provider_cfg["iot_client_cert_path"]
        self.subscribe_topic = iot_provider_cfg["subscribe_topic"]

    def onmsg(self, msg_payload):
        try:
            dict_payload = json.loads(msg_payload)
            msg_type = dict_payload["msg_type"].strip().lower()    # Remove whitespace from both ends and make lower-case
            value = dict_payload["value"].strip()
            if msg_type == "run_sequence":
                states_and_params = read_sequence_file(f"{config['sequences_dir']}/{value}.seq")
                for state_and_params in states_and_params:
                    states_queue.put(state_and_params, "from_sequence")
            elif msg_type == "run_state":
                state_and_params = state_params_str_to_array(value)
                states_queue.put(state_and_params, "from_iot")
        except Exception as e:
            iot_rw_logger.error(f"ERROR; iot_onmsg; {sm_name}; {type(e).__name__}; {e}")

    def connect(self):
        pass

    def disconnect(self):
        pass



class AwsIotMqtt(IotProvider):

    def onmsg(self, msg):
        msg_payload = msg.payload
        super().onmsg(msg_payload)

    def connect(self):
        # A connection to iot is established at the beginning and if publish fails
        self.aws_iot_mqtt_comm = AWSIoTMQTTClient(f"{self.sm_name}_xqtive")
        self.aws_iot_mqtt_comm.onMessage = self.onmsg
        self.aws_iot_mqtt_comm.configureEndpoint(self.iot_broker, self.iot_port)
        self.aws_iot_mqtt_comm.configureCredentials(self.iot_ca_cert_path, self.iot_client_key_path, self.iot_client_cert_path)
        self.aws_iot_mqtt_comm.connect()
        self.aws_iot_mqtt_comm.subscribe(self.subscribe_topic, 1, None)
        #return aws_iot_mqtt_comm

    def disconnect(self, aws_iot_mqtt_comm):
        self.aws_iot_mqtt_comm.close()

    def publish(self, publish_topic, msg_str, qos):
        self.aws_iot_mqtt_comm.publish(publish_topic, msg_str, QoS=qos)



class MosQuiTTo(IotProvider):

    def on_connect(client, userdata, flags, rc):
        client.subscribe(self.subscribe_topic, qos=0)
        print(f"subscribed to {self.subscribe_topic}")

    def onmsg(self, client, userdata, msg):
        msg_payload = msg.payload
        super().onmsg(msg_payload)

    def connect(self):
        # A connection to iot is established at the beginning and if publish fails
        self.mosquitto_comm = MosQuiTToClient()
        self.mosquitto_comm.on_connect = self.on_connect
        self.mosquitto_comm.on_message = self.onmsg
        self.mosquitto_comm.tls_set(local_ca_cert_path, local_client_cert_path,local_client_key_path, cert_reqs=ssl.CERT_REQUIRED)
        self.mosquitto_comm.connect(local_broker, local_port)
        self.mosquitto_comm.loop_start()

    def disconnect(self, aws_iot_mqtt_comm):
        self.mosquitto_comm.close()

    def publish(self, publish_topic, msg_str, qos):
        self.mosquitto_comm.publish(publish_topic, msg_str, qos=qos)



def read_config(config_filepath):
    """
    Read config JSON file and return as managed dict
    """
    with open(config_filepath) as cfgFile:
        config = json.load(cfgFile)
    return(config)


def state_params_str_to_array(state_params_str):
    """
    Take a ';' separated state_params_str and return a state_params_array with capitalized state
    """
    state_and_params = state_params_str.split(";")

    # Trim whitespace from both ends of states, params
    state_and_params_stripped = []
    for element in state_and_params:
        state_and_params_stripped.append(element.strip())

    # Capitalize state: all states called from the outside have to be public.
    # Public states are indicated by being named all upper case
    state_and_params_with_cap_state = [state_and_params_stripped[0].upper()] + state_and_params_stripped[1:]
    return state_and_params_with_cap_state


def get_sequence_names(config):
    sequence_names = []
    sequence_names += [filename for filename in os.listdir(config["sequences_dir"]) if filename.endswith(".seq")]
    return sequence_names


def read_sequence_file(sequence_filepath):
    """
    Read a sequence file and convert to states_and_params list of lists
    """
    seq_file = open(sequence_filepath, "r")
    state_params_strs = seq_file.readlines()
    states_and_params = []
    for state_params_str in state_params_strs:
        if state_params_str in ["\r", "\n", "\r\n"] or state_params_str.startswith("//"):    # Ignore blank and comment lines (start with '//')
            pass
        else:
            state_and_params = state_params_str_to_array(state_params_str)
            states_and_params.append(state_and_params)
    return states_and_params


def iot_onmsg(msg):
    try:
        msg_payload = msg.payload
        dict_payload = json.loads(msg_payload)
        msg_type = dict_payload["msg_type"].strip().lower()    # Remove whitespace from both ends and make lower-case
        value = dict_payload["value"].strip()
        if msg_type == "run_sequence":
            states_and_params = read_sequence_file(f"{config['sequences_dir']}/{value}.seq")
            for state_and_params in states_and_params:
                states_queue.put(state_and_params, "from_sequence")
        elif msg_type == "run_state":
            state_and_params = state_params_str_to_array(value)
            states_queue.put(state_and_params, "from_iot")
    except Exception as e:
        iot_rw_logger.error(f"ERROR; iot_onmsg; {sm_name}; {type(e).__name__}; {e}")


def iot_rw(obj):
    global sm_name
    sm_name = obj.get("sm_name")
    certs_dir = obj.get("certs_dir")
    iot_provider = obj.get("iot_provider")
    global states_queue
    all_sm_queues = obj.get("all_sm_queues")
    this_sm_queues = all_sm_queues[sm_name]
    states_queue = this_sm_queues["states_queue"]
    #iot_rw_queue = this_sm_queues["iot_rw_queue"]
    iot_rw_queues = this_sm_queues["iot_rw_queues"]
    global config
    config = obj.get("config")
    #dependents = obj.get("dependents")
    process_name = f"{sm_name}_iot_rw"
    global iot_rw_logger
    iot_rw_logger = create_logger(process_name, config)
    try:
        # Configure connection to IoT broker
        iot_broker = config[iot_provider]["broker_address"]
        iot_port = config[iot_provider]["broker_port"]
        subscribe_topic = f"{config[iot_provider]['subscribe_topic_prefix']}/{sm_name}"
        #dependent_topics = []
        #for dependent in dependents:
        #    dependent_topics.append(f"{config[iot_provider]['subscribe_topic_prefix']}/{dependent}")
        publish_topic = config[iot_provider]["publish_topic"]
        iot_ca_cert_path = f"{certs_dir}/{config[iot_provider]['ca_cert']}"
        iot_client_cert_path = f"{certs_dir}/{config[iot_provider]['client_cert']}"
        iot_client_key_path = f"{certs_dir}/{config[iot_provider]['client_key']}"
    except Exception as e:
        iot_rw_logger.error(f"ERROR; {process_name}; {type(e).__name__}; {e}")
    iot_rw_queue = iot_rw_queues[iot_provider]
    iot_provider_cfg = {
        "sm_name": sm_name,
        "iot_broker": iot_broker,
        "iot_port": iot_port,
        "iot_ca_cert_path": iot_ca_cert_path,
        "iot_client_key_path": iot_client_key_path,
        "iot_client_cert_path": iot_client_cert_path,
        "subscribe_topic": subscribe_topic}
    if iot_provider == "aws_iot_mqtt":
        iot_comm = AwsIotMqtt(iot_provider_cfg)
    elif iot_provider == "mosquitto":
        iot_comm = MosQuiTToClient(iot_provider_cfg)
    iot_connected = False
    while True:
        try:
            if not iot_connected:
                try:
                    iot_comm.connect()
                    iot_connected = True
                except Exception as e:
                    # If there was an error during connection close and wait before trying again
                    #iot_comm.close()
                    iot_comm.disconnect()
                    time.sleep(config[iot_provider]["wait_between_reconn_attempts"])
                    iot_rw_logger.error(f"ERROR; {process_name}; {type(e).__name__}; {e}; reconnecting...")
            else:
                dequeued = iot_rw_queue.get()
                if dequeued == "SHUTDOWN":
                    # Send SHUTDOWN to topics of dependents, then exit
                    #msg_dict = {"type": "run_state", "value": "SHUTDOWN"}
                    #msg_str = json.dumps(msg_dict)
                    #for dependent_topic in dependent_topics:
                    #    iot_comm.publish(dependent_topic, msg_str, QoS=1)
                    break
                else:
                    #type = dequeued["type"]
                    msg_dict = dequeued
                    msg_str = json.dumps(msg_dict)
                    #iot_comm.publish(publish_topic, msg_str, QoS=1)
                    iot_comm.publish(publish_topic, msg_str, 1)
        except Exception as e:
            iot_rw_logger.error(f"ERROR; {process_name}; {type(e).__name__}; {e}")


def iot_close(iot_comm):
    iot_comm.disconnect()


def create_logger(logger_name, config):
    logging.basicConfig(filename=f"/var/log/{logger_name}.log", format="%(asctime)s %(message)s", level=config["log_level"])
    logger = logging.getLogger(logger_name)
    return logger


def launch_state_machines(sm_defs, config, certs_dir):
    all_sm_queues = {}
    for sm_def in sm_defs:
        sm_name = sm_def["sm_name"]
        #uses_iot = sm_def["uses_iot"]
        iot_providers = sm_def.get("iot_providers")
        #sm_queues = create_sm_queues(config, uses_iot)
        sm_queues = create_sm_queues(config, iot_providers)
        all_sm_queues[sm_name] = sm_queues
    all_sm = {}
    for sm_def in sm_defs:
        sm_name = sm_def["sm_name"]
        sm_class = sm_def["sm_class"]
        sm = create_sm(config, sm_def, all_sm_queues)
        all_sm[sm_name] = sm
    all_sm_processes = []
    for sm_def in sm_defs:
        sm_name = sm_def["sm_name"]
        #uses_iot = sm_def["uses_iot"]
        iot_providers = sm_def.get("iot_providers")
        sm = all_sm[sm_name]
        #sm_processes = launch_sm_processes(sm_name, sm, uses_iot, all_sm_queues, config, certs_dir)
        sm_processes = launch_sm_processes(sm_name, sm, iot_providers, all_sm_queues, config, certs_dir)
        all_sm_processes += sm_processes
    to_return = {"all_sm_queues": all_sm_queues, "all_sm": all_sm, "all_sm_processes": all_sm_processes}
    return to_return

#def create_sm_queues(config, uses_iot):
def create_sm_queues(config, iot_providers):
    # Create managed PriorityQueue for states
    states_queue = xqtive.XQtiveQueue(config)

    #if uses_iot:
    if iot_providers != None:
        iot_providers = list(iot_providers)    # Force iot_providers to a list in case an individual str was passed
        # Create managed queue for sending messages to process that writes to IoT brokers
        iot_rw_queues = {}
        for iot_provider in iot_providers:
            xqtive.XQtiveSyncMgr.register("Queue", Queue)
            iot_rw_queue_mgr = xqtive.XQtiveSyncMgr()
            iot_rw_queue_mgr.start()
            iot_rw_queue = iot_rw_queue_mgr.Queue()
            iot_rw_queues[iot_provider] = iot_rw_queue
    else:
        iot_rw_queues = None
    sm_queues = {"states_queue": states_queue, "iot_rw_queues": iot_rw_queues}
    return sm_queues

def create_sm(config, sm_def, all_sm_queues):
    sm_name = sm_def["sm_name"]
    sm_class = sm_def["sm_class"]
    sm = sm_class(sm_name, config, all_sm_queues)
    return sm

#def launch_sm_processes(sm_name, sm, uses_iot, all_sm_queues, config, certs_dir):
def launch_sm_processes(sm_name, sm, iot_providers, all_sm_queues, config, certs_dir):
    launched_processes = []

    #if uses_iot:
    if iot_providers != None:
        iot_providers = list(iot_providers)    # Force iot_providers to a list in case an individual str was passed
        # Launch IoT process which receives messages to publish to IoT
        for iot_provider in iot_providers:
            iot_rw_cfg = {
                "sm_name": sm_name,
                "certs_dir": certs_dir,
                "iot_provider": iot_provider,
                "all_sm_queues": all_sm_queues,
                "config": config}
            iot_rw_process = Process(target = iot_rw, args = [iot_rw_cfg])
            iot_rw_process.start()
            launched_processes.append(iot_rw_process)

    # Launch sm process
    sm_cfg = {
        "sm_name": sm_name,
        "sm": sm,
        "config": config,
        "all_sm_queues": all_sm_queues}
    sm_process = Process(target = xqtive.xqtive_state_machine, args = [sm_cfg])
    sm_process.start()
    launched_processes.append(sm_process)
    return launched_processes
