---
id: DIS-0018
title: A number with a fraction in an integer column, such as an RF delay of 100.5
kind: spec-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "the RF, gradient and ADC delays are integers (µs)"
  - key: cpp-reader
    behavior: "reads the integer part; for an RF or ADC delay, the rest of the row moves one column"
  - key: matlab-pulseq
    behavior: "reads the fraction; writes an RF delay of 100.5 when the RF raster is below 1 µs"
  - key: pypulseq
    behavior: "reads an RF delay of 100.5; rounds a gradient or ADC delay to a whole µs; writes 100.5"
    version: "1.5.0.post1"
  - key: pypulseq
    behavior: "reads as 1.5.0.post1; writes the RF delay rounded to a whole µs (100)"
    version: "master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq]
  reason: "MATLAB Pulseq writes an RF delay such as 100.5 when the RF raster is below 1 us; the spec types it as an integer. The C++ reader reads 100 and shifts the rest of the row. pypulseq master rounds it (pulseq/pypulseq#406)."
pulseq_analysis:
  ids: [D14]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0018: A number with a fraction in an integer column, such as an RF delay of 100.5

## Summary

The specification types the RF, gradient and ADC delays as integers in µs.
MATLAB Pulseq writes the RF delay with `%g`, so with an RF raster below 1 µs
it writes a delay such as `100.5`. MATLAB Pulseq and pypulseq read 100.5 µs.
The C++ reader reads the row with `sscanf`: the delay is 100 µs, and `.5`
and the values after it move one column, so the pulse plays with the wrong
frequency and phase offsets.

## What each source does

| Source | What it does |
|---|---|
| Specification | "integer types are stored as 64-bit unsigned integers" (section 2.1, `spec:176`). The RF `<delay>` is an integer in µs (section 2.8.1, `spec:351`); so are the gradient delay (section 2.8.2, `spec:399`) and the ADC delay (section 2.8.3, `spec:438`). The text gives no syntax for a number and no rule for a value with a fraction in an integer column. |
| C++ reader | Holds the delays as `int` (`cpp.h:100`, `cpp.h:116`, `cpp.h:141`) and reads a 1.5 RF row with `"%d%f%d%d%d%f%d%f%f%f%f %c"` (`cpp:1042-1044`). For `100.5`, `%d` reads `100` and stops at `.`; the next `%f` reads `.5` as `freq_ppm`, and each later value goes to the field before its own: `phase_ppm` takes `freq_ppm`, `freq` takes `phase_ppm`, `phase` takes `freq`, and `use` is the first character of `phase`. The row still gives 12 conversions, so it is accepted. The ADC row (`"%d%d%d%d%f%f%f%f%d"`, `cpp:1148`) moves the same way. A fraction in the last column of `[TRAP]` (`cpp:1117`) or `[GRADIENTS]` (`cpp:1073`) is cut: the delay is the integer part and the rest is not read. |
| MATLAB Pulseq | Reads every column of an event row with `%f` (`read.m:520-526`, `read.m:548`, `read.m:565`; the RF row: `read.m:120`), so the delay is 100.5 µs. Writes the RF delay rounded to the RF raster, in µs, with `%g` (`write.m:85-86`): with `RadiofrequencyRasterTime` 0.5 µs the delay is written `100.5` (run). |
| pypulseq | Reads every column of an event row with `float()` (`read_seq.py:822`; `:830` on master): the RF delay is 100.5 µs. `read` then calls `remove_duplicates` (`read_seq.py:443-444`), which rounds the gradient times and delays and the ADC delay to whole µs (`sequence.py:1179`, `:1195`; `:1211`, `:1227` on master) and keeps 6 significant digits of the RF delay (`sequence.py:1188`; `:1220` on master). 1.5.0.post1 writes the RF delay with `{:g}` (`write_seq.py:111`, `:117`), so it writes `100.5` as MATLAB does (run). Master writes it with `{:.0f}` (`write_seq.py:111`, changed by pulseq/pypulseq#406), so it writes `100` (run). |

## Reproducer

In [`reproducers/DIS-0018/`](../reproducers/DIS-0018/):

- `matlab_rf_delay.seq`: written by MATLAB Pulseq under Octave 11.3.0:

  ```matlab
  sys = mr.opts('rfRasterTime', 0.5e-6);
  seq = mr.Sequence(sys);
  rf = mr.makeBlockPulse(pi/20, sys, 'Duration', 100e-6, 'delay', 100.5e-6, ...
      'freqOffset', 1000, 'phaseOffset', 0.5, 'use', 'excitation');
  seq.addBlock(rf, mr.makeDelay(300e-6));
  seq.write('matlab_rf_delay.seq');
  ```

  Its RF row:

  ```
  # id ampl. mag_id phase_id time_shape_id center delay freqPPM phasePPM freq phase use
  1          250 1 2 3 50 100.5 0 0 1000 0.5 e
  ```

  The same script with pypulseq 1.5.0.post1 (`pp.Opts(rf_raster_time=0.5e-6)`,
  `make_block_pulse`) writes the same row; with pypulseq master it writes the
  delay `100`.
- `trap_adc_delay_fraction.seq`: written by hand. A trapezoid with the delay
  `10.5` and an ADC row `1 10 10000 20.5 0 0 1000 0.5 0` (delay 20.5 µs,
  `freq` 1000 Hz, `phase` 0.5 rad), in one block.
- `grad_delay_fraction.seq`: written by hand. An arbitrary gradient with the
  delay `10.5`.

Commands as in DIS-0001, and `pulseq-cpp-oracle --dump` for the values that
the C++ reader holds.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | `matlab_rf_delay.seq`: the RF delay is an integer, so the row is not a valid row; the specification does not say what a reader does. | — |
| C++ reader | — | `matlab_rf_delay.seq`: read (exit 0; sanitized build exit 0). RF: `delay` 100 µs, `freq_ppm` 0.5, `phase_ppm` 0, `freq_offset` 0 Hz, `phase_offset` 1000 rad, `use` `'0'`. `trap_adc_delay_fraction.seq`: read; trapezoid delay 10 µs; ADC `delay` 20 µs, `freq_ppm` 0.5, `freq_offset` 0 Hz, `phase_offset` 1000 rad. `grad_delay_fraction.seq`: read; delay 10 µs. 2026-10-14. |
| MATLAB Pulseq | — | `matlab_rf_delay.seq`: RF `delay` 100.5 µs, `freqOffset` 1000 Hz, `phaseOffset` 0.5 rad, `use` excitation; `waveforms_and_times`: the pulse from 100.5 to 200.5 µs. `trap_adc_delay_fraction.seq`: trapezoid delay 10.5 µs, ADC delay 20.5 µs, `freqOffset` 1000 Hz, `phaseOffset` 0.5 rad. `grad_delay_fraction.seq`: delay 10.5 µs. 2026-10-14. |
| pypulseq | — | 1.5.0.post1 and master, the same: `matlab_rf_delay.seq`: RF `delay` 100.5 µs, `freq_offset` 1000 Hz, `phase_offset` 0.5 rad; the pulse from 100.5 to 200.5 µs. `trap_adc_delay_fraction.seq`: trapezoid delay 10 µs, ADC delay 20 µs, `freq_offset` 1000 Hz, `phase_offset` 0.5 rad. `grad_delay_fraction.seq`: delay 10 µs. 2026-10-14. |

## Impact

A MATLAB Pulseq sequence made with an RF raster below 1 µs (for example
0.5 µs) and an RF delay that is not a whole µs is written with a fractional
delay; so is the same sequence written by pypulseq 1.5.0.post1. Both
toolboxes play it as written. The scanner's reader plays the pulse 0.5 µs
early, without its frequency offset, with the value of the frequency offset
as its phase, and with a frequency offset of 0.5 ppm (about 64 Hz at 3 T);
no message is printed. A hand-edited ADC delay with a fraction is misread in
the same way; a trapezoid or arbitrary gradient delay with a fraction is cut
to whole µs by the C++ reader and by pypulseq, and kept by MATLAB Pulseq.

## Suggested resolution

The C++ reader: read each row as a list of tokens, and reject a row whose
integer column has a fraction (or read the column as a float and round it),
in place of reading `%d` and going on with the rest of the token. MATLAB
Pulseq: write the RF delay with `%d` of the rounded µs, as pypulseq master
does since pulseq/pypulseq#406, or reject an RF delay that is not a whole µs
when the sequence is written.

## Report

Draft, to pulseq/pulseq:

> **An RF delay with a fraction: written by MATLAB, misread by the C++ reader**
>
> The specification types the RF delay as an integer in µs (section 2.8.1).
> `write.m` writes the delay rounded to the RF raster with `%g` (lines
> 85-86), so with `mr.opts('rfRasterTime', 0.5e-6)` and a delay of
> 100.5 µs the RF row is `1 250 1 2 3 50 100.5 0 0 1000 0.5 e`. MATLAB
> Pulseq reads it back as written. `ExternalSequence::load` reads the row
> with `%d` for the delay (`ExternalSequence.cpp:1042-1044`): it reads 100,
> then `.5` as `freq_ppm`, and each later value goes one field to the left:
> `freq_offset` 0, `phase_offset` 1000 rad, `use` `'0'`. The row has 12
> conversions, so no error is printed. The ADC row (line 1148) moves the
> same way. Reproducer attached (`matlab_rf_delay.seq`, written by MATLAB
> Pulseq). Could `write.m` write whole µs (pypulseq master does since
> pulseq/pypulseq#406), and could the C++ reader reject a fraction in an
> integer column?

## History

- 2026-10-09: found by pulseq-analysis (old ID D14, commit `49a7e2c`, part
  (3): "`100.5` as the RF delay"). The other parts of D14 (rows with too few
  or too many values, encoding, NaN, negative values) are DIS-0048 to
  DIS-0051. At `5bd053a` the misreading of a fraction is listed as removed
  from D14 (appendix, the old IDs), so it has no new ID.
- 2026-10-14: confirmed against the pinned sources. The MATLAB file written
  and read under Octave 11.3.0; the same input written by pypulseq
  1.5.0.post1 and master; both files run in the C++ reader (plain and
  sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and master `c977214`,
  with the two hand-written files.
  The citations give the lines of 1.5.0.post1, with those of master where
  they differ.
