import mqtt from 'mqtt';

var mqttClient;

const mqttConnectSubscribe = (subscribeTopic, incomingMsgHandler) => {
    const options = {
        protocol: 'mqtt',
        clientId: 'xqtive_ui'
    };
    mqttClient = mqtt.connect('wss://akash-5510-elementary.local:9001', options);
    mqttClient.on('connect', () => {
        mqttClient.subscribe(subscribeTopic, (err) => {
            if (err) {
                console.log(err);
            };
        });
    });
    mqttClient.on("message", (topic, message) => {
        const msgJson = JSON.parse(message.toString());
        incomingMsgHandler(msgJson);
    });
};

const mqttPublish = (sendTopic, msgToSend) => {
    const msgToSendStr = JSON.stringify(msgToSend);
    mqttClient.publish(sendTopic, msgToSendStr);
}

export { mqttConnectSubscribe, mqttPublish };