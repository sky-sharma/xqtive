const FeedbackDisplay = (props) => {
    return (
        <div>
            <u><b>Feedback Display:</b></u>
            <div
                style={{
                    height: 800,
                    overflowY: 'scroll',
                    whiteSpace: 'pre-wrap',
                    maxWidth: 450 }}>
                {props.display}
            </div>
            <br />
        </div>
    )
};

export default FeedbackDisplay;