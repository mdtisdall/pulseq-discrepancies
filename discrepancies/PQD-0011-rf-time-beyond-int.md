---
id: PQD-0011
title: An RF time shape whose last time does not fit an int
kind: spec-gap
severity: crash
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "no bound on the times of a time shape"
  - key: cpp-reader
    behavior: "converts the last time to int, which is undefined behaviour above INT_MAX"
  - key: matlab-pulseq
    behavior: "reads the times as written"
  - key: pypulseq
    behavior: "reads the times as written"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D5.9]
  commit: 5bd053a
found: 2026-10-12
checked: 2026-10-13
---

# PQD-0011: An RF time shape whose last time does not fit an int

## Summary

The specification sets no bound on the times of an RF time shape. MATLAB
Pulseq and pypulseq read a time shape whose last time is 3e9 RF rasters. The
C++ reader converts that time to `int` to size its resampled pulse; above
`INT_MAX` the conversion is undefined behaviour, and in a release build the
reader does not end in 10 s.

## What each source does

| Source | What it does |
|---|---|
| Specification | The RF `<time_id>` gives "the time sampling points, specified in the units of `RadiofrequencyRasterTime`" (section 2.8.1, `spec:349`); the samples of a shape are 32-bit floats (`spec:176`). No bound. |
| C++ reader | For a time shape that it resamples (PQD-0010), `int nSamples=int(0.5+waveform_t.back())` (`cpp:2031`): a float above `INT_MAX` (2147483647) has no `int` value, and the conversion is undefined behaviour. The result sizes two vectors and the loop over the cells (`cpp:2034-2037`). |
| MATLAB Pulseq | `rf.t` is the time shape times the RF raster (`Sequence.m:530`). |
| pypulseq | As MATLAB Pulseq (`sequence.py:1238`). |

## Reproducer

[`reproducers/PQD-0011/rf_time_range.seq`](../reproducers/PQD-0011/rf_time_range.seq):
an RF event of 2 samples at the times `0` and `3e9` (RF raster 1 µs, so 3000
s), in a block of 3000 s:

```
shape_id 3
num_samples 2
0
3e9
```

Commands as in PQD-0001.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Samples at 0 and 3000 s. | — |
| C++ reader | — | Plain build: no end in 10 s (killed). Sanitized: "runtime error: 3e+09 is outside the range of representable values of type 'int'" at `ExternalSequence.cpp:2031` (exit 3). 2026-10-13. |
| MATLAB Pulseq | — | Read; `rf.t` 0 and 3000 s. 2026-10-13. |
| pypulseq | — | Read. 2026-10-13. |

## Impact

No real pulse lasts 3000 s, so the condition comes from a damaged or
malicious file (pulseq-analysis found it by fuzzing). It makes the scanner's
reader behave in an undefined way, or spend its time and memory on billions
of cells, where both toolboxes read the file.

## Suggested resolution

The C++ reader: before the conversion, check that the last time is finite,
not negative, and below a bound (for example the block's duration in RF
rasters), and reject the file otherwise.

## Report

Draft, to pulseq/pulseq:

> **C++ reader: an RF time shape with a very large last time**
>
> `decodeBlock` converts the last time of a resampled RF time shape with
> `int(0.5+waveform_t.back())` (`ExternalSequence.cpp:2031`). For a time
> above `INT_MAX` RF rasters (the attached file has 3e9) the conversion is
> undefined; UBSan reports it, and a release build does not end in 10 s.
> Could the reader check the range first? MATLAB Pulseq and pypulseq read the
> file.

## History

- 2026-10-12: found by pulseq-analysis by fuzzing (D5.9, commit `5bd053a`).
- 2026-10-13: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq (a 1.5.1 file).
