% Write a trapezoid of delay -10 us with MATLAB Pulseq, and print the [TRAP] section.
sys = mr.opts();
seq = mr.Sequence(sys);
g = mr.makeTrapezoid('x', 'amplitude', 100000, 'riseTime', 100e-6, ...
                     'flatTime', 200e-6, 'delay', -10e-6, 'system', sys);
seq.addBlock(g, mr.makeDelay(500e-6));
out = [tempname() '.seq'];
seq.write(out);
text = fileread(out);
delete(out);
k = strfind(text, '[TRAP]');
e = strfind(text(k:end), sprintf('\n\n'));
disp(text(k:k + e(1) - 2));
