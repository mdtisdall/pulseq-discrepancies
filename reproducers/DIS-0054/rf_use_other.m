% The same RF pulse of use 'other' with MATLAB Pulseq: write writes 'o'.
sys = mr.opts();
rf = mr.makeBlockPulse(pi/2, 'duration', 1e-3, 'use', 'other', 'system', sys);
seq = mr.Sequence(sys);
seq.addBlock(rf);
out = [tempname() '.seq'];
seq.write(out);
text = fileread(out);
seq2 = mr.Sequence(sys);
seq2.read(out);
delete(out);
k = strfind(text, '[RF]');
e = strfind(text(k:end), sprintf('\n\n'));
disp(text(k:k + e(1) - 2));
b = seq2.getBlock(1);
fprintf('after write and read: %s\n', b.rf.use);
