import Amplify from 'aws-amplify';
import PubSub, { AWSIoTProvider } from '@aws-amplify/pubsub';

const mqttConnectSubscribe = (subscribeTopic, incomingMsgHandler) => {
    Amplify.configure({
        Auth: {
          identityPoolId: '<Your Cognito Identity Pool ID>',
          region: 'us-east-2',
        },
    });
    
    Amplify.addPluggable(new AWSIoTProvider({
        aws_pubsub_region: 'us-east-2',
        aws_pubsub_endpoint: 'wss://a3nhp0s4taaayb-ats.iot.us-east-2.amazonaws.com/mqtt'
    }));
    
    PubSub.subscribe(subscribeTopic).subscribe({
        next: data => incomingMsgHandler(data),
        error: error => console.error(error),
        close: () => console.log('Done'),
    });  
};

const mqttPublish = (sendTopic, msgToSend) => {
    PubSub.publish(sendTopic, msgToSend);
}

export { mqttConnectSubscribe, mqttPublish }; 