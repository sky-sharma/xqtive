import { Button } from '@material-ui/core';

const EStopButton = (props) => {
    const onEStopClick = () => {
        props.onEStopClick('run_state', 'E_STOP')
    };

    return (
        <Button
            variant="contained"
            color="primary"
            size="large"
            style={{ width: 300 }}
            onClick={onEStopClick}>
                E-Stop
        </Button>
    )
};

export default EStopButton;