import { TextField } from '@material-ui/core';
import { Autocomplete } from '@material-ui/lab';

const SequenceSelector = (props) => {
    return (
        <Autocomplete
          id="sequences"
          options={props.sequences}
          getOptionLabel={(option) => option}
          style={{ width: 300 }}
          renderInput={(params) => <TextField {...params} label="Sequences..." variant="outlined" />}
          onChange={event => props.onSeqSelection(event.target.textContent)}
        />
      );
};

export default SequenceSelector;