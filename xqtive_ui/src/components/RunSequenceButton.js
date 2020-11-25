import { Button } from '@material-ui/core';

const RunSequenceButton = (props) => {
    const onRunSeqClick = () => {
        console.log("onRunSeqClick", props.selectedSeq);
        props.onRunSeqClick('run_sequence', props.selectedSeq)
    };

    return (
        <Button
            variant="contained"
            color="primary"
            size="large"
            style={{ width: 300 }}
            disabled={!(props.selectedSeq)}
            onClick={onRunSeqClick}>
                Run Sequence
        </Button>
    )
};

export default RunSequenceButton;