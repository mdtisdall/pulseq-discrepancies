"""Makes an oversampled arbitrary gradient (make_arbitrary_grad with
oversampling=True) and writes it with Sequence.write(..., v141_compat=True),
first with remove_duplicates=False, then with the default
remove_duplicates=True, to write_v141_oversampled.seq (in the current folder).
Prints the [VERSION] and [GRADIENTS] sections of the file, or the error."""
import traceback
import warnings

import numpy as np
import pypulseq as pp

warnings.simplefilter('ignore')
system = pp.Opts()
wave = 1e5 * np.array([0, 0.25, 0.5, 0.75, 1, 0.75, 0.5, 0.25, 0])
for remove in [False, True]:
    seq = pp.Sequence(system)
    gz = pp.make_arbitrary_grad(channel='z', waveform=wave, oversampling=True, system=system)
    seq.add_block(gz)
    try:
        seq.write('write_v141_oversampled.seq', v141_compat=True, remove_duplicates=remove)
        text = open('write_v141_oversampled.seq').read()
        print(f'remove_duplicates={remove}: ok')
        for sec in ['[VERSION]', '[GRADIENTS]']:
            print(sec + '\n' + text.split(sec + '\n')[1].split('\n\n')[0])
    except Exception:
        print(f'remove_duplicates={remove}: ' + traceback.format_exc(limit=-1).strip().splitlines()[-1])
        print('  at ' + traceback.format_exc().strip().splitlines()[-3].strip())
