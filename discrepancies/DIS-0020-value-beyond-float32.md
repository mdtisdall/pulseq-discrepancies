---
id: DIS-0020
title: A value with more digits than a 32-bit float holds
kind: spec-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "floats are 64-bit; shapes are 32-bit floats"
  - key: cpp-reader
    behavior: "holds amplitudes, offsets and shape samples as 32-bit floats, and decompresses a shape in 32-bit floats"
  - key: matlab-pulseq
    behavior: "64-bit values, as in the file"
  - key: pypulseq
    behavior: "64-bit values, but read rounds event values to 6 significant digits"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
pulseq_analysis:
  ids: [D7.2]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0020: A value with more digits than a 32-bit float holds

## Summary

The specification stores the float values of the events as 64-bit floats,
and the shapes as 32-bit floats. The C++ reader holds the amplitudes, the
frequency and phase offsets and the shape samples as 32-bit floats, and it
decompresses a shape by a cumulative sum in 32-bit floats, so a long
compressed shape drifts: a linear RF ramp of 10000 samples written by
MATLAB Pulseq is 6e-5 low at its middle. pypulseq rounds the event values to
6 significant digits when it reads a file. MATLAB Pulseq keeps the values of
the file.

## What each source does

| Source | What it does |
|---|---|
| Specification | "In general, integer types are stored as 64-bit unsigned integers while floating-point numbers are in the 64-bit IEEE 754 floating-point format. Exceptions are `<id>` values, which are 32-bit integers. Shapes are stored as 32-bit single-precision floats." (section 2.1, `spec:176`). The decompressed shape is the cumulative sum of the derivative (section 2.9.1, `spec:628-687`); the specification notes that compression can give "rounding errors" (section 2.9, `spec:602`), but does not give the precision of the sum. |
| C++ reader | Holds as `float` the RF amplitude, `center`, `freq_ppm`, `phase_ppm`, `freq` and `phase` (`cpp.h:90`, `cpp.h:95-99`), the gradient amplitude, `first` and `last` (`cpp.h:115`, `cpp.h:124-125`), the ADC offsets (`cpp.h:142-145`), and the shape samples (`cpp:937`, `cpp:959`, `cpp.h:780`). `decompressShape` sums the derivative in `float` (`cpp:2241-2244`). `checkRF` then limits an RF magnitude above 1 to 1 (`cpp:2286`). |
| MATLAB Pulseq | Reads the event values and the shape samples as doubles with `sscanf('%f')` (`read.m:548`, `read.m:565`, `read.m:654`; a comment at `read.m:655` notes that "C-code uses single precision"), and decompresses with `cumsum` in doubles (`decompressShape.m:64`). |
| pypulseq | Reads the values as Python floats (`read_seq.py:689`, `read_seq.py:822`; `:691`, `:830` on master) and decompresses with `np.cumsum` in doubles (`decompress_shape.py:69`). `read` then calls `remove_duplicates` (`read_seq.py:443-444`), which replaces each event by its values rounded to 6 significant digits (the gradient and RF amplitudes, the frequency and phase offsets; `sequence.py:1179`, `:1188`, `:1195`; `:1211`, `:1220`, `:1227` on master; `round_data`, `event_lib.py:275-283`), and each shape by its samples rounded to 9 significant digits (`sequence.py:1161`; `:1193` on master). |

## Reproducer

In [`reproducers/DIS-0020/`](../reproducers/DIS-0020/):

- `matlab_rf_ramp.seq`: written by MATLAB Pulseq under Octave 11.3.0:

  ```matlab
  sys = mr.opts();
  seq = mr.Sequence(sys);
  rf = mr.makeArbitraryRf((1:10000)/10000, pi/2, sys, 'dwell', 1e-6, 'use', 'excitation');
  seq.addBlock(rf);
  seq.write('matlab_rf_ramp.seq');
  ```

  Its RF row is `1 49.995 1 2 0 9999.5 0 0 0 0 0 e`, and its magnitude
  shape is stored in three values:

  ```
  shape_id 1
  num_samples 10000
  0.0001
  0.0001
  9998
  ```

  Sample `i` (from 1) is `i/10000`.
- `trap_amplitude.seq`: written by hand. A trapezoid of amplitude
  `1234567.891` Hz/m and an ADC with `freq` `123456.789` Hz and `phase`
  `0.123456789` rad, in one block. (The writers write the event values with
  `%12g` and `%g`, 6 significant digits; they write the shape samples with
  `%.9g`.)

Commands as in DIS-0001; `pulseq-cpp-oracle --dump` for the samples that the
C++ reader holds after `decodeBlock`, and `printf '0 60\n' |
pulseq-cpp-oracle --sample trap_amplitude.seq` for the gradient that
`SeqBlock::gradientsAt` gives at 60 µs.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | `matlab_rf_ramp.seq`: the samples `i/10000`, with the amplitude 49.995 Hz (24.9975 Hz at sample 5000); the precision of a 32-bit float is about 6e-8. `trap_amplitude.seq`: the values of the file, as 64-bit floats. | — |
| C++ reader | — | `matlab_rf_ramp.seq`: read (exit 0; sanitized build exit 0). Amplitude 49.9949989; sample 1000: 0.100001119; sample 5000: 0.499970615 (relative error -5.9e-5, 24.99603 Hz); sample 9999: 0.999953568 (+5.4e-5); the sum reaches 1.0000535 at sample 10000, and `checkRF` limits it to 1. `trap_amplitude.seq`: amplitude 1234567.875 (`--sample` at 60 µs: 1234567.875 Hz/m); ADC `freq` 123456.789 (32-bit: 123456.7890625), `phase` 0.123456791. 2026-10-14. |
| MATLAB Pulseq | — | `matlab_rf_ramp.seq`: sample 5000: 24.9975 Hz; sample 10000: 49.995 Hz. `trap_amplitude.seq`: amplitude 1234567.891, the waveform 1234567.891 Hz/m on the flat top; ADC `freqOffset` 123456.789, `phaseOffset` 0.123456789. 2026-10-14. |
| pypulseq | — | 1.5.0.post1 and master, the same: `matlab_rf_ramp.seq`: as MATLAB Pulseq. `trap_amplitude.seq`: amplitude 1234570, the waveform 1234570 Hz/m on the flat top; ADC `freq_offset` 123457 Hz, `phase_offset` 0.123457 rad. 2026-10-14. |

## Impact

The 32-bit values of the C++ reader differ from the 64-bit values of the
file by about 6e-8 of the value: small for one value. The cumulative sum in
32-bit floats adds an error at each sample, so a long compressed shape (a
ramp, a long constant gradient, a long RF pulse with a regular slope) is
played with a drift that grows with its length: 6e-5 of the full scale
after 5000 samples in the MATLAB file of the reproducer, and a last sample
above 1 that is cut to 1. pypulseq's rounding to 6 significant digits
changes a frequency offset of 123456.789 Hz by 0.211 Hz and any other value
with more than 6 significant digits, so its waveforms are not those of the
file.

## Suggested resolution

The C++ reader: decompress the shapes with a `double` accumulator (or in
`double` and then store `float`), and hold the event values as `double`, as
the specification states. pypulseq: do not round the values of a file in
`read`; compare rounded copies to find duplicates, and keep the values of
the file.

## Report

Draft, to pulseq/pulseq:

> **C++ reader: shapes decompressed in 32-bit floats drift**
>
> `ExternalSequence::decompressShape` sums the derivative of a compressed
> shape in `float` (`ExternalSequence.cpp:2241-2244`). For a long shape the
> error grows with each sample. MATLAB Pulseq writes
> `mr.makeArbitraryRf((1:10000)/10000, pi/2, sys, 'dwell', 1e-6)` as a shape
> of three values (`0.0001 0.0001 9998`); after `decodeBlock` sample 5000 is
> 0.499970615 (MATLAB Pulseq: 0.5), and the last sample is 1.0000535 before
> `checkRF` limits it to 1. The event values (amplitudes, frequency and
> phase offsets) are also held as `float` (`ExternalSequence.h:90-99`,
> `:115`, `:124-125`, `:142-145`), where the specification states 64-bit
> floats (section 2.1). Could the reader sum in `double`, and hold the event
> values as `double`? Reproducer attached (`matlab_rf_ramp.seq`).

Draft, to pulseq/pypulseq:

> **`Sequence.read` rounds the values of the file to 6 significant digits**
>
> `read` calls `remove_duplicates(in_place=True)` (`read_seq.py:443-444`),
> which replaces each RF, gradient and ADC event by its values rounded to 6
> significant digits (`sequence.py`, `remove_duplicates`). A trapezoid of
> amplitude `1234567.891` Hz/m is then played at 1234570 Hz/m, and an ADC
> frequency offset of `123456.789` Hz at 123457 Hz; MATLAB Pulseq plays the
> values of the file. Could `read` keep the values, and use rounded copies
> only to find duplicates? Reproducer attached (`trap_amplitude.seq`).

## History

- 2026-10-09: found by pulseq-analysis (old ID D18, commit `49a7e2c`; D7.2
  of `packages/pulseq-cpp-siemens/docs/specification.md` at `5bd053a`).
  pulseq-analysis gives the 32-bit amplitude of the C++ reader; the drift of
  the 32-bit cumulative sum and the rounding of pypulseq are new here.
- 2026-10-14: confirmed against the pinned sources. The MATLAB file written
  and read under Octave 11.3.0; both files run in the C++ reader (plain and
  sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and master `c977214`
  (1.5.1 files; the cited code does not depend on the version). The
  citations give the lines of 1.5.0.post1, with those of master where they
  differ.
