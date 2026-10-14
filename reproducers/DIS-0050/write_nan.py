"""The same events with pypulseq: make_trapezoid and make_block_pulse with NaN, then write."""
import os
import tempfile
import traceback

import numpy as np
import pypulseq as pp

system = pp.Opts()
for name, make in [
    ('trapezoid of amplitude NaN', lambda: pp.make_trapezoid('x', amplitude=np.nan, rise_time=100e-6, flat_time=200e-6, system=system)),
    ('block pulse of freq_offset NaN', lambda: pp.make_block_pulse(np.pi / 2, duration=1e-3, freq_offset=np.nan, use='excitation', system=system)),
]:
    seq = pp.Sequence(system)
    try:
        seq.add_block(make())
        with tempfile.TemporaryDirectory() as folder:
            seq.write(os.path.join(folder, 'out.seq'))
        print(name + ': written')
    except Exception as e:
        frame = traceback.extract_tb(e.__traceback__)[-1]
        print(f'{name}: {type(e).__name__}: {e} ({os.path.basename(frame.filename)}:{frame.lineno})')
