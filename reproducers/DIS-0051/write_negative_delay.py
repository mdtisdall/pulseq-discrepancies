"""Write a trapezoid of delay -10 us with pypulseq, and print the [TRAP] section."""
import os
import tempfile

import pypulseq as pp

system = pp.Opts()
seq = pp.Sequence(system)
g = pp.make_trapezoid('x', amplitude=100000, rise_time=100e-6, flat_time=200e-6, delay=-10e-6, system=system)
seq.add_block(g, pp.make_delay(500e-6))
with tempfile.TemporaryDirectory() as folder:
    out = os.path.join(folder, 'out.seq')
    seq.write(out)
    text = open(out).read()
print(text[text.index('[TRAP]') :].split('\n\n', 1)[0])
