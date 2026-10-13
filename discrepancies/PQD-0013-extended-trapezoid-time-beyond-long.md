---
id: PQD-0013
title: An extended trapezoid time that does not fit a long
kind: spec-gap
severity: crash
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "no bound on the times of a gradient time shape"
  - key: cpp-reader
    behavior: "converts each time to long µs, which is undefined behaviour above LONG_MAX"
  - key: matlab-pulseq
    behavior: "reads the times as written"
  - key: pypulseq
    behavior: "reads the times as written"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D5.11]
  commit: 5bd053a
found: 2026-10-12
checked: 2026-10-13
---

# PQD-0013: An extended trapezoid time that does not fit a long

## Summary

The specification sets no bound on the times of a gradient time shape. MATLAB
Pulseq and pypulseq read an extended trapezoid with a time of 1e18 gradient
rasters. The C++ reader converts each time to a `long` number of µs; above
`LONG_MAX` the conversion is undefined behaviour.

## What each source does

| Source | What it does |
|---|---|
| Specification | The `<time_id>` of a `[GRADIENTS]` row gives "the time sampling points, specified in the units of `GradientRasterTime`" (section 2.8.2, `spec:395`); shape samples are 32-bit floats (`spec:176`). No bound. |
| C++ reader | `first[i]=long(0.5+m_dGradientRasterTime_us*waveform[i])` for each time (`cpp:2181-2182`): with a raster of 10 µs, a time of 1e18 rasters is 1e19 µs, above `LONG_MAX` (about 9.22e18 on a 64-bit system), and the conversion is undefined behaviour. |
| MATLAB Pulseq | Reads the times as written (run: `tt` 0, 10 µs and 1e13 s). |
| pypulseq | Reads the file (run). |

## Reproducer

[`reproducers/PQD-0013/ext_trap_time_range.seq`](../reproducers/PQD-0013/ext_trap_time_range.seq):
one block with the gradient `1 100000 0 0 3 4 0`, whose amplitude shape 3 is
`0 1 0` and time shape 4 is

```
shape_id 4
num_samples 3
0
1
1e18
```

Commands as in PQD-0001.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Points at 0, 10 µs and 1e19 µs. | — |
| C++ reader | — | Plain build: read (exit 0). Sanitized: "runtime error: 1e+19 is outside the range of representable values of type 'long'" at `ExternalSequence.cpp:2182` (exit 3). 2026-10-13. |
| MATLAB Pulseq | — | Read. 2026-10-13. |
| pypulseq | — | Read. 2026-10-13. |

## Impact

No real gradient lasts 1e13 s, so the condition comes from a damaged or
malicious file (pulseq-analysis found it by fuzzing). The scanner's reader
then holds a time that depends on the build; both toolboxes read the file.
The event is also far longer than its block, which no reader checks here.

## Suggested resolution

The C++ reader: check that each time is finite and within the block (or
within a bound) before the conversion at `cpp:2182`, and reject the file
otherwise.

## Report

Draft, to pulseq/pulseq:

> **C++ reader: an extended trapezoid time that does not fit a `long`**
>
> `decodeExtTrapGradInBlock` converts each time with
> `long(0.5+m_dGradientRasterTime_us*waveform[i])`
> (`ExternalSequence.cpp:2182`). For a time of 1e18 gradient rasters (the
> attached file) the value is 1e19 µs, and the conversion is undefined; UBSan
> reports it. Could the reader check the range first? MATLAB Pulseq and
> pypulseq read the file.

## History

- 2026-10-12: found by pulseq-analysis by fuzzing (D5.11, commit `5bd053a`).
- 2026-10-13: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq (a 1.5.1 file).
- 2026-10-13: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, not at the fork that `sources.yaml` pins;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
