import { useState, useEffect } from 'react';
import SequenceSelector from '../components/SequenceSelector';
import RunSequenceButton from '../components/RunSequenceButton';
import EStopButton from '../components/EStopButton';
import ShutdownButton from '../components/ShutdownButton';
import FeedbackDisplay from './FeedbackDisplay';
import ClearDisplayButton from '../components/ClearDisplayButton';
import { mqttConnectSubscribe, mqttPublish } from '../mqtt_providers/aws_iot';

const App = () => {
    const [sequences, setSequences] = useState([]);
    const [selectedSeq, setSelectedSeq] = useState(null);
    const [display, setDisplay] = useState('');
    
    const rcvMsgFromXqtiveController = (data) => {
        console.log("rcvMsgFromXqtiveController!", data);
        const msg = data.value;
        const msg_sender = msg.sender;
        const msg_type = msg.msg_type;
        const msg_val = msg.value;
        switch (msg_type) {
            case 'sequence_names':
                // Set sequences to array of sequence names without .seq extensions
                setSequences(msg_val.map(seq => { return (seq.split('.seq')[0]) }));
                break;
            default:
                setDisplay(display =>`From ${msg_sender}; ${msg_type}: ${msg_val}\n\n${display}`);
        };
    };
    
    const sendMsgToXqtiveController = (msg_type, value) => {
        const msgToSend = { msg_type, value };
        console.log("sendMsgToXqtiveController!", msgToSend);
        mqttPublish('xqtive/controller', msgToSend)
    };

    const onSeqSelection = (seqSelection) => {
        console.log("selectSequence: ", seqSelection);
        setSelectedSeq(seqSelection);
    };

    const onClearDispClick = () => {
        console.log("onClearDispClick");
        setDisplay('');
    };

    useEffect(() => {
        console.log("In useEffect.");
        mqttConnectSubscribe('xqtive/feedback', rcvMsgFromXqtiveController)
    },[]);

    return (
        <div
            className="ui container"
            style={{ padding: 20 }} >
            <div className="ui grid">
                <div className="ui row">
                    <div className="eleven wide column">
                        <FeedbackDisplay display={display}/>
                        <ClearDisplayButton display={display} onClearDispClick={onClearDispClick}/>
                    </div>
                    <div className="five wide column">
                        <SequenceSelector sequences={sequences} onSeqSelection={onSeqSelection}/>
                        <br />
                        <RunSequenceButton selectedSeq={selectedSeq} onRunSeqClick={sendMsgToXqtiveController} />
                        <br />
                        <br />
                        <EStopButton onEStopClick={sendMsgToXqtiveController} />
                        <br />
                        <br />
                        <br />
                        <br />
                        <ShutdownButton onShutdownClick={sendMsgToXqtiveController} />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default App;