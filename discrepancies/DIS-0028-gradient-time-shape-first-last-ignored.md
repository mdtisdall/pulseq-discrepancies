---
id: DIS-0028
title: A 1.5 arbitrary gradient with a time shape, whose first and last are not its end samples
kind: spec-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "first and last are the gradient at the start and the end of the event, also for extended trapezoids"
  - key: cpp-reader
    behavior: "never reads first or last of a time-shaped gradient: first segment carried back, 0 after the last time"
  - key: matlab-pulseq
    behavior: "plays first at the start and last at the end of the last cell"
  - key: pypulseq
    behavior: "plays first at the start and last at the end of the last cell"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq, pypulseq]
  reason: "Both writers write short arbitrary gradients with a time shape and with first and last. The spec says that first and last are the end values, and the C++ reader never reads them for a time shape."
found: 2026-10-13
checked: 2026-10-14
---

# DIS-0028: A 1.5 arbitrary gradient with a time shape, whose first and last are not its end samples

## Summary

In a 1.5 file, `first` and `last` of a `[GRADIENTS]` row are the gradient at
the start and at the end of the event, for shaped gradients and extended
trapezoids alike. The C++ reader takes every gradient with a time shape as an
extended trapezoid and never reads its `first` or `last`: before the first
time it carries the first segment back to the start, and after the last time
it plays 0. MATLAB Pulseq and pypulseq write short arbitrary gradients with a
time shape `0.5 1.5 2.5` and the right `first` and `last`, and play them; the
scanner's reader plays another start and drops to 0 half a raster early.

## What each source does

| Source | What it does |
|---|---|
| Specification | `<first>` is "the amplitude of the gradient at the start of the gradient. Only relevant for the arbitrary gradients (shaped gradients and extended trapezoids)", `<last>` the amplitude at the end (section 2.8.2, `spec:392-393`). A time shape gives the sample times in units of `GradientRasterTime` (`spec:394`), "(typically) on raster edges, but this is not a requirement" (slide 4). Gradient events start and end on raster edges (`spec:290`). |
| C++ reader | Reads `first` and `last` of a 1.5 row (`cpp:1070-1076`). A gradient with a time shape is an extended trapezoid (`cpp.h:698`), its times rounded to µs (`cpp:2182`), and its duration is its last time (`cpp:1954`). `gradientsAt` for it (`cpp:3611-3651`) does not read `first` or `last`: it gives 0 after the last time (`cpp:3621-3625`), and before the first time the binary search extrapolates the first segment back to the delay (`cpp:3638-3649`). Only time ID 0 and -1 use `first` and `last` (`cpp:3679-3688`). |
| MATLAB Pulseq | `getBlock` keeps `first` and `last` (`Sequence.m:1409-1410`). `waveforms_and_times` treats a gradient whose times are the cell centres as one of time ID 0, whatever its time ID (`Sequence.m:2009-2010`), and builds it from `first`, the samples and `last` with the restoration of DIS-0029 (`Sequence.m:2018`, `restoreAdditionalShapeSamples.m:10-44`): `first` at the start, `last` at the end of the last cell. |
| pypulseq | `get_block` keeps `first` and `last` (`block.py:446-447`). `waveforms` joins `first` at the start, the samples, and `last` half a raster after the last sample, with lines, for a gradient whose times are the cell centres (`sequence.py:1582-1604`; `:1645-1667` on master). |

Both writers write such a gradient: an arbitrary gradient of 4 samples or
fewer is not compressed (`compressShape.m:20`, `compress_shape.py:30`), so its
time shape is not the `0.5 1 1 N-3` that gives time ID 0, and it is written
as an uncompressed time shape, with `first` and `last` (`Sequence.m:669-687`;
`block.py:698-713`).

## Reproducer

[`reproducers/DIS-0028/time_shape_v151.seq`](../reproducers/DIS-0028/),
written by MATLAB Pulseq under Octave 11.3.0 (`seq.write`), gradient raster
10 µs: two blocks of 30 µs on x, each a 3-sample `mr.makeArbitraryGrad`: block
1 the samples 50000, 100000, 100000 Hz/m with `first` 0 and `last` 100000 (a
ramp to a plateau), block 2 the samples 100000, 100000, 50000 with `first`
100000 and `last` 0. pypulseq 1.5.0.post1 and master write the same
`[GRADIENTS]` and `[SHAPES]` (run; their files say revision 1.5.0).

```
[GRADIENTS]
1       100000            0       100000 1 2 0
2       100000       100000            0 3 2 0
...
shape_id 2
num_samples 3
0.5
1.5
2.5
```

Commands as in DIS-0026 (C++ `gradientsAt` by `pulseq-cpp-oracle --sample`;
the polylines of `waveforms_and_times` of MATLAB Pulseq and pypulseq,
interpolated at the same times). Hz/m, gx.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Block 1: 0 at 0 µs, 100000 at 30 µs. Block 2: 100000 at 0 µs, 0 at 30 µs. | — |
| C++ reader | — | Times 5, 15, 25 µs (`--dump`). Block 1 at 0, 2.5, 27.5, 30 µs: 25000, 37500, 0, 0. Block 2 at 0, 27.5, 30 µs: 100000, 0, 0. 2026-10-14. |
| MATLAB Pulseq | — | Block 1 at 0, 2.5, 27.5, 30 µs: 0, 25000, 100000, 100000. Block 2 at 0, 27.5, 30 µs: 100000, 25000, 0. 2026-10-14. |
| pypulseq | — | As MATLAB Pulseq at these times (between the samples see DIS-0029: at 10 µs of block 1, 75000 against MATLAB's 100000). 2026-10-14. |

## Impact

Every arbitrary gradient of 1 to 4 samples on the default raster that MATLAB
Pulseq or pypulseq writes is played by the scanner's reader without its `first`
and `last`: here the ramp of block 1 starts at 25000 Hz/m in place of 0, and
the plateau drops to 0 for the last 5 µs of block 1 and the ramp down of block
2 for its last 5 µs. The same holds for any time shape that does not start at
0 or end at the end of the event. The gradient moment differs from what the
toolboxes compute.

## Suggested resolution

The C++ reader: in `gradientsAt` (and in `gradMomentsAt`, which integrates
such a gradient only from its first to its last time, `cpp:3751-3775`), for a
gradient with a time shape, join
`first` at the delay to the first sample when the first time is after 0, and
the last sample to `last` at the end of the event when the last time is
before it; take the end of the event as the last time rounded up to the
raster, as MATLAB Pulseq does for the block duration (`Sequence.m:861`).

## Report

Draft, to pulseq/pulseq (C++ reader):

> **`gradientsAt` does not use `first` and `last` of a gradient with a time shape**
>
> MATLAB Pulseq and pypulseq write an arbitrary gradient of 4 samples or fewer
> with an uncompressed time shape (`0.5 1.5 2.5` for 3 samples) and with
> `first` and `last`. `SeqBlock::gradientsAt` takes it as an extended
> trapezoid (`isExtTrapGradient`, `ExternalSequence.h:698`) and never reads
> `first` or `last` (`ExternalSequence.cpp:3611-3651`): it extrapolates the
> first segment back to the delay, and returns 0 after the last time. For the
> attached file (a 3-sample ramp to a plateau, `first` 0, `last` 100000 Hz/m)
> it gives 25000 Hz/m at 0 µs and 0 from 25 to 30 µs, where the specification
> (`first`/`last`, section 2.8.2) and both toolboxes give 0 and 100000 Hz/m.

## History

- 2026-10-13: found by pulseq-analysis (`docs/findings-for-pulseq-checks.md`
  lines 281-289, F-281, commit `5bd053a`, the file that pypulseq writes for
  `gap_sequences.short_arbitrary_sequence`); no ID of `docs/discrepancies.md`
  (D4.5, `5bd053a`, gives the same C++ code path for 1.4 files: DIS-0027).
- 2026-10-14: confirmed against the pinned sources; the reproducer written by
  MATLAB Pulseq under Octave 11.3.0 (pypulseq writes the same sections), and
  run in the C++ reader (plain and sanitized: both exit 0), MATLAB Pulseq and
  pypulseq, with the values sampled at the same times.
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq; the two behave the same here, and the
  citations give the lines of 1.5.0.post1, with those of master where they
  differ.
