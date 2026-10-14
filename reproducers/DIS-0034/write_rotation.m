% Writes rotation_extension.seq and rotation_explicit.seq with MATLAB Pulseq
% (pulseq/pulseq c7469123). One block: a triangle gradient on x (0 -> 1e5 Hz/m
% -> 0 in 100 us) and an ADC of 10 samples of 10 us, rotated by 30 degrees
% about z: with the rotation extension, and with mr.rotate3D (no extension).
sys = mr.opts('adcDeadTime', 0, 'rfDeadTime', 0, 'rfRingdownTime', 0, ...
              'maxGrad', 1e6, 'maxSlew', 1e12, 'gradUnit', 'Hz/m', 'slewUnit', 'Hz/m/s');
g = mr.makeExtendedTrapezoid('x', 'times', [0 50e-6 100e-6], 'amplitudes', [0 1e5 0], 'system', sys);
adc = mr.makeAdc(10, 'Dwell', 10e-6, 'system', sys);
rot = mr.makeRotation(pi/6);   % rotQuaternion = [0.9659 0 0 0.2588]
seq = mr.Sequence(sys);
seq.addBlock(g, adc, rot);
seq.write('rotation_extension.seq');
seq = mr.Sequence(sys);
c = mr.rotate3D(rot.rotQuaternion, g, adc, 'system', sys);
seq.addBlock(c{:});
seq.write('rotation_explicit.seq');
