% Read definitions_number.seq with MATLAB Pulseq, write it again, and print the
% definitions that were written.
src = fullfile(fileparts(mfilename('fullpath')), 'definitions_number.seq');
seq = mr.Sequence();
seq.read(src);
out = [tempname() '.seq'];
seq.write(out);
text = fileread(out);
delete(out);
k = strfind(text, '[DEFINITIONS]');
e = strfind(text(k:end), sprintf('\n\n'));
disp(text(k:k + e(1) - 2));
