---
id: DIS-0036
title: An extended trapezoid time that is not a whole µs
kind: spec-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "the time shape is in units of GradientRasterTime, which can be any time in seconds"
  - key: cpp-reader
    behavior: "rounds each time of an extended trapezoid to a whole µs"
  - key: matlab-pulseq
    behavior: "keeps the times of the shape; writes a 2.5 µs raster"
  - key: pypulseq
    behavior: "keeps the times of the shape; writes a 2.5 µs raster"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq, pypulseq]
  reason: "Both writers write a gradient raster of 2.5 us with an extended trapezoid (opts gradRasterTime, makeExtendedTrapezoid). The C++ reader rounds each vertex time to a whole us."
found: 2026-10-12
checked: 2026-10-14
---

# DIS-0036: An extended trapezoid time that is not a whole µs

## Summary

The time shape of an extended trapezoid gives its times in units of
`GradientRasterTime`. The C++ reader converts each time to a whole µs, so a
time that is not a whole µs moves by up to 0.5 µs. Such times come from a
gradient raster that is not a whole µs (the specification does not forbid
one, and both writers write one), or from a vertex between raster edges
(DIS-0035). MATLAB Pulseq and pypulseq keep the times of the file.

## What each source does

| Source | What it does |
|---|---|
| Specification | `GradientRasterTime` is the "Default raster time (dwell time) of the shaped gradient events, specified in seconds", with no constraint on its value (section 2.5, `spec:273`). The gradient `<time_id>` gives "the time sampling points, specified in the units of `GradientRasterTime`" (section 2.8.2, `spec:395`); gradients start and end on multiples of `GradientRasterTime` (section 2.6, `spec:290`). Slide 11 requires only that the gradient raster and `BlockDurationRaster` are integer multiples of each other. |
| C++ reader | Reads `GradientRasterTime` as `1e6*def[0]` µs (`cpp:1488`). In `decodeExtTrapGradInBlock`, each time of the shape becomes `long(0.5 + m_dGradientRasterTime_us * t)` (`cpp:2182`), a whole µs, kept as `std::vector<long>` (`cpp.h:683`); `gradientsAt` draws its lines between those times (`cpp:3611-3651`). |
| MATLAB Pulseq | The times are the decompressed shape times `GradientRasterTime` (`Sequence.m:1396`), as doubles. `mr.opts('gradRasterTime', 2.5e-6, …)` and `makeExtendedTrapezoid` write a file with `GradientRasterTime 2.5e-06` and a time shape `0 1 3 4` (run). |
| pypulseq | The times are the decompressed shape times `grad_raster_time` (`block.py:434`). `Opts(grad_raster_time=2.5e-6, …)` and `make_extended_trapezoid` write the same file (run). |

## Reproducer

In [`reproducers/DIS-0036/`](../reproducers/DIS-0036/):

- `matlab_raster_2p5us.seq` and `pypulseq_raster_2p5us.seq`: written by
  `make_raster_2p5us.m` (MATLAB Pulseq under Octave 11.3.0) and
  `make_raster_2p5us.py` (pypulseq 1.5.0.post1; master `c977214` writes the
  same file): `GradientRasterTime 2.5e-06`, `BlockDurationRaster 1e-05`, one
  block of 10 µs, an extended trapezoid of amplitude 1000 Hz/m, amplitude
  shape `0 1 1 0`, time shape `0 1 3 4` (0, 2.5, 7.5, 10 µs). Every vertex is
  on the gradient raster.
- `vertex_12p5us.seq` (hand-written): a 10 µs raster, amplitude 100000 Hz/m,
  shape `0 1 0`, time shape `0 1.25 3`: the inner vertex at 12.5 µs, off the
  raster (DIS-0035).

Commands as in DIS-0001; the C++ times from `pulseq-cpp-oracle --dump`, its
values from `printf '0 2.5\n0 8\n0 9\n' | pulseq-cpp-oracle --sample FILE`.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Raster files: vertices at 0, 2.5, 7.5, 10 µs; 1000, 800, 400 Hz/m at 2.5, 8, 9 µs. `vertex_12p5us.seq`: vertex at 12.5 µs, 100000 Hz/m there. | — |
| C++ reader | — | Raster files (both): read (exit 0; sanitized exit 0), `times_us` `[0, 3, 8, 10]`; `--sample` 833.3, 1000, 500 Hz/m at 2.5, 8, 9 µs. `vertex_12p5us.seq`: `times_us` `[0, 13, 30]`; 96154 Hz/m at 12.5 µs, 100000 at 13 µs. 2026-10-14. |
| MATLAB Pulseq | — | Raster files: `tt` 0, 2.5, 7.5, 10 µs; `waveforms_and_times` the same points. `vertex_12p5us.seq`: `tt` 0, 12.5, 30 µs. 2026-10-14. |
| pypulseq | — | 1.5.0.post1 and master: as MATLAB Pulseq. 2026-10-14. |

## Impact

A sequence written with a gradient raster that is not a whole µs (for a
system whose gradient raster is not a whole µs) plays its extended trapezoids
with vertices moved by up to 0.5 µs on the scanner's reader, and with the
times of the file in MATLAB Pulseq and pypulseq (and in their simulations and
checks). With the Siemens raster of 10 µs and vertices on the raster, every
time is a whole µs and nothing moves. The same C++ reader rejects an
arbitrary gradient on a raster other than 10 µs (`cpp:2115-2121`, DIS-0061),
but not an extended trapezoid.

## Suggested resolution

The C++ reader: keep the times of an extended trapezoid as `double` µs (or
in a finer unit), or reject a time that is not a whole µs. The
specification could state the resolution of a gradient time, if the
interpreters need one.

## Report

Draft, to pulseq/pulseq:

> **C++ reader: the times of an extended trapezoid are rounded to whole µs**
>
> `decodeExtTrapGradInBlock` converts each time of the time shape to
> `long(0.5 + m_dGradientRasterTime_us * t)` (`ExternalSequence.cpp:2182`).
> With `GradientRasterTime 2.5e-06`, which MATLAB Pulseq and pypulseq both
> write for `makeExtendedTrapezoid` with `gradRasterTime 2.5e-6`, the vertices
> at 2.5 and 7.5 µs are played at 3 and 8 µs: `gradientsAt` gives 833 Hz/m at
> 2.5 µs where the file has 1000. Files attached. Could the times be kept as
> floating point, or such a file be rejected?

## History

- 2026-10-12: found by pulseq-analysis (section 4 of `docs/discrepancies.md`,
  S4-1, commit `49a7e2c`; "It was not run"). No ID there, so the record has
  no `pulseq_analysis` field.
- 2026-10-14: run for the first time. Files written by MATLAB Pulseq (Octave
  11.3.0) and pypulseq with a 2.5 µs gradient raster, and a hand-written file
  with a vertex at 12.5 µs; all run in the C++ reader (plain, sanitized, and
  `--sample`), MATLAB Pulseq and pypulseq. Confirmed against the pinned
  sources. Kind and severity as in the inventory.
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, the two pins of `sources.yaml`;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, which are the same on master.
