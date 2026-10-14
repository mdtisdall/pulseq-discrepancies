% Write a trapezoid of amplitude NaN, and a block pulse of frequency offset NaN,
% with MATLAB Pulseq, and print the [TRAP] and [RF] sections that are written.
sys = mr.opts();
seq = mr.Sequence(sys);
g = mr.makeTrapezoid('x', 'amplitude', NaN, 'riseTime', 100e-6, 'flatTime', 200e-6, 'system', sys);
seq.addBlock(g);
rf = mr.makeBlockPulse(pi/2, 'duration', 1e-3, 'freqOffset', NaN, 'use', 'excitation', 'system', sys);
seq.addBlock(rf);
out = [tempname() '.seq'];
seq.write(out);
text = fileread(out);
delete(out);
for name = {'[RF]', '[TRAP]'}
  k = strfind(text, name{1});
  e = strfind(text(k:end), sprintf('\n\n'));
  disp(text(k:k + e(1) - 2));
end
