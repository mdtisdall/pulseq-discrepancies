---
id: DIS-0023
title: An RF magnitude shape with a sample below 0
kind: spec-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "an amplitude shape, RF or gradient, is in [-1, 1]"
  - key: cpp-reader
    behavior: "sets a magnitude sample below 0 to 0, with no message"
  - key: matlab-pulseq
    behavior: "plays the sample as written: a negative magnitude, the same as a phase of pi"
  - key: pypulseq
    behavior: "plays the sample as written, as MATLAB Pulseq"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D2.8]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0023: An RF magnitude shape with a sample below 0

## Summary

The specification allows [-1, 1] for the samples of an amplitude shape of an
RF or a gradient event. MATLAB Pulseq and pypulseq play a negative sample of
an RF magnitude shape as written, which is the magnitude of its absolute
value with the phase turned by π. The C++ reader sets the sample to 0, with
no message: the scanner plays no RF where the toolboxes play half the
amplitude.

## What each source does

| Source | What it does |
|---|---|
| Specification | "When used as amplitude shapes for gradient or RF objects, the decompressed samples must be in the normalised range of [-1, 1] (e.g. the absolute value of the shape must be normalized to the range of [0 1])" (section 2.9, `spec:624`). The RF `<mag_id>` is the "Shape ID for magnitude profile" (section 2.8.1, `spec:347`). It does not say that the magnitude shape alone is in [0, 1]. |
| C++ reader | `checkRF`, called at the end of `decodeBlock` (`cpp:2089`), sets each magnitude sample below 0 to 0 (`cpp:2287`), with no message; the header says that it checks the RF amplitude "between [0 1]" (`cpp.h:1203-1211`). The phase of the sample is not changed. |
| MATLAB Pulseq | `rf.signal = amplitude*mag.*exp(1j*2*pi*phase)` (`Sequence.m:524`): a sample of -0.5 is a signal of half the amplitude with the phase turned by π. Its writer writes the magnitude as `abs(signal)` divided by its largest value (`Sequence.m:584-586`), so it does not write the condition. |
| pypulseq | As MATLAB Pulseq (`sequence.py:1232`; `:1264` on master). Its writer writes `np.abs(signal)` divided by its largest value (`block.py:832-834`). |

## Reproducer

[`reproducers/DIS-0023/rf_magnitude_negative.seq`](../reproducers/DIS-0023/rf_magnitude_negative.seq),
written by hand (no writer writes the condition): one RF event of amplitude
1000 Hz on the default RF raster (1 µs), magnitude shape `1 -0.5 1 0.5`,
phase shape 0.

Commands as in DIS-0001, and `pulseq-cpp-oracle --dump` for the samples.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Valid (`spec:624`). The second sample: 500 Hz with a phase of π, if the magnitude shape is signed like any amplitude shape. | — |
| C++ reader | — | Read (exit 0; sanitized exit 0), no message. Magnitude `1 0 1 0.5`, phase `0 0 0 0`: the second µs plays 0 Hz. 2026-10-14. |
| MATLAB Pulseq | — | Read, no message. `abs(rf.signal)` 1000, 500, 1000, 500 Hz; `angle(rf.signal)` 0, π, 0, 0. 2026-10-14. |
| pypulseq | — | 1.5.0.post1 and master: read; the same values as MATLAB Pulseq. 2026-10-14. |

## Impact

MATLAB Pulseq and pypulseq do not write a negative magnitude. A file written
by another tool that stores a real RF pulse with a sign in the magnitude
(for example a sinc pulse with its negative lobes, and a phase shape of 0) is
read by both toolboxes as that pulse, while the scanner plays only its
positive lobes: a different flip angle and slice profile, with no message.

## Suggested resolution

The C++ reader: play a negative magnitude sample as its absolute value with
the phase turned by π (as the toolboxes do), or reject the file. If the
magnitude shape is meant to be in [0, 1], the specification could say so in
section 2.8.1 or 2.9, and the toolboxes could reject a negative sample.

## Report

Draft, to pulseq/pulseq:

> **C++ reader: a negative RF magnitude sample is set to 0**
>
> The specification allows [-1, 1] for an amplitude shape of an RF or a
> gradient event (section 2.9). `checkRF` sets a magnitude sample below 0 to
> 0 (`ExternalSequence.cpp:2287`), with no message. MATLAB Pulseq and
> pypulseq play the sample as written: in the attached file, the magnitude
> shape `1 -0.5 1 0.5` of a 1000 Hz pulse gives 500 Hz with a phase of π in
> the second µs in both toolboxes, and 0 Hz in the C++ reader. Could the
> reader play the sample with its sign (or reject the file), or the
> specification say that the magnitude shape is in [0, 1]?

## History

- 2026-10-09: found by pulseq-analysis (old ID D31, commit `49a7e2c`; the
  fixture `tests/seqfiles/bad_shape_rf_magnitude_negative.seq`).
- 2026-10-14: confirmed against the pinned sources; reproducer written and
  run in the C++ reader (plain and sanitized), MATLAB Pulseq under Octave
  11.3.0, and pypulseq 1.5.0.post1 and master `c977214` (1.5.1 file; the
  code paths cited do not depend on the version).
