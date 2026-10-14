% Writes adc_phase_modulation.seq with MATLAB Pulseq (pulseq/pulseq c7469123).
% One block: a triangle gradient on x (0 -> 1e5 Hz/m -> 0 in 100 us) and an
% ADC of 10 samples of 10 us whose phase modulation is (0:9)*pi/4, in rad as
% MATLAB Pulseq uses it.
sys = mr.opts('adcDeadTime', 0, 'rfDeadTime', 0, 'rfRingdownTime', 0, ...
              'maxGrad', 1e6, 'maxSlew', 1e12, 'gradUnit', 'Hz/m', 'slewUnit', 'Hz/m/s');
g = mr.makeExtendedTrapezoid('x', 'times', [0 50e-6 100e-6], 'amplitudes', [0 1e5 0], 'system', sys);
adc = mr.makeAdc(10, 'Dwell', 10e-6, 'phaseModulation', (0:9)*pi/4, 'system', sys);
seq = mr.Sequence(sys);
seq.addBlock(g, adc);
seq.write('adc_phase_modulation.seq');
