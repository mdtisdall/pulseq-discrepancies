"""add_block stores an RF event of use='other' as undefined ('u'); write writes 'u'."""
import os
import tempfile

import numpy as np
import pypulseq as pp

system = pp.Opts()
rf = pp.make_block_pulse(np.pi / 2, duration=1e-3, use='other', system=system)
print('event use:', rf.use)
seq = pp.Sequence(system)
seq.add_block(rf)
print('get_block use:', seq.get_block(1).rf.use, '(expected: other)')
with tempfile.TemporaryDirectory() as folder:
    out = os.path.join(folder, 'out.seq')
    seq.write(out)
    text = open(out).read()
    read_back = pp.Sequence(system)
    read_back.read(out)
print(text[text.index('[RF]') :].split('\n\n', 1)[0])
print('after write and read:', read_back.get_block(1).rf.use, '(expected: other)')
