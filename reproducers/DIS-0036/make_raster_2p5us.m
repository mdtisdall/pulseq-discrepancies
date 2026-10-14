% Writes matlab_raster_2p5us.seq: an extended trapezoid with its vertices on
% a gradient raster of 2.5 us (0, 2.5, 7.5 and 10 us).
sys = mr.opts('gradRasterTime', 2.5e-6, 'blockDurationRaster', 10e-6);
seq = mr.Sequence(sys);
g = mr.makeExtendedTrapezoid('x', 'times', [0 2.5 7.5 10]*1e-6, ...
    'amplitudes', [0 1000 1000 0], 'system', sys);
seq.addBlock(g);
seq.write('matlab_raster_2p5us.seq');
