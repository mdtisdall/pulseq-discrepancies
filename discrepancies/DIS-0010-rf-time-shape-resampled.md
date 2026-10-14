---
id: DIS-0010
title: Any other RF time shape, which the C++ reader resamples
kind: spec-vs-implementation
severity: crash
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "the time shape gives the time sampling points, in RF rasters"
  - key: cpp-reader
    behavior: "resamples to the RF raster; reads one sample past the end when the last time has a fraction of 0.5 or more"
  - key: matlab-pulseq
    behavior: "the samples at the times of the shape"
  - key: pypulseq
    behavior: "the samples at the times of the shape"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq, pypulseq]
  reason: "MATLAB makeArbitraryRf writes a one-sample time shape [5]. The C++ reader plays it for 5 us; the toolboxes give it a 10 us dwell. Off-raster last times crash the C++ reader."
pulseq_analysis:
  ids: [D2.11, D3.9, D5.8]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-13
---

# DIS-0010: Any other RF time shape, which the C++ reader resamples

## Summary

The specification gives an RF time shape as the times of the samples. MATLAB
Pulseq and pypulseq put each sample at its time. The C++ reader resamples any
time shape that it does not take as regular (DIS-0009) to cells of one RF
raster, by a nearest-sample rule; when the last time, in RF rasters, has a
fraction of 0.5 or more, the loop reads one sample past the end: a crash, or
undefined behaviour. A time shape of one sample, or of times that do not
increase, is played with another duration than the toolboxes give it.

## What each source does

| Source | What it does |
|---|---|
| Specification | The RF `<time_id>` is the "Shape ID for the time sampling points, specified in the units of `RadiofrequencyRasterTime`" (section 2.8.1, `spec:349`). It does not say that the times increase or start at 0. |
| C++ reader | Resamples the pulse to the RF raster (`cpp:2022-2050`): `nSamples = int(0.5 + t_last)` cells (`cpp:2031`); in cell `c` the index `tc` moves to the next sample when `waveform_t[tc] < c + 1` (`cpp:2039-2043`), and the cell plays the sample at `tc` (`cpp:2044-2045`). The check `tc < waveform_t.size()` lets `tc` reach the number of samples, so when the last time is below `nSamples` the last cells read past the samples. The FIXME at `cpp:2033` names linear interpolation as the intent. |
| MATLAB Pulseq | `rf.t` is the decompressed time shape times the RF raster, and `shape_dur` the last time rounded up to the raster (`Sequence.m:530-531`). |
| pypulseq | As MATLAB Pulseq (`sequence.py:1238-1239`; `:1270-1271` on master). |

## Reproducer

In [`reproducers/DIS-0010/`](../reproducers/DIS-0010/), each one RF event of
amplitude 1000 Hz:

- `time_end.seq`: 2 samples at the times `0` and `99.6` (RF raster 1 µs);
- `one_sample.seq`: 1 sample at the time `5`;
- `matlab_one_sample.seq`: written by MATLAB Pulseq from
  `mr.makeArbitraryRf([1], pi/20, 'dwell', 1e-5)`: 1 sample at the time `5`;
- `decreasing.seq`: 3 samples at the times `10 5 1`.

Commands as in DIS-0001, and `pulseq-cpp-oracle --dump` for the samples.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | `time_end.seq`: samples at 0 and 99.6 µs. `one_sample.seq`: one sample at 5 µs. | — |
| C++ reader | — | `time_end.seq`: crash (exit 70); sanitized: libc++ assertion (`vector::operator[]`) in `decodeBlock` (exit 3). `one_sample.seq`, `matlab_one_sample.seq`: read, 5 cells of 1 µs (`shape_dur` 5 µs, where MATLAB Pulseq meant one dwell of 10 µs). `decreasing.seq`: read, 1 cell of 1 µs. 2026-10-13. |
| MATLAB Pulseq | — | All read; `time_end.seq`: `rf.t` 0 and 99.6 µs; `one_sample.seq`: `rf.t` 5 µs. 2026-10-13. |
| pypulseq | — | All read. 2026-10-13. |

## Impact

A pulse given by points whose last time is not on the RF raster, such as
`time_end.seq`, makes the scanner's reader read past its samples; both
toolboxes read it. MATLAB Pulseq's short regular pulses hit the same loop
(DIS-0009). The other time
shapes are played by the scanner with the nearest-sample artefacts of the
resampling, and a time shape of one sample for one dwell (which MATLAB Pulseq
writes) is played for half that dwell.

## Suggested resolution

The C++ reader: stop the index at the last sample in the resampling loop
(`cpp:2037-2046`), and reject a time shape whose times do not increase. The
specification: state whether the times of an RF time shape must increase and
start at 0 or later, and what the duration of a pulse of one sample is.

## Report

Draft, to pulseq/pulseq:

> **C++ reader: the resampling of an RF time shape reads past the samples**
>
> For a time shape that is not stored as a regular step, `decodeBlock`
> resamples the pulse to `int(0.5 + t_last)` cells
> (`ExternalSequence.cpp:2031`). The index `tc` can reach the number of
> samples (`tc < waveform_t.size()` at line 2041 is checked before `++tc`),
> and lines 2044-2045 then read `waveform[tc]` and `waveform_p[tc]` past the
> end. This happens whenever the last time, in RF rasters, has a fraction of
> 0.5 or more: the time shape `0 99.6` of the attached file is read past its
> 2 samples. MATLAB Pulseq and pypulseq read the file. Could the index stop at
> the last sample (or, as the FIXME at line 2033 says, the pulse be
> interpolated)?

## History

- 2026-10-09: found by pulseq-analysis (old ID D36, commit `49a7e2c`); the
  time shape of one sample on 2026-10-13 (D3.9, `5bd053a`).
- 2026-10-13: confirmed against the pinned sources; the MATLAB file written
  under Octave 11.3.0, and all files run in the C++ reader (plain and
  sanitized), MATLAB Pulseq and pypulseq (1.5.1 files).
- 2026-10-13: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, not at the fork that `sources.yaml` pins;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
