"""Writes pypulseq_raster_2p5us.seq: an extended trapezoid with its vertices on
a gradient raster of 2.5 us (0, 2.5, 7.5 and 10 us)."""
import numpy as np
import pypulseq as pp

system = pp.Opts(grad_raster_time=2.5e-6, block_duration_raster=10e-6)
seq = pp.Sequence(system)
g = pp.make_extended_trapezoid(
    channel='x',
    times=np.array([0, 2.5, 7.5, 10]) * 1e-6,
    amplitudes=np.array([0.0, 1000.0, 1000.0, 0.0]),
    system=system,
)
seq.add_block(g)
seq.write('pypulseq_raster_2p5us.seq')
