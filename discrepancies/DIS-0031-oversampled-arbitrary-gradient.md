---
id: DIS-0031
title: An oversampled arbitrary gradient (time ID -1)
kind: spec-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "N samples half a gradient raster apart, alternating raster centres and edges, from a centre to a centre; first and last at the event's edges"
  - key: spec-slides
    behavior: "the same; first and last are not in the shape"
  - key: cpp-reader
    behavior: "default: plays only the centre samples; edge mode: the edge samples half a raster early; preserve mode: all samples one raster apart, cut at the block end"
  - key: matlab-pulseq
    behavior: "all samples at (1:N)/2 rasters, with first at 0 and last at (N + 1)/2 rasters"
  - key: pypulseq
    behavior: "read fails with KeyError: -1"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
pulseq_analysis:
  ids: [D6.1]
  commit: 5bd053a
found: 2026-09-24
checked: 2026-10-14
---

# DIS-0031: An oversampled arbitrary gradient (time ID -1)

## Summary

An arbitrary gradient with time ID -1 has N samples, half a gradient raster
apart: the specification puts them alternately on the raster centres and
edges, from a centre to a centre. MATLAB Pulseq plays all of them. The C++
reader, by default, keeps only the centre samples, and its two other modes
play the edge samples half a raster early, or all the samples one raster
apart (twice as long, cut at the block end). pypulseq does not read the file
(`KeyError: -1`).

## What each source does

| Source | What it does |
|---|---|
| Specification | `<time_id>`: "-1 means 1/2 of the default time raster (gradient oversampling case)" (section 2.8.2, `spec:395`). The shape "is defined with the oversampling (e.g. it contains N-1 additional points between the nominal samples sampled at the gradient raster cell edges)" (`spec:420`); the nominal samples are at the raster centres (section 2.6, `spec:290`). |
| Slide set | "Sampling time points alternate between the cell centers and cell edges with the sampling period being exactly 0.5 of default dwell time"; "The shape starts and ends at the cell centers; first and last points are not included into the shape vector" (slide 4). Slide 8: "First and last values are not stored as a part of the shape, but only in the “Grad” object"; its figure draws a sample on every raster centre and edge, joined by straight lines, from `Grad.first` at the start to `Grad.last` at the end. |
| C++ reader | `decodeArbGradInBlock`: in the default mode `ags_center` (`cpp:103`) it keeps `(N + 1)/2` samples, the first, third, ... stored sample (the centres); in the mode `ags_edge` (`SetArbGradCenterSampling(false)`, `cpp.h:978`) it keeps the `(N - 1)/2` edge samples; in `ags_preserve_oversampling` (`SetArbGradPreserveOversampling`, `cpp.h:989-992`) it keeps all `N` (`cpp:2123-2149`). The block keeps only the samples, no oversampling flag. `gradientsAt` places the kept samples at the raster centres, one gradient raster apart, with `first` at the start and `last` one raster after the last sample (`cpp:3661-3692`), and gives 0 after the block's duration (`cpp:3561-3566`). |
| MATLAB Pulseq | Writes time ID -1 for a gradient whose times compress to a half-raster step (`Sequence.m:678-681`), as `makeArbitraryGrad(..., 'oversampling', true)` makes them. `getBlock`: `tt = (1:N)/2 * gradRasterTime`, `shape_dur = (N + 1)/2 * gradRasterTime`, and an odd `N` is asserted (`Sequence.m:1384-1390`). `waveforms_and_times` adds `first` at 0 and `last` at `shape_dur` to all the samples (`Sequence.m:2026-2028`). |
| pypulseq | `read` calls `remove_duplicates(in_place=True)` (`read_seq.py:444`), which maps the time ID of each arbitrary gradient through the shape library's map of IDs: -1 is not in it, and it raises `KeyError` (`sequence.py:1167`; `:1199` on master). With the option `remove_duplicates=False` the file reads, but `waveforms` takes the event as an extended trapezoid and leaves out `first` and `last` (`sequence.py:1582-1583`, `:1605-1612`; `:1645-1646`, `:1668-1675` on master), and on 1.5.0.post1 `get_block` gives twice the `shape_dur` (`block.py:428`; fixed on master). |

## Reproducer

[`reproducers/DIS-0031/oversampled_zigzag.seq`](../reproducers/DIS-0031/oversampled_zigzag.seq),
written by MATLAB Pulseq under Octave 11.3.0 from

```matlab
sys = mr.opts();
g = mr.makeArbitraryGrad('x', 10000*[1 .5 1 .5 1 .5 1], sys, 'oversampling', true, 'first', 0, 'last', 0);
s = mr.Sequence(sys); s.addBlock(g); s.write('oversampled_zigzag.seq');
```

one block of 40 µs with the gradient

```
[GRADIENTS]
1        10000            0            0 1 -1 0
```

and the shape `1 0.5 1 0.5 1 0.5 1` (7 samples): 10000 Hz/m on the raster
centres, 5000 Hz/m on the edges.

Commands as in DIS-0001; the C++ values from `pulseq-cpp-oracle
[--oversampling=center|edge|preserve] --dump FILE` and `--sample FILE` (times
in the block, µs; `center` is the reader's default).

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification, slides | x: 0 at 0 µs (`first`); 10000 at 5, 15, 25, 35 µs; 5000 at 10, 20, 30 µs; 0 at 40 µs (`last`). | — |
| C++ reader, default (`center`) | — | Read (exit 0, sanitized exit 0). Samples `1 1 1 1`. x at 0, 2.5, 5, 7.5, 10, 15, 20, 25, 30, 35, 37.5, 40 µs: 0, 5000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 5000, 0: a constant 10000 Hz/m, no edge sample. 2026-10-14. |
| C++ reader, `edge` | — | Samples `0.5 0.5 0.5`. At the same times: 0, 2500, 5000, 5000, 5000, 5000, 5000, 5000, 0, 0, 0, 0: the edge samples at 5, 15, 25 µs (half a raster early), and 0 from 30 µs. 2026-10-14. |
| C++ reader, `preserve` | — | Samples `1 0.5 1 0.5 1 0.5 1`. At the same times: 0, 5000, 10000, 8750, 7500, 5000, 7500, 10000, 7500, 5000, 6250, 7500: the samples one raster apart (5, 15, …, 65 µs), cut at the block end (7500 Hz/m at 40 µs). 2026-10-14. |
| MATLAB Pulseq | — | Read. `getBlock` `tt` 5 to 35 µs in steps of 5 µs, `shape_dur` 40 µs. `waveforms_and_times` x: times 0, 5, 10, …, 40 µs; values 0, 10000, 5000, 10000, 5000, 10000, 5000, 10000, 0. 2026-10-14. |
| pypulseq | — | `read`: `KeyError(np.float64(-1.0))` in `remove_duplicates` (`sequence.py:1167` on 1.5.0.post1, `:1199` on master). With `read(..., remove_duplicates=False)`: `waveforms` x at 5 to 35 µs only (no `first`, no `last`); `get_block(1).gx.shape_dur` 80 µs on 1.5.0.post1, 40 µs on master. 2026-10-14. |

The same in a larger file written by MATLAB Pulseq: block 3 of
`tests/seqfiles/oracle/koma_v1.5_spiral.seq` of pulseq-analysis (`65fc7e8`)
has gradients of time ID -1; the C++ reader keeps 2112 samples in the mode
`center`, 2111 in `edge` and 4223 in `preserve` (run, 2026-10-14).

## Impact

MATLAB Pulseq writes time ID -1 for its oversampled gradients
(`makeArbitraryGrad(..., 'oversampling', true)`), for example spiral readouts. The scanner's reader, in
its default mode, plays only the centre samples: the gradient between them is
the line between two centres, not the edge sample; the result is the same only
where the gradient is linear across each raster cell. Which mode a scanner's
interpreter sets is not in the file, so the same file can play three ways, and
the two other modes are not the specification's waveform either. pypulseq
cannot read the file with its default options, so it cannot analyse a
sequence that MATLAB Pulseq writes and the scanner plays.

## Suggested resolution

The C++ reader: in the modes that keep the edge samples, place them on the
raster edges, and in `preserve` mode keep the half-raster step in
`gradientsAt`; or document that only the centre samples are played, and that
the edge samples are for checks only. pypulseq: in `remove_duplicates`, keep the
time IDs 0 and -1 as they are (P04's fix), and add `first` and `last` to an
oversampled gradient in `waveforms` (P03's fix).

## Report

Draft, to pulseq/pulseq (C++ reader):

> **The C++ reader and an oversampled arbitrary gradient (time ID -1)**
>
> For a gradient with time ID -1, the specification and the slide set define
> N samples, half a raster apart, alternating centres and edges (section
> 2.8.2, slide 4). `decodeArbGradInBlock` keeps only the centre samples by
> default, and `gradientsAt` places what it keeps on the raster centres, one
> raster apart (`ExternalSequence.cpp:2123-2149`, `:3661-3692`). With
> `SetArbGradCenterSampling(false)`, the edge samples are played half a raster
> early; with `SetArbGradPreserveOversampling()`, all samples are played one
> raster apart, so the gradient is twice as long and is cut at the block end.
> In the attached file (written by `mr.makeArbitraryGrad(...,
> 'oversampling', true)`), the centre samples are 10000 Hz/m and the edge
> samples 5000 Hz/m: the default mode plays a constant 10000 Hz/m. Is the
> default the intended waveform, and what should the other modes play?

To pulseq/pypulseq: P04 of mdtisdall/pypulseq-issues (`1de4a1d`, `KeyError:
-1` in `write` and `read`) and P03 (`waveforms` leaves out `first` and
`last`) are the drafts.

## History

- 2026-09-24: found (P03 and P04 of mdtisdall/pypulseq-issues, commit
  `e46c8c0`).
- 2026-10-12: in pulseq-analysis as D43 (commit `49a7e2c`; also its
  section 4 entry, S4-6); D6.1 at `5bd053a`.
- 2026-10-14: confirmed against the pinned sources: the reproducer written by
  MATLAB Pulseq under Octave 11.3.0 and run in the C++ reader (the three modes;
  plain and sanitized), MATLAB Pulseq and pypulseq (a 1.5.1 file).
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, the two pins of `sources.yaml`;
  `read` behaves the same in both, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
