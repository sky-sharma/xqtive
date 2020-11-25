import { Button } from '@material-ui/core';

const ClearDisplayButton = (props) => {
    
    return (
        <Button
            variant="contained"
            color="primary"
            size="large"
            style={{ width: 450 }}
            disabled={!(props.display)}
            onClick={props.onClearDispClick}>
                Clear Display
        </Button>
    )
};

export default ClearDisplayButton;