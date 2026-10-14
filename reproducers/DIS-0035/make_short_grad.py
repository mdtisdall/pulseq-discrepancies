"""Writes pypulseq_short_grad.seq: an arbitrary gradient of 3 samples on the
default raster. pypulseq writes it with a time shape 0.5 1.5 2.5."""
import numpy as np
import pypulseq as pp

system = pp.Opts()
seq = pp.Sequence(system)
g = pp.make_arbitrary_grad(channel='x', waveform=np.array([1000.0, 2000.0, 1000.0]), system=system)
seq.add_block(g)
seq.write('pypulseq_short_grad.seq')
