---
id: DIS-0022
title: An amplitude shape with a sample outside [-1, 1]
kind: spec-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "the decompressed samples of an amplitude shape must be in [-1, 1]"
  - key: cpp-reader
    behavior: "reads; clamps arbitrary gradient samples to [-1, 1] and RF magnitude samples to [0, 1], with no message; does not clamp extended trapezoids"
  - key: matlab-pulseq
    behavior: "reads, and plays the samples as written"
  - key: pypulseq
    behavior: "reads, and plays the samples as written"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
pulseq_analysis:
  ids: [D30]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0022: An amplitude shape with a sample outside [-1, 1]

## Summary

The specification says that the samples of an amplitude shape must be in
[-1, 1]. No source rejects a file with a sample outside that range, and they
play it differently: the C++ reader clamps the samples of an arbitrary
gradient and of an RF magnitude shape, with no message, but not the samples
of an extended trapezoid; MATLAB Pulseq and pypulseq play every sample as
written. The scanner plays a gradient of 1.0 times the amplitude where the
toolboxes play 1.5 times the amplitude.

## What each source does

| Source | What it does |
|---|---|
| Specification | "When used as amplitude shapes for gradient or RF objects, the decompressed samples must be in the normalised range of [-1, 1]" (section 2.9, `spec:624`). It does not say what a reader does with a sample outside the range. |
| C++ reader | `decodeBlock` calls `checkGradient` and `checkRF` (`cpp:2088-2089`). `checkGradient` sets each sample of `gradWaveforms` above 1 to 1 and below -1 to -1 (`cpp:2265-2278`); `gradWaveforms` holds the arbitrary gradients (`cpp:2126-2149`), not the extended trapezoids, which are in `gradExtTrapForms` (`cpp:2189`) and are not clamped. `checkRF` sets each RF magnitude sample above 1 to 1 and below 0 to 0 (`cpp:2286-2287`; a sample below 0 is DIS-0023). There is no message. The header gives the range as [0 1] for both (`cpp.h:1194-1211`). |
| MATLAB Pulseq | Multiplies the decompressed samples by the amplitude, with no check: `rf.signal = amplitude*mag.*exp(1j*2*pi*phase)` (`Sequence.m:524`), `grad.waveform = amplitude*g` (`Sequence.m:1376`). Its writer divides a gradient by its largest absolute value (`Sequence.m:654-668`) and an RF signal by its largest magnitude (`Sequence.m:584-586`), so it does not write the condition. |
| pypulseq | As MATLAB Pulseq: `rf.signal = amplitude * mag * np.exp(...)` (`sequence.py:1232`; `:1264` on master), `grad.waveform = amplitude * g` (`block.py:413`). Its writer divides by the largest absolute value too (`block.py:678-690`, `block.py:832-834`). |

## Reproducer

[`reproducers/DIS-0022/amplitude_above_1.seq`](../reproducers/DIS-0022/amplitude_above_1.seq),
written by hand (no writer writes the condition): three blocks, each with one
sample of 1.5 in its amplitude shape.

- Block 1: an RF event of amplitude 1000 Hz, magnitude shape `0.5 1 1.5 1`.
- Block 2: an arbitrary gradient of amplitude 100000 Hz/m on the gradient
  raster, shape `0 0.75 1.5 0.75 0`.
- Block 3: an extended trapezoid of amplitude 100000 Hz/m, shape `0 1.5 0`
  at the times `0 1 2` (gradient rasters).

Commands as in DIS-0001, and `pulseq-cpp-oracle --dump` for the samples;
`printf '1 25\n2 10\n' | pulseq-cpp-oracle --sample FILE` for the gradient
that `SeqBlock::gradientsAt` gives in block 2 at 25 µs and block 3 at 10 µs.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | The file is not valid (`spec:624`). | — |
| C++ reader | — | Read (exit 0; sanitized exit 0), no message. RF magnitude `0.5 1 1 1` (peak 1000 Hz); arbitrary gradient `0 0.75 1 0.75 0`; extended trapezoid `0 1.5 0`. `--sample`: 100000 Hz/m in block 2 at 25 µs, 150000 Hz/m in block 3 at 10 µs. 2026-10-14. |
| MATLAB Pulseq | — | Read, no message. RF signal 500, 1000, 1500, 1000 Hz; gradient of block 2 0, 75000, 150000, 75000, 0 Hz/m; block 3 0, 150000, 0 Hz/m. 2026-10-14. |
| pypulseq | — | 1.5.0.post1 and master: read, no message (only the warning that the file version 1.5.1 is above 1.5.0); the same values as MATLAB Pulseq. 2026-10-14. |

## Impact

A file written by MATLAB Pulseq or pypulseq does not have the condition
(apart from the rounding of compression, which is far below the 0.5 of the
reproducer). A file written by another tool, or edited by hand, with a sample
outside [-1, 1] is played by the scanner with that sample cut to the range,
with no message, while both toolboxes compute the k-space, the gradient
moments and the RF power from the sample as written. An extended trapezoid
with the same sample is played as written by all three.

## Suggested resolution

The readers: reject a file whose amplitude shape has a sample outside
[-1, 1] (with a small tolerance for the error of compression), or at least
warn, as the specification makes it invalid. The C++ reader: treat arbitrary
gradients and extended trapezoids the same, and correct the [0 1] of the
comment of `checkGradient` (`cpp.h:1194-1201`).

## Report

Draft, to pulseq/pulseq (C++ reader and MATLAB toolbox) and pulseq/pypulseq:

> **An amplitude shape with a sample outside [-1, 1] is read with no message**
>
> The specification says that the decompressed samples of an amplitude shape
> "must be in the normalised range of [-1, 1]" (section 2.9). No reader
> rejects a file that breaks this rule, and they play it differently. In the
> attached file, each of three amplitude shapes has a sample of 1.5. The C++
> reader cuts the sample to 1 for the RF magnitude and for the arbitrary
> gradient (`checkRF`, `checkGradient`, `ExternalSequence.cpp:2265-2291`),
> with no message, but not for the extended trapezoid, which is not in
> `gradWaveforms`. MATLAB Pulseq and pypulseq play 1.5 times the amplitude in
> all three. Could the readers reject (or warn about) such a sample?

## History

- 2026-10-09: found by pulseq-analysis (old ID D30, commit `49a7e2c`; the
  fixture `tests/seqfiles/bad_shape_range.seq`). The ID has no entry at
  `5bd053a`.
- 2026-10-14: confirmed against the pinned sources; reproducer written and
  run in the C++ reader (plain and sanitized), MATLAB Pulseq under Octave
  11.3.0, and pypulseq 1.5.0.post1 and master `c977214` (1.5.1 file; the
  code paths cited do not depend on the version). That the C++ reader does
  not clamp an extended trapezoid was found in this check.
