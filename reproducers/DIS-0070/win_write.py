"""Write a one-block sequence with pypulseq as it writes on Windows.

On Windows, a file opened in text mode with no `newline` argument has each
'\n' written as '\r\n' (os.linesep). This script gives `write_seq` an `open`
that does the same on any system, then writes the sequence.

Usage: python -I win_write.py OUT.seq
"""

import builtins
import importlib
import sys
import warnings

import pypulseq as pp

write_seq = importlib.import_module('pypulseq.Sequence.write_seq')
real_open = builtins.open


def windows_open(file, mode='r', *args, **kwargs):
    if 'b' not in mode and 'newline' not in kwargs and len(args) < 3 and any(c in mode for c in 'wa'):
        kwargs['newline'] = '\r\n'
    return real_open(file, mode, *args, **kwargs)


write_seq.open = windows_open  # write_seq calls open by its global name
warnings.simplefilter('ignore')
seq = pp.Sequence()
seq.add_block(pp.make_block_pulse(flip_angle=0.1, duration=1e-4, system=seq.system))
seq.write(sys.argv[1])
