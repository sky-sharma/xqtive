import json
import time
import logging
import xqtive
from queue import Queue
from multiprocessing import Process
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT

def read_config(config_filepath):
    with open(config_filepath) as cfgFile:
        config = json.load(cfgFile)
    return(config)

def iot_onmsg(msg):
    msg_payload = msg.payload
    dict_payload = json.loads(msg_payload)
    msg = dict_payload["message"]
    print(msg)
    msg_array = msg.split(";")

    # Capitalize state: all states called from the outside have to be public.
    # Public states are indicated by being named all upper case
    msg_arr_with_cap_state = [msg_array[0].upper()] + msg_array[1:]
    states_queue.put(msg_arr_with_cap_state)

def iot_rw(obj):
    certs_dir = obj["certs_dir"]
    global states_queue
    states_queue = obj["states_queue"]
    iot_rw_queue = obj["iot_rw_queue"]
    config = obj["config"]
    # Configure connection to IoT broker
    iot_broker = config["iot"]["broker_address"]
    iot_port = config["iot"]["broker_port"]
    subscribe_topic = config["iot"]["subscribe_topic"]
    publish_topic = config["iot"]["publish_topic"]
    iot_ca_cert_path = f"{certs_dir}/{config['iot']['ca_cert']}"
    iot_client_cert_path = f"{certs_dir}/{config['iot']['client_cert']}"
    iot_client_key_path = f"{certs_dir}/{config['iot']['client_key']}"

    iot_connected = False
    while True:
        if not iot_connected:
            try:
                # A connection to iot is established at the beginning and if publish fails
                iot_comm = AWSIoTMQTTClient("xqtive")
                iot_comm.onMessage = iot_onmsg
                iot_comm.configureEndpoint(iot_broker, iot_port)
                iot_comm.configureCredentials(iot_ca_cert_path, iot_client_key_path, iot_client_cert_path)
                iot_comm.connect()
                iot_comm.subscribe(subscribe_topic, 1, None)
                iot_connected = True
            except Exception as e:
                # If there was an error during connection close and wait before trying again
                iot_comm.close()
                time.sleep(config["iot"]["wait_between_reconn_attempts"])
        else:
            dequeued = iot_rw_queue.get()
            if dequeued == "SHUTDOWN":
                break
            else:
                msg_dict = {"message": dequeued}
                msg_str = json.dumps(msg_dict)
                iot_comm.publish(publish_topic, msg_str, QoS=0)


def iot_close(iot_comm):
    iot_comm.disconnect()

def create_logger(logger_name, config):
    logging.basicConfig(filename=f"/var/log/{logger_name}.log", format="%(asctime)s %(message)s", level=config["log_level"])
    logger = logging.getLogger(logger_name)
    return logger

def launch_state_machine(state_machine_class, config, certs_dir):
    state_machine = state_machine_class(config)
    launched_processes = []
    # Create managed PriorityQueue for states
    states_queue = xqtive.XqtiveQueue(state_machine.priority_values, state_machine.hi_priorities)

    xqtive.XqtiveSyncMgr.register("Queue", Queue)
    iot_rw_queue_mgr = xqtive.XqtiveSyncMgr()
    iot_rw_queue_mgr.start()
    iot_rw_queue = iot_rw_queue_mgr.Queue()

    iot_rw_cfg = {
        "certs_dir": certs_dir,
        "states_queue": states_queue,
        "iot_rw_queue": iot_rw_queue,
        "config": config}
    iot_rw_process = Process(target = iot_rw, args = [iot_rw_cfg])
    iot_rw_process.start()
    launched_processes.append(iot_rw_process)

    state_machine_cfg = {
        "state_machine": state_machine,
        "config": config,
        "states_queue": states_queue,
        "iot_rw_queue": iot_rw_queue}
    state_machine_process = Process(target = xqtive.xqtive_state_machine, args = [state_machine_cfg])
    state_machine_process.start()
    launched_processes.append(state_machine_process)
    processes_and_queues = {
        "processes": launched_processes,
        "states_queue": states_queue,
        "iot_rw_queue": iot_rw_queue}
    return processes_and_queues
