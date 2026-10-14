% Reads v131_rf_adc_grad.seq and v151_rf_adc_grad.seq (in the current folder)
% with three systems, and prints the block durations, the times of the
% gradient and the ADC samples (waveforms_and_times) and checkTiming.
systems = {mr.opts(), ...
           mr.opts('rfDeadTime', 100e-6, 'rfRingdownTime', 20e-6, 'adcDeadTime', 10e-6), ...
           mr.opts('gradRasterTime', 5e-6)};
names = {'default', 'deadtimes', 'grad5us'};
files = {'v131_rf_adc_grad.seq', 'v151_rf_adc_grad.seq'};
for f = 1:numel(files)
  for s = 1:numel(systems)
    seq = mr.Sequence(systems{s});
    seq.read(files{f});
    fprintf('%s %s: block durations (us) %s\n', files{f}, names{s}, mat2str(round(seq.blockDurations*1e9)/1e3));
    [wave, ~, ~, t_adc] = seq.waveforms_and_times(true);
    fprintf('  gx times (us) %s\n', mat2str(round(wave{1}(1,:)*1e9)/1e3));
    fprintf('  ADC samples (us) %g to %g\n', t_adc(1)*1e6, t_adc(end)*1e6);
    [ok, rep] = seq.checkTiming();
    fprintf('  checkTiming ok=%d %s\n', ok, strjoin(rep, ' | '));
  end
end
