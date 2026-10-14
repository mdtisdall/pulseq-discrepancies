---
id: DIS-0061
title: An arbitrary gradient on a gradient raster other than 10 µs
kind: spec-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "GradientRasterTime is any raster, given in the file"
  - key: cpp-reader
    behavior: "decodeBlock fails for an arbitrary gradient when the raster is not 10 µs"
  - key: matlab-pulseq
    behavior: "reads and plays it on the raster of the file"
  - key: pypulseq
    behavior: "reads and plays it on the raster of the file"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq, pypulseq]
  reason: "Both writers write an arbitrary gradient on a user-chosen raster such as 5 µs. The C++ reader cannot decode the block of this spec-valid file and rejects it."
pulseq_analysis:
  ids: [D28]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0061: An arbitrary gradient on a gradient raster other than 10 µs

## Summary

The specification lets a file give its own `GradientRasterTime`. MATLAB
Pulseq and pypulseq read and play an arbitrary gradient (time ID 0) on a
raster of 5 µs. The C++ reader loads the file but fails to decode the block:
it decodes an arbitrary gradient only on a raster of 10 µs.

## What each source does

| Source | What it does |
|---|---|
| Specification | `GradientRasterTime` is the "Default raster time (dwell time) of the shaped gradient events, specified in seconds", a required definition with no fixed value (section 2.5, `spec:273`). The samples of an arbitrary gradient are at the centres of the raster cells (section 2.6, `spec:290`). |
| C++ reader | `decodeBlock` returns false for an arbitrary gradient when the raster of the file is not 10 µs: "Shape is on a raster that is different from the system raster, exitting…", with the note "TODO … we need 'first' and 'last' to be able to interpolate correctly" (`cpp:2115-2121`). Its sampling uses a fixed gradient raster of 10 µs (`SeqBlock::s_gradientRaster`, `cpp:90`). The message is printed at the debug level, so a plain run shows only that the block did not decode. |
| MATLAB Pulseq | Reads it, with the samples on the raster of the file (run). |
| pypulseq | Reads it, with the samples on the raster of the file (run). |

## Reproducer

Two 1.5.1 files in [`reproducers/DIS-0061/`](../reproducers/DIS-0061/), each
of one block with an arbitrary gradient of 10 samples on x:

- `arbitrary_gradient_5us_raster.seq`: `GradientRasterTime 5e-06`, a block of
  50 µs;
- `arbitrary_gradient_10us_raster.seq`: the same gradient with
  `GradientRasterTime 1e-05`, in a block of 100 µs (the control).

```
[DEFINITIONS]
AdcRasterTime 1e-07
BlockDurationRaster 1e-05
GradientRasterTime 5e-06
RadiofrequencyRasterTime 1e-06

[BLOCKS]
1 5 0 1 0 0 0 0

[GRADIENTS]
1 100000 0 0 1 0 0
```

Commands as in DIS-0001.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Both files are valid. | — |
| C++ reader | — | 5 µs: `decodeBlock returned false for block 0` (exit 1; sanitized exit 1). 10 µs: read (exit 0). 2026-10-14. |
| MATLAB Pulseq | — | Both read and played. 2026-10-14. |
| pypulseq | — | Both read and played. 2026-10-14. |

## Impact

A file for a system whose gradient raster is not 10 µs, written by MATLAB
Pulseq or pypulseq with arbitrary gradients, is played by both toolboxes and
cannot be decoded by this reader. The reader is that of the Siemens
interpreter, where the gradient raster is 10 µs (slide 7: "Gradient raster is
10 us on Siemens"), so the limit is of the reader, not of the format; the
user learns of it only at the scanner, and the message is at the debug level.

## Suggested resolution

The C++ reader: resample the gradient (the code's TODO), or reject the file at
`load` with a message at the error level that names the raster. Or the
specification says that an interpreter may support only some rasters, and
how it says so.

## Report

Draft, to pulseq/pulseq:

> **An arbitrary gradient on a raster other than 10 µs**
>
> The specification lets a file set `GradientRasterTime` (section 2.5).
> `ExternalSequence::decodeBlock` returns false for an arbitrary gradient when
> that raster is not 10 µs (`ExternalSequence.cpp:2115-2121`), and its message
> is printed at `DEBUG_LOW_LEVEL`. MATLAB Pulseq and pypulseq play the same
> file on its raster. Could the reader resample it (the TODO there), or at
> least reject the file at `load` with an error message? Reproducer attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D28, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here).
