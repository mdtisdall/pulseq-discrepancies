"""Read definitions_number.seq with pypulseq, write it again, and print the definitions that were written."""
import os
import tempfile

import pypulseq as pp

src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'definitions_number.seq')
seq = pp.Sequence()
seq.read(src)
with tempfile.TemporaryDirectory() as folder:
    out = os.path.join(folder, 'out.seq')
    seq.write(out)
    lines = open(out).read().split('[DEFINITIONS]\n', 1)[1].split('\n\n', 1)[0]
print(lines)
