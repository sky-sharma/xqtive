import os
import json
import time
import logging
import ssl
import xqtive
import sys
from pathlib import Path
from queue import Queue
from multiprocessing import Process
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from paho.mqtt import client as mqtt
from paho.mqtt.client import Client
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT

class IotProvider():
    """
    Generic class defining all IoT Providers (e.g. AWS, MosQuiTTo etc.)
    """

    def __init__(self, iot_provider_cfg):
        self.sm_name = iot_provider_cfg["sm_name"]
        self.iot_broker = iot_provider_cfg["iot_broker"]
        self. iot_port = iot_provider_cfg["iot_port"]
        self.iot_ca_cert_path = iot_provider_cfg["iot_ca_cert_path"]
        self.iot_client_key_path = iot_provider_cfg["iot_client_key_path"]
        self.iot_client_cert_path = iot_provider_cfg["iot_client_cert_path"]
        self.subscribe_topic = iot_provider_cfg["subscribe_topic"]

    def onmsg(self, msg_payload):
        # Core event handler for incoming messages
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
    """
    Child class containing implementations of IotProvider specific to Amazon Web Services.
    """

    def onmsg(self, msg):
        # Wraps core event handler for incoming messages
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

    def disconnect(self):
        self.aws_iot_mqtt_comm.disconnect()

    def publish(self, publish_topic, msg_str, qos):
        self.aws_iot_mqtt_comm.publish(publish_topic, msg_str, QoS=qos)



class MosQuiTTo(IotProvider):
    """
    Child class containing implementations of IotProvider specific to MosQuiTTo.
    """

    def __init__(self, iot_provider_cfg):
        # 1. Set tls_version to correspond to mosquitto broker.
        # 2. Call parent class' __init__
        self.tls_version = eval(f"ssl.PROTOCOL_TLSv1_{iot_provider_cfg['tls_version']}")
        super().__init__(iot_provider_cfg)

    def on_connect(self, client, userdata, flags, rc):
        # Event handler for connection event. Subscribe to topic(s) here.
        client.subscribe(self.subscribe_topic, qos=0)
        
    def onmsg(self, client, userdata, msg):
        # Wraps core event handler for incoming messages
        msg_payload = msg.payload
        super().onmsg(msg_payload)

    def connect(self):
        # A connection to iot is established at the beginning and if publish fails
        self.mosquitto_comm = Client()
        self.mosquitto_comm.on_connect = self.on_connect
        self.mosquitto_comm.on_message = self.onmsg
        self.mosquitto_comm.tls_set(self.iot_ca_cert_path, self.iot_client_cert_path, self.iot_client_key_path, tls_version=self.tls_version, cert_reqs=ssl.CERT_REQUIRED)
        self.mosquitto_comm.connect(self.iot_broker, self.iot_port)
        self.mosquitto_comm.loop_start()

    def disconnect(self):
        self.mosquitto_comm.disconnect()

    def publish(self, publish_topic, msg_str, qos):
        self.mosquitto_comm.publish(publish_topic, msg_str, qos=qos)



class AzureIoT(IotProvider):
    def __init__(self, iot_provider_cfg):
        # 1. Set device_name.
        # 2. Set tls_version.
        # 3. Set MQTT Protocol version
        # 4. Call parent class' __init__
        self.device_name = iot_provider_cfg["device_name"]
        self.tls_version = eval(f"ssl.PROTOCOL_TLSv1_{iot_provider_cfg['tls_version']}")
        self.mqtt_version = eval(f"mqtt.MQTTv{iot_provider_cfg['mqtt_version']}")
        super().__init__(iot_provider_cfg)

    def on_connect(self, client, userdata, flags, rc):
        # Event handler for connection event. Subscribe to topic(s) here.
        client.subscribe(self.subscribe_topic, qos=0)
        
    def on_disconnect(client, userdata, rc):
        print(f"Disconnected with code {rc}")

    def onmsg(self, client, userdata, msg):
        # Wraps core event handler for incoming messages
        msg_payload = msg.payload
        super().onmsg(msg_payload)

    def connect(self):
        # A connection to iot is established at the beginning and if publish fails
        self.azure_iot_comm = Client(client_id = self.device_name, protocol = self.mqtt_version)
        self.azure_iot_comm.on_connect = self.on_connect
        self.azure_iot_comm.on_disconnect = self.on_disconnect
        self.azure_iot_comm.on_message = self.onmsg
        self.azure_iot_comm.username_pw_set(username = f"{self.iot_broker}/{self.device_name}")
        self.azure_iot_comm.tls_set(self.iot_ca_cert_path, self.iot_client_cert_path, self.iot_client_key_path, tls_version=self.tls_version, cert_reqs=ssl.CERT_REQUIRED)
        self.azure_iot_comm.connect(self.iot_broker, self.iot_port)
        self.azure_iot_comm.loop_start()

    def disconnect(self):
        self.azure_iot_comm.disconnect()

    def publish(self, publish_topic, msg_str, qos):
        # Overriding qos to 0 because Azure doesn't seem to like any other qos
        self.azure_iot_comm.publish(publish_topic, msg_str, qos=0)



class ClearBladeIot(IotProvider):
    """
    Child class containing implementations of IotProvider specific to CleaBlade.
    """

    def __init__(self, iot_provider_cfg):
        # 1. Load path to ClearBlade-specific module from config and add to path.
        # 2. Import ClearBlade-specific module.
        # 3. Load system_key and system_secret from config.
        # 4. Create "System" object.
        # 5. Call parent class' __init__
        sys.path.append(iot_provider_cfg["module_dir"])
        from clearblade.ClearBladeCore import System as ClearBladeSystem
        self.ClearBladeSystem = ClearBladeSystem(iot_provider_cfg["system_key"], iot_provider_cfg["system_secret"])
        super().__init__(iot_provider_cfg)

    def on_connect(self, client, userdata, flags, rc):
        # Event handler for connection event. Subscribe to topic(s) here.
        client.subscribe(self.subscribe_topic)
        print(f"subscribed to {self.subscribe_topic}")

    def onmsg(self, client, userdata, msg):
        # Wraps core event handler for incoming messages
        msg_payload = msg.payload
        super().onmsg(msg_payload)

    def connect(self):
        # A connection to iot is established at the beginning and if publish fails.
        # 1. Create AnonUser.
        # 2. Create Messaging object with AnonUser as param.
        # 3. Pass on_connect function.
        # 4. Pass onmsg function.
        # 5. Call Messaging object's "connect" method.
        self.clearblade_iot_user = self.ClearBladeSystem.AnonUser()
        self.clearblade_iot_comm = self.ClearBladeSystem.Messaging(self.clearblade_iot_user, client_id="xqtive")
        self.clearblade_iot_comm.on_connect = self.on_connect
        self.clearblade_iot_comm.on_message = self.onmsg
        self.clearblade_iot_comm.connect()

    def publish(self, publish_topic, msg_str, qos):
        self.clearblade_iot_comm.publish(publish_topic, msg_str, qos=qos)



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
    """
    Return list of sequence files' names found in sequences_dir.
    """
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


def iot_rw(obj):
    """
    Function that runs within the process dedicated to communicating with an IoT Provider.
    """

    # Retrieve params passed in through obj
    global sm_name    # sm_name needed by functions defined outside of this function.
    sm_name = obj.get("sm_name")
    certs_dir = obj.get("certs_dir")
    iot_provider = obj.get("iot_provider")
    global states_queue    # states_queue needed by functions defined outside of this function.
    all_sm_queues = obj.get("all_sm_queues")
    this_sm_queues = all_sm_queues[sm_name]
    states_queue = this_sm_queues["states_queue"]
    iot_rw_queues = this_sm_queues["iot_rw_queues"]
    global config    # config needed by functions defined outside of this function.
    config = obj.get("config")
    process_name = f"{sm_name}_iot_rw"
    global iot_rw_logger    # iot_rw_logger needed by functions defined outside of this function.

    # Create logger
    iot_rw_logger = create_logger(process_name, config)

    # Configure connection to IoT provider
    try:
        iot_broker = config[iot_provider].get("broker_address")
        iot_port = config[iot_provider].get("broker_port")
        subscribe_topic = f"{config[iot_provider]['subscribe_topic_prefix']}/{sm_name}"
        publish_topic = config[iot_provider]["publish_topic"]
        iot_ca_cert_path = f"{certs_dir}/{config[iot_provider].get('ca_cert')}"
        iot_client_cert_path = f"{certs_dir}/{config[iot_provider].get('client_cert')}"
        iot_client_key_path = f"{certs_dir}/{config[iot_provider].get('client_key')}"
    except Exception as e:
        iot_rw_logger.error(f"ERROR; Init of {process_name}; {type(e).__name__}; {e}")

    # iot_rw_queues is a dict with a queue reference for each IoT Provider used by this application
    iot_rw_queue = iot_rw_queues[iot_provider]

    # Create specific IotProvider object for THIS process
    iot_provider_cfg = {
        "sm_name": sm_name,
        "iot_broker": iot_broker,
        "iot_port": iot_port,
        "iot_ca_cert_path": iot_ca_cert_path,
        "iot_client_key_path": iot_client_key_path,
        "iot_client_cert_path": iot_client_cert_path,
        "subscribe_topic": subscribe_topic,
        "tls_version": config[iot_provider].get("tls_version"),
        "mqtt_version": config[iot_provider].get("mqtt_version"),
        "device_name": config[iot_provider].get("device_name"),
        "module_dir": config[iot_provider].get("module_dir"),
        "system_key": config[iot_provider].get("system_key"),
        "system_secret": config[iot_provider].get("system_secret")}
    if iot_provider == "aws_iot_mqtt":
        iot_comm = AwsIotMqtt(iot_provider_cfg)
    elif iot_provider == "azure_iot":
        iot_comm = AzureIoT(iot_provider_cfg)
    elif iot_provider == "mosquitto":
        iot_comm = MosQuiTTo(iot_provider_cfg)
    elif iot_provider == "clearblade_iot":
        iot_comm = ClearBladeIot(iot_provider_cfg)

    iot_connected = False
    while True:
        try:
            if not iot_connected:
                try:
                    iot_comm.connect()
                    logging.warning(f"Connected to {iot_provider}: {iot_comm}")
                    iot_connected = True
                except Exception as e:
                    # If there was an error during connection close and wait before trying again
                    iot_comm.disconnect()
                    iot_rw_logger.error(f"ERROR; Attempted to connect; main loop of {process_name}; {type(e).__name__}; {e}; reconnecting...")
                    time.sleep(config[iot_provider]["wait_between_reconn_attempts"])
            else:
                dequeued = iot_rw_queue.get()
                if dequeued == "SHUTDOWN":
                    iot_comm.disconnect()
                    logging.warning(f"Disconnected from {iot_provider}.")
                    break
                else:
                    msg_dict = dequeued
                    msg_str = json.dumps(msg_dict)
                    try:
                        iot_comm.publish(publish_topic, msg_str, 1)
                    except Exception as e:
                        # If there was an error during connection close and wait before trying again
                        iot_comm.disconnect()
                        iot_rw_logger.error(f"ERROR; Attempted to publish {msg_str} to {publish_topic}; main loop of {process_name}; {type(e).__name__}; {e}; reconnecting...")
                        time.sleep(config[iot_provider]["wait_between_reconn_attempts"])
        except Exception as e:
            iot_rw_logger.error(f"ERROR; main loop of {process_name}; {type(e).__name__}; {e}")


def create_logger(logger_name, config):
    """
    Create logger dedicated to this process
    """
    logging.basicConfig(filename=f"/var/log/{logger_name}.log", format="%(asctime)s %(message)s", level=config["log_level"])
    logger = logging.getLogger(logger_name)
    return logger


def launch_state_machines(sm_defs, config, certs_dir):
    """
    Launch all processes pertinent to all state machines. This includes creating the state machine objects and all
    queues that the various processes will receive messages on.  Also includes launching all processes for IoT Providers that
    these state machines talk to.
    """

    # Create all queues
    all_sm_queues = {}
    for sm_def in sm_defs:
        sm_name = sm_def["sm_name"]
        iot_providers = sm_def.get("iot_providers")
        sm_queues = create_sm_queues(config, iot_providers)
        all_sm_queues[sm_name] = sm_queues

    # Create all state machine objects
    all_sm = {}
    for sm_def in sm_defs:
        sm_name = sm_def["sm_name"]
        sm_class = sm_def["sm_class"]
        sm = create_sm(config, sm_def, all_sm_queues)
        all_sm[sm_name] = sm

    # Launch all processes
    all_sm_processes = []
    for sm_def in sm_defs:
        sm_name = sm_def["sm_name"]
        iot_providers = sm_def.get("iot_providers")
        sm = all_sm[sm_name]
        sm_processes = launch_sm_processes(sm_name, sm, iot_providers, all_sm_queues, config, certs_dir)
        all_sm_processes += sm_processes
    to_return = {"all_sm_queues": all_sm_queues, "all_sm": all_sm, "all_sm_processes": all_sm_processes}
    return to_return


def create_sm_queues(config, iot_providers):
    """
    Create the managed PriorityQueues that will carry states and parameters for all state machines
    """
    states_queue = xqtive.XQtiveQueue(config)

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
    """
    Create a State Machine object and return it
    """
    sm_name = sm_def["sm_name"]
    sm_class = sm_def["sm_class"]
    sm = sm_class(sm_name, config, all_sm_queues)
    return sm


def launch_sm_processes(sm_name, sm, iot_providers, all_sm_queues, config, certs_dir):
    """
    Launch all processes
    """

    launched_processes = []
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
