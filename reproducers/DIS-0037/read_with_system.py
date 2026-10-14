"""Reads v131_rf_adc_grad.seq and v151_rf_adc_grad.seq (in the current folder)
with three systems, and prints the block durations, the times of the gradient
and the ADC samples (waveforms_and_times) and check_timing."""
import contextlib
import io
import warnings

import numpy as np
import pypulseq as pp

warnings.simplefilter('ignore')
systems = {
    'default': pp.Opts(),
    'deadtimes': pp.Opts(rf_dead_time=100e-6, rf_ringdown_time=20e-6, adc_dead_time=10e-6),
    'grad5us': pp.Opts(grad_raster_time=5e-6),
}
for f in ['v131_rf_adc_grad.seq', 'v151_rf_adc_grad.seq']:
    for name, system in systems.items():
        seq = pp.Sequence(system)
        seq.read(f)
        print(f, name, 'block durations (us)', [round(seq.block_durations[k] * 1e9) / 1e3 for k in seq.block_events])
        wave, _, _, t_adc, _ = seq.waveforms_and_times(append_RF=True)
        print('  gx times (us)', np.round(wave[0][0] * 1e9) / 1e3)
        print('  ADC samples (us)', round(t_adc[0] * 1e7) / 10, 'to', round(t_adc[-1] * 1e7) / 10)
        with contextlib.redirect_stdout(io.StringIO()):
            ok, report = seq.check_timing()
        print('  check_timing ok', ok, [r.error_type for r in report])
