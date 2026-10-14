% Writes matlab_short_grad.seq: an arbitrary gradient of 3 samples on the
% default raster. MATLAB Pulseq writes it with a time shape 0.5 1.5 2.5.
sys = mr.opts();
seq = mr.Sequence(sys);
g = mr.makeArbitraryGrad('x', [1000 2000 1000], sys);
seq.addBlock(g);
seq.write('matlab_short_grad.seq');
