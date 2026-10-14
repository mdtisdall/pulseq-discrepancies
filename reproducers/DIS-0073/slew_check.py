"""make_arbitrary_grad(oversampling=True) with every segment at 350 % of max_slew.

From draft P01 of mdtisdall/pypulseq-issues. pypulseq 1.5.0.post1 accepts the
350 % gradient; master (c977214) and MATLAB Pulseq's makeArbitraryGrad reject it.
"""

import numpy as np
import pypulseq as pp

system = pp.Opts(max_slew=100, slew_unit='T/m/s')
dt = system.grad_raster_time  # 10 us

# A sample every dt/2; each segment rises or falls by 3.5 * max_slew * dt/2.
step = 3.5 * system.max_slew * dt / 2
waveform = step * np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 2, 1])

try:
    pp.make_arbitrary_grad('x', waveform, first=0, last=0, oversampling=True, system=system)
    print('350 %: accepted')
except ValueError as err:
    print(f'350 %: {err}')
