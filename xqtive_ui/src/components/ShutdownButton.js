import { Button } from '@material-ui/core';

const ShutdownButton = (props) => {
    const onShutdownClick = () => {
        props.onShutdownClick('run_state', 'SHUTDOWN')
    };

    return (
        <Button
            variant="contained"
            color="secondary"
            size="large"
            style={{ width: 300 }}
            onClick={onShutdownClick}>
                SHUTDOWN
        </Button>
    )
};

export default ShutdownButton;