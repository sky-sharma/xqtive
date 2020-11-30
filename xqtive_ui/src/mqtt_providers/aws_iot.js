import Amplify from 'aws-amplify';
import PubSub, { AWSIoTProvider } from '@aws-amplify/pubsub';

const mqttConnectSubscribe = (subscribeTopic, incomingMsgHandler) => {
    Amplify.configure({
        Auth: {
            identityPoolId: 'us-east-2:d5279c86-de14-4b86-9525-40c8d5ab4cb0',
            region: 'us-east-2',
        },
    });

    Amplify.addPluggable(new AWSIoTProvider({
        aws_pubsub_region: 'us-east-2',
        aws_pubsub_endpoint: 'wss://a3nhp0s4taaayb-ats.iot.us-east-2.amazonaws.com/mqtt'
    }));

    PubSub.subscribe(subscribeTopic).subscribe({
        next: data => incomingMsgHandler(data.value),
        error: error => console.error(error),
        close: () => console.log('Done'),
    });
};

const mqttPublish = (sendTopic, msgToSend) => {
    PubSub.publish(sendTopic, msgToSend);
}

export { mqttConnectSubscribe, mqttPublish }; 