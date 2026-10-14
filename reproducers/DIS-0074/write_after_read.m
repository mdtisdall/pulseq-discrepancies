% Reads v131_rf.seq and v141_rf.seq (in the current folder) with read, then
% writes each with write.
files = {'v131_rf', 'v141_rf'};
for i = 1:numel(files)
  seq = mr.Sequence();
  seq.read([files{i} '.seq']);
  seq.write([files{i} '_matlab.seq']);
  fprintf('%s.seq: read; write %s_matlab.seq: ok\n', files{i}, files{i});
end
