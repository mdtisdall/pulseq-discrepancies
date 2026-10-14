"""Builds a sequence with Sequence.set_block at the block IDs 1, 3, 2, in that
order, writes it with Sequence.write to set_block_out_of_order.seq (in the
current folder), and prints the [BLOCKS] section of the file."""
import warnings

import pypulseq as pp

warnings.simplefilter('ignore')
system = pp.Opts()
seq = pp.Sequence(system)
seq.set_block(1, pp.make_block_pulse(flip_angle=0.1, duration=1e-4, system=system))
seq.set_block(3, pp.make_trapezoid(channel='z', area=10, duration=1.2e-4, system=system))
seq.set_block(2, pp.make_adc(num_samples=10, duration=1e-4, system=system))
print('block_events keys:', list(seq.block_events))
seq.write('set_block_out_of_order.seq')
lines = open('set_block_out_of_order.seq').read().split('[BLOCKS]\n')[1].split('\n\n')[0]
print('[BLOCKS]\n' + lines)
