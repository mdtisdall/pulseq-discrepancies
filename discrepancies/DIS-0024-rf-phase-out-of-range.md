---
id: DIS-0024
title: An RF phase shape with a sample outside [0, 1)
kind: spec-gap
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "silent on the unit and the range of the RF phase shape"
  - key: cpp-reader
    behavior: "multiplies by 2 pi and clamps to [0, 2 pi - 1e-4], with no wrap and no message"
  - key: matlab-pulseq
    behavior: "plays exp(i 2 pi p) for any p: a phase outside [0, 1) wraps"
  - key: pypulseq
    behavior: "as MATLAB Pulseq"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D2.9]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0024: An RF phase shape with a sample outside [0, 1)

## Summary

The specification gives neither the unit nor the range of the samples of an
RF phase shape. All three implementations read a sample as a fraction of a
turn, and both writers write it in [0, 1). For a sample outside [0, 1),
MATLAB Pulseq and pypulseq play `exp(i 2π p)`, so the phase wraps; the C++
reader clamps `2π p` to [0, 2π - 1e-4], with no message. A phase of 1.5
turns is π in the toolboxes and about 0 on the scanner; a phase of -0.25
turns is -π/2 in the toolboxes and 0 on the scanner.

## What each source does

| Source | What it does |
|---|---|
| Specification | The RF `<phase_id>` is the "Shape ID for phase profile", with no unit (section 2.8.1, `spec:348`). The range rule of section 2.9 is for amplitude shapes only (`spec:624`). Nothing says that the samples are in turns, or in which range. |
| C++ reader | Multiplies the phase samples by 2π (`cpp:2005`). `checkRF` then sets a phase above `2π - 1e-4` to `2π - 1e-4` and a phase below 0 to 0 (`cpp:2288-2289`), with no message; the header says that it checks "the phase between [0 2pi]" (`cpp.h:1203-1211`). |
| MATLAB Pulseq | `rf.signal = amplitude*mag.*exp(1j*2*pi*phase)` (`Sequence.m:524`), for any value. Its writer writes `angle(signal)`, plus 2π when negative, divided by 2π (`Sequence.m:587-589`): a value in [0, 1). |
| pypulseq | As MATLAB Pulseq: reads with `np.exp(1j * 2 * math.pi * phase)` (`sequence.py:1232`; `:1264` on master), writes the phase in [0, 1) (`block.py:838-840`). |

## Reproducer

[`reproducers/DIS-0024/rf_phase_range.seq`](../reproducers/DIS-0024/rf_phase_range.seq),
written by hand (no writer writes the condition): one RF event of amplitude
1000 Hz on the default RF raster (1 µs), magnitude shape `1 1 1 1`, phase
shape `0 0.25 1.5 -0.25` (turns).

Commands as in DIS-0001, and `pulseq-cpp-oracle --dump` for the samples.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent. | — |
| C++ reader | — | Read (exit 0; sanitized exit 0), no message. Phase 0, 1.57079637, 6.28308535, 0 rad: the third and fourth µs play about 0 rad. 2026-10-14. |
| MATLAB Pulseq | — | Read, no message. `angle(rf.signal)` 0, π/2, π, -π/2 rad. 2026-10-14. |
| pypulseq | — | 1.5.0.post1 and master: read; the same phases as MATLAB Pulseq. 2026-10-14. |

## Impact

A file written by MATLAB Pulseq or pypulseq has phases in [0, 1). A file
from another tool that stores an unwrapped phase (for example the phase of a
frequency-modulated pulse as a ramp of turns, or a phase of -0.25 for -90°)
is played by the scanner with that phase cut to [0, 2π), with no message,
while both toolboxes play the phase that the file gives. The pulse that the
scanner plays has another phase modulation, so another frequency and slice
profile.

## Suggested resolution

The specification: state that the RF phase shape is in turns (fractions of
2π), and either that its samples are in [0, 1) or that any value is allowed
and wraps. The C++ reader: wrap the phase modulo 2π, as the toolboxes do, in
place of clamping it; or reject a value outside the range that the
specification gives.

## Report

Draft, to pulseq/pulseq:

> **The unit and range of the RF phase shape; the C++ reader clamps it**
>
> The specification does not give the unit or the range of the samples of an
> RF phase shape (section 2.8.1, `<phase_id>`). The C++ reader, MATLAB Pulseq
> and pypulseq read them as turns, and the writers write them in [0, 1). For a
> value outside [0, 1), MATLAB Pulseq and pypulseq play `exp(i 2π p)`, so it
> wraps; the C++ reader clamps `2π p` to [0, 2π - 1e-4] (`checkRF`,
> `ExternalSequence.cpp:2288-2289`). In the attached file, the phase shape
> `0 0.25 1.5 -0.25` plays 0, π/2, π, -π/2 rad in the toolboxes and 0, π/2,
> 2π - 1e-4, 0 rad in the C++ reader. Could the specification state the unit
> and the range, and the C++ reader wrap the phase in place of clamping it?

## History

- 2026-10-09: found by pulseq-analysis (old ID D32, commit `49a7e2c`; the
  fixture `tests/seqfiles/bad_shape_rf_phase_range.seq`).
- 2026-10-14: confirmed against the pinned sources; reproducer written and
  run in the C++ reader (plain and sanitized), MATLAB Pulseq under Octave
  11.3.0, and pypulseq 1.5.0.post1 and master `c977214` (1.5.1 file; the
  code paths cited do not depend on the version).
