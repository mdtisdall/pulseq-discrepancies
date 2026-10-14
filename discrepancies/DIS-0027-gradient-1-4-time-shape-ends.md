---
id: DIS-0027
title: A 1.4 arbitrary gradient with a time shape (no first column)
kind: spec-gap
severity: playback
status: confirmed
format_versions: ["1.4.x"]
sources:
  - key: spec
    behavior: "gives only the 1.5 row with first and last; silent on the ends of a 1.4 gradient"
  - key: cpp-reader
    behavior: "plays the samples from the first to the last time, the first segment carried back to the start; 0 after the last time"
  - key: matlab-pulseq
    behavior: "first from the block before (else 0); last = the last sample, held to the end of the last cell"
  - key: pypulseq
    behavior: "first and last as MATLAB Pulseq; joins them to the samples with lines"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
pulseq_analysis:
  ids: [D4.5]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0027: A 1.4 arbitrary gradient with a time shape (no first column)

## Summary

A 1.4 `[GRADIENTS]` row has no `first` and `last`. When the time shape of the
gradient starts at 0 and ends at the end of the event, the samples give the
two ends, and the readers agree. When it does not, as for the short arbitrary
gradients that MATLAB Pulseq and pypulseq write with a time shape `0.5 1.5
2.5`, the file does not give the ends, the specification is silent, and the
readers play different waveforms: the C++ reader extends the first segment
back to the start and plays 0 after the last time; MATLAB Pulseq and pypulseq
start from the gradient of the block before (or 0) and hold the last sample to
the end of the last cell.

## What each source does

| Source | What it does |
|---|---|
| Specification | Gives only the 1.5 row with `first` and `last`, "the amplitude of the gradient at the start" and "at the end" (section 2.8.2, `spec:375-377`, `spec:392-393`), not the 1.4 row. A time shape gives the sample times in units of `GradientRasterTime` (`spec:394`); its points are "(typically) on raster edges, but this is not a requirement" (slide 4). The vertices of an extended trapezoid are on raster edges (slide 6). |
| C++ reader | Sets `first` and `last` of a 1.4 row to `FLOAT_UNDEFINED` (`cpp:1078-1086`). A gradient with a time shape is an extended trapezoid in any version (`cpp.h:698`); its times are rounded to µs (`cpp:2182`), and `gradientsAt` never reads `first` or `last` (`cpp:3611-3651`): from the delay to the first time it extends the first segment backwards (the binary search, `cpp:3638-3649`), and after the last time it gives 0 (`cpp:3621-3625`). |
| MATLAB Pulseq | In the second pass of `read` (`read.m:323-391`), `first` is the `last` of the gradient of the block before on the same axis when that one ends at the end of its block and this one has no delay, else 0 (`read.m:344-350`, `read.m:365-368`); for a time shape, `last` is the last sample, and the gradient ends at its last time (`read.m:352-354`). `waveforms_and_times` treats a gradient whose times are the cell centres as one of time ID 0, whatever its time ID (`Sequence.m:2009-2010`), and restores the cell edges from `first` and `last` (`Sequence.m:2018`, `restoreAdditionalShapeSamples.m:10-27`; DIS-0029); when the restored end differs from `last` it joins `first`, the samples and `last` at the end of the last cell (`restoreAdditionalShapeSamples.m:14-27`). |
| pypulseq | `first` and `last` as MATLAB Pulseq (`read_seq.py:370-383`, `read_seq.py:390-396`). `waveforms` joins `first`, the samples and `last` (half a raster after the last sample) with lines, for a gradient whose times are the cell centres (`sequence.py:1582-1604`; `:1645-1667` on master). |

Both writers write such a gradient: an arbitrary gradient of 4 samples or fewer
is not compressed (`compressShape.m:20`, `compress_shape.py:30`), so its time
shape is not the `0.5 1 1 N-3` that gives time ID 0, and it is written as a
time shape (`Sequence.m:673-684`; `block.py:698-708`); `write_v141.m:93-95`
and `write_seq.py:400-410` then drop `first` and `last`.

## Reproducer

[`reproducers/DIS-0027/time_shape_v141.seq`](../reproducers/DIS-0027/),
written by MATLAB Pulseq under Octave 11.3.0 (`seq.write_v141`), gradient
raster 10 µs: two blocks of 30 µs on x, each a 3-sample
`mr.makeArbitraryGrad`: block 1 the samples 50000, 100000, 100000 Hz/m
(`first` 0, `last` 100000: a ramp to a plateau), block 2 the samples 100000,
100000, 50000 (`first` 100000, `last` 0). pypulseq 1.5.0.post1 and master
write the same sections with `v141_compat=True` (run).

```
[GRADIENTS]
1       100000 1 2 0
2       100000 3 2 0
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
| Specification | No value at 0 µs and from 25 to 30 µs of either block (the samples are at 5, 15 and 25 µs). | — |
| C++ reader | — | Times 5, 15, 25 µs (`--dump`). Block 1 at 0, 2.5, 27.5, 30 µs: 25000, 37500, 0, 0. Block 2 at 0, 25, 27.5, 30 µs: 100000, 50000, 0, 0. 2026-10-14. |
| MATLAB Pulseq | — | `getBlock`: block 1 `first` 0, `last` 100000; block 2 `first` 0 (block 1 ends at 25 µs, before the end of its block), `last` 50000. Block 1 at 0, 2.5, 27.5, 30 µs: 0, 25000, 100000, 100000. Block 2 at 25, 27.5, 30 µs: 50000, 50000, 50000 (then the sequence ends). 2026-10-14. |
| pypulseq | — | `first` and `last` as MATLAB Pulseq. Block 1 at 0, 2.5, 27.5, 30 µs: 0, 25000, 100000, 100000; block 2 at 27.5, 30 µs: 50000, 50000. 2026-10-14. |

At the start of block 2, both toolboxes' polylines keep the point of block 1
at 30 µs (100000) and drop block 2's `first` of 0 at the same time
(`Sequence.m:2136-2145`; `sequence.py:1683-1689`, `:1746-1752` on master), so
they play 100000 there, as the C++ reader does.

## Impact

1.4 files with short arbitrary gradients (1 to 4 samples) written by MATLAB
Pulseq or pypulseq, and any 1.4 time shape that does not start at 0 or does
not end at the end of the event. The scanner's reader plays a value at the
start that the toolboxes do not (25000 against 0 Hz/m here), and 0 in the
last half raster where the toolboxes hold the last sample (100000 Hz/m in
block 1): the gradient moment differs.

## Suggested resolution

The specification: give the 1.4 row of `[GRADIENTS]`, and say what a reader
takes at the start and at the end of a 1.4 gradient with a time shape that
does not cover the whole event (for example, as DIS-0026 asks for time ID 0).
The C++ reader's handling of a time shape that does not start at 0 or end at
the end of the event, in any version, is DIS-0028.

## Report

Draft, to pulseq/pulseq (specification):

> **The ends of a gradient with a time shape in a 1.4 file**
>
> MATLAB Pulseq and pypulseq write an arbitrary gradient of 4 samples or
> fewer with a time shape (`0.5 1.5 2.5` for 3 samples). In a 1.4 file
> (`write_v141`) the row has no `first` and `last`, so the file does not give
> the gradient between 0 and 5 µs and between 25 and 30 µs. The readers play
> different values there: for the attached file, `ExternalSequence` gives
> 25000 Hz/m at 0 µs (the first segment carried back) and 0 after 25 µs;
> MATLAB Pulseq and pypulseq give 0 at 0 µs and hold 100000 Hz/m to 30 µs.
> Could the specification give the 1.4 row and say what the ends are?

## History

- 2026-10-09: found by pulseq-analysis (old ID D40, commit `49a7e2c`; D4.5,
  `5bd053a`).
- 2026-10-14: confirmed against the pinned sources; the reproducer written by
  MATLAB Pulseq under Octave 11.3.0 (pypulseq writes the same sections), and
  run in the C++ reader (plain and sanitized: both exit 0), MATLAB Pulseq and
  pypulseq, with the values sampled at the same times.
- 2026-10-14: `report_to` is the specification only (the inventory also had
  the C++ reader): the C++ reader plays a time shape the same way in 1.4 and
  1.5 files, and DIS-0028 reports that.
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq; the two behave the same here, and the
  citations give the lines of 1.5.0.post1, with those of master where they
  differ.
