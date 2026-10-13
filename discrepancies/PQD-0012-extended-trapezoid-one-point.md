---
id: PQD-0012
title: An extended trapezoid of one point at a time above 0
kind: spec-gap
severity: crash
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "silent on the number of points of a gradient time shape, and on its first time"
  - key: cpp-reader
    behavior: "gradientsAt reads times[1] and wave[1], past both vectors"
  - key: matlab-pulseq
    behavior: "reads the point at its time"
  - key: pypulseq
    behavior: "reads the point at its time"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D5.10]
  commit: 5bd053a
found: 2026-10-12
checked: 2026-10-13
---

# PQD-0012: An extended trapezoid of one point at a time above 0

## Summary

A `[GRADIENTS]` row with a time shape is an extended trapezoid: points joined
by lines. The specification does not say how many points it has, or that the
first is at time 0. MATLAB Pulseq and pypulseq read an extended trapezoid of
one point at 40 µs. The C++ reader reads it too, but its `gradientsAt` reads
`times[1]` and `wave[1]` for a time between the gradient's start and that
point: past both vectors, a crash, or undefined behaviour.

## What each source does

| Source | What it does |
|---|---|
| Specification | The `<time_id>` of a `[GRADIENTS]` row gives "the time sampling points, specified in the units of `GradientRasterTime`" (section 2.8.2, `spec:395`). Nothing on their number or on the first time. |
| C++ reader | Reads the event (`cpp:2165-2193`). `SeqBlock::gradientsAt` returns early before the delay or for an amplitude of 0 (`cpp:3614`), and after the last time (`cpp:3621`), or at the first or the last time (`cpp:3628-3637`). Between the delay and a single point above 0, its binary search starts with the bounds 0 and `times.size()` = 1 and does not run, and it interpolates between `times[0]` and `times[1]`, `wave[0]` and `wave[1]` (`cpp:3639-3650`): one past the end of each vector. |
| MATLAB Pulseq | Reads the point at its time (run: `tt` 40 µs). |
| pypulseq | Reads the file (`read`, `get_block`, `waveforms_and_times`; run). |

## Reproducer

[`reproducers/PQD-0012/ext_trap_one_point.seq`](../reproducers/PQD-0012/ext_trap_one_point.seq):
one block of 100 µs with the gradient

```
[GRADIENTS]
1 100000 0 50000 3 4 0
```

whose amplitude shape 3 is `0.5` and time shape 4 is `4` (one point at 40 µs).
Commands as in PQD-0001, and `pulseq-cpp-oracle --sample FILE` with the line
`0 20` on stdin (the gradients of block 0 at 20 µs, by `gradientsAt`).

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent on a gradient of one point. | — |
| C++ reader | — | `load` and `decodeBlock`: read (exit 0). `--sample` at 20 µs: crash (exit 70); sanitized: libc++ assertion (`vector::operator[]`) in `SeqBlock::gradientsAt` (exit 3). 2026-10-13. |
| MATLAB Pulseq | — | Read; `tt` 40 µs, `waveform` 50000 Hz/m. 2026-10-13. |
| pypulseq | — | Read. 2026-10-13. |

## Impact

The makers of the toolboxes do not write this condition: MATLAB Pulseq's
`makeExtendedTrapezoid` refuses a first point above 0 with an amplitude other
than 0 (`makeExtendedTrapezoid.m:62-63`), and for the one point
`times [40e-6]`, `amplitudes [0]` it writes the time as a delay of 40 µs, a
time shape `0` and an amplitude of 0 (run), which the C++ reader samples
without error. A file from another tool with one point above 0 is read by
both toolboxes and makes the reader's `gradientsAt` read past its vectors.

## Suggested resolution

The C++ reader: in `gradientsAt`, handle a time shape of one point (and a time
before the first point) without the interpolation; or reject an extended
trapezoid of fewer than 2 points, or whose first time is not 0, when it reads
the file. The specification: state the number of points and the first time of
a gradient time shape.

## Report

Draft, to pulseq/pulseq:

> **C++ reader: `gradientsAt` on an extended trapezoid of one point**
>
> For an extended trapezoid whose time shape is one point above 0 (the
> attached file: one point at 40 µs), `SeqBlock::gradientsAt` at a time
> before that point skips the binary search (`nUpperBoundCnt` is 1) and
> interpolates with `times[1]` and `wave[1]`
> (`ExternalSequence.cpp:3639-3650`), past both vectors. MATLAB Pulseq and
> pypulseq read the file.

## History

- 2026-10-12: found by pulseq-analysis (D5.10, commit `5bd053a`).
- 2026-10-13: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized, `--sample`), MATLAB Pulseq and pypulseq (a
  1.5.1 file); MATLAB Pulseq's `makeExtendedTrapezoid` run under Octave
  11.3.0.
