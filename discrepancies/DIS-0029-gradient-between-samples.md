---
id: DIS-0029
title: An arbitrary gradient on the default raster (time ID 0), between its samples
kind: spec-gap
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "samples at the centres of the raster cells; silent between them"
  - key: spec-slides
    behavior: "slide 7 draws a sampled trapezoid with its corners on the raster edges"
  - key: cpp-reader
    behavior: "straight lines between the samples, and to first and last at the ends"
  - key: matlab-pulseq
    behavior: "restores values on the raster edges by an alternating sum from first; lines between the edges"
  - key: pypulseq
    behavior: "straight lines between the samples, and to first and last at the ends"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
pulseq_analysis:
  ids: [D2.13]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0029: An arbitrary gradient on the default raster (time ID 0), between its samples

## Summary

The samples of an arbitrary gradient of time ID 0 are at the centres of the
raster cells, and the specification does not say what the gradient is
between them. The C++ reader and pypulseq join the samples with straight
lines. MATLAB Pulseq computes values on the raster edges by an alternating
sum from `first`, so that each sample is the mean of its two edges, and joins
the edges: a sampled trapezoid then gets its corners back on the raster
edges, as slide 7 draws it, but a smooth shape gets a zigzag that goes 15 %
above the amplitude of the event. The three implementations give different
waveforms for the same file.

## What each source does

| Source | What it does |
|---|---|
| Specification | The default sampling points of an arbitrary gradient are at the centres of the raster cells, `t_n = t_start + Δt (0.5 + n)` (section 2.6, `spec:290`); the time ID 0 "means default time raster" (section 2.8.2, `spec:394`), and `<amp>` is the "peak amplitude" (`spec:391`). It does not say what the gradient is between the samples. |
| Slide set | Slide 4: the samples of time ID 0 are at the cell centres, `([1:N] - 0.5) * raster_step`. Slide 7 ("Gradient with a Regularly-Sampled Shape") draws a trapezoid sampled at the cell centres, with the corners of its line on raster edges, not on the samples, and "non-zero start/end values are allowed". It does not state a rule. |
| C++ reader | `gradientsAt` interpolates linearly between two neighbouring samples, from `first` at the start of the event to the first sample, and from the last sample to `last` at the end (`cpp:3653-3693`). |
| MATLAB Pulseq | `waveforms_and_times` takes a gradient whose times are the cell centres (`Sequence.m:2009-2010`) through `restoreAdditionalShapeSamples` (`Sequence.m:2018`): the edge values are `e[0] = first`, `e[k+1] = 2 w[k] - e[k]` (`restoreAdditionalShapeSamples.m:10-12`); where an edge value differs from the mean of its two neighbouring samples by more than 2e-5 of the largest sample it is kept, else the mean is used (`restoreAdditionalShapeSamples.m:13`, `:30-31`), and the samples and edges are joined, without the points on straight segments (`restoreAdditionalShapeSamples.m:33-44`). When the last edge value differs from `last` by more than that tolerance, it warns and joins `first`, the samples and `last` instead (`restoreAdditionalShapeSamples.m:14-27`). |
| pypulseq | `waveforms` joins `first`, the samples and `last` with straight lines; the restoration is a `TODO` (`sequence.py:1582-1604`; `:1645-1667` on master). |

## Reproducer

[`reproducers/DIS-0029/between_samples.seq`](../reproducers/DIS-0029/),
written by MATLAB Pulseq under Octave 11.3.0 (`seq.write`, a 1.5.1 file),
gradient raster 10 µs: two blocks of 100 µs on x, each an
`mr.makeArbitraryGrad` of 10 samples with `first` 0 and `last` 0:

1. a trapezoid sampled at the cell centres: `[0.25 0.75 1 1 1 1 1 1 0.75 0.25]`
   times 100000 Hz/m (a ramp of 20 µs, a plateau, a ramp of 20 µs);
2. a half sine `sin(pi i / 9)`, `i = 0 … 9`, amplitude 98480.8 Hz/m (the shape
   of pulseq-analysis's `koma_v1.4_gr-uniformly-shaped.seq`).

Commands as in DIS-0026 (C++ `gradientsAt` by `pulseq-cpp-oracle --sample`;
the polylines of `waveforms_and_times` of MATLAB Pulseq and pypulseq,
interpolated at the same times). Hz/m, gx; all agree at the samples (5, 15,
… µs).

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | The samples at 5, 15, …, 95 µs; nothing between them. | — |
| C++ reader | — | Block 1 at 20 and 80 µs: 87500. Block 2 at 10, 20, 30, 40, 50 µs: 17101.0, 49240.4, 75440.7, 92541.7, 98480.8. 2026-10-14. |
| MATLAB Pulseq | — | Polyline of block 1: (0, 0), (20, 100000), (80, 100000), (100, 0) µs: 100000 at 20 and 80 µs. Block 2, on the edges 10 to 50 µs: 0, 68404.0, 60153.5, 113051.6, 83910.0 (a zigzag; 113051.6 is 15 % above the amplitude 98480.8). 2026-10-14. |
| pypulseq | — | As the C++ reader at every time above. 2026-10-14. |

The same rule makes MATLAB Pulseq differ from the others on a gradient with a
time shape whose times are the cell centres (DIS-0028: 100000 against 75000
Hz/m at 10 µs).

## Impact

Every sequence with arbitrary gradients on the default raster (spirals, EPI
ramps sampled by `makeArbitraryGrad`, gradients converted to shapes). The
scanner's reader plays straight lines between the samples; MATLAB Pulseq
computes the k-space trajectory, the moments, the slew rate and PNS from
another waveform. For a shape made from a trapezoid, MATLAB Pulseq's
waveform has the corners that the slide shows and the others cut them; for a
smooth shape, MATLAB Pulseq's waveform has edge values that the samples do not
suggest, above the amplitude of the event.

## Suggested resolution

The specification: state what the gradient is between the samples of time ID
0 (straight lines between the samples and to `first` and `last`, as the C++
reader and pypulseq play it, or the edge values of slide 7), and make slide 7
agree. MATLAB Pulseq: follow that rule in `waveforms_and_times`; if the
restoration stays, use it only when it gives a line that is straight between
the edges (a converted trapezoid), not for any shape that passes the
tolerance on `last`.

## Report

Draft, to pulseq/pulseq (specification and MATLAB Pulseq):

> **The gradient between the samples of an arbitrary gradient (time ID 0)**
>
> The specification puts the samples of time ID 0 at the cell centres
> (section 2.6) and does not say what the gradient is between them; slide 7
> of `pulseq_shapes_and_times.pdf` draws a sampled trapezoid with its corners
> on the raster edges. `ExternalSequence::gradientsAt` and pypulseq join the
> samples with straight lines. MATLAB Pulseq's `waveforms_and_times` restores
> edge values by an alternating sum from `first`
> (`restoreAdditionalShapeSamples.m`): for the attached file it gives the
> trapezoid's corners (100000 Hz/m at 20 µs, where the scanner's reader plays
> 87500), but for a half sine of 10 samples it gives the edges 0, 68404,
> 60153, 113052, 83910 Hz/m at 10 to 50 µs, while the samples rise smoothly
> and the event's amplitude is 98481 Hz/m. Could the specification state the
> rule, and MATLAB Pulseq compute the waveform the scanner plays?

## History

- 2026-10-09: found by pulseq-analysis (old ID D41, commit `49a7e2c`; D2.13,
  `5bd053a`).
- 2026-10-14: confirmed against the pinned sources; the reproducer written by
  MATLAB Pulseq under Octave 11.3.0, and run in the C++ reader (plain and
  sanitized: both exit 0), MATLAB Pulseq and pypulseq, with the values sampled
  at the same times.
- 2026-10-14: kind changed from `spec-vs-implementation` to `spec-gap`, and
  the specification added to `report_to`: the text of the specification is
  silent between the samples, and slide 7 draws the corners on the raster
  edges, as MATLAB Pulseq restores them for a trapezoid.
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq; the two behave the same here, and the
  citations give the lines of 1.5.0.post1, with those of master where they
  differ.
