---
id: DIS-0035
title: A vertex of a gradient time shape off the gradient raster (slide 6 against slide 4)
kind: spec-contradiction
severity: documentation
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec-slides
    behavior: "slide 6: the vertices of an extended trapezoid are all on raster edges; slide 4: the points of a time shape are on the edges only typically, not a requirement"
  - key: spec
    behavior: "the time shape is in units of GradientRasterTime; a gradient starts and ends on the raster; silent on the inner vertices"
  - key: cpp-reader
    behavior: "reads the vertex at its time (rounded to a whole µs, DIS-0036)"
  - key: matlab-pulseq
    behavior: "reads the vertex at its time; its maker refuses such a vertex, but it writes a short arbitrary gradient as a time shape 0.5 1.5 2.5"
  - key: pypulseq
    behavior: "reads the vertex at its time; its maker refuses such a vertex, but it writes a short arbitrary gradient as a time shape 0.5 1.5 2.5"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
priority:
  level: low
  written_by: [matlab-pulseq, pypulseq]
  reason: "Both writers write a 3-sample arbitrary gradient with the time shape 0.5 1.5 2.5. Every reader reads the vertices at their times. Only the slides disagree with each other."
pulseq_analysis:
  ids: [D1.3]
  commit: 5bd053a
found: 2026-10-13
checked: 2026-10-14
---

# DIS-0035: A vertex of a gradient time shape off the gradient raster (slide 6 against slide 4)

## Summary

The slide set that the specification cites does not agree with itself on
the times of a gradient time shape. Slide 6 puts all the vertices of an
extended trapezoid on raster edges; slide 4 says that the points of a time
shape are on the edges only "typically", and that this is "not a
requirement". Both writers refuse such a vertex in their makers, but both
write a short arbitrary gradient as a time shape `0.5 1.5 2.5`, whose
vertices are all off the edges: a file that slide 6 forbids and slide 4
allows. Every reader reads and plays such a vertex at its time.

## What each source does

| Source | What it does |
|---|---|
| Slide set | Slide 6 ("Extended Trapezoid Gradient"): "Arbitrary number of vertices, all aligned on raster edges", "Implemented by providing time_shape_id". Slide 4 ("Shapes in Pulseq"), for shapes with explicit time vectors (`time_shape_id >= 1`): "Sampling points are (typically) on raster edges, but this is not a requirement". |
| Specification | The gradient `<time_id>` is the "Shape ID for the time sampling points, specified in the units of `GradientRasterTime`" (section 2.8.2, `spec:395`). "Gradient events may only start and end at time points which are multiple of `GradientRasterTime`" (section 2.6, `spec:290`), which constrains the first and last vertex, not the inner ones. Section 2.6 refers the reader to the slide set for the timing (`spec:290`). |
| C++ reader | Does not check the vertices. It converts each time of the shape to µs as `long(0.5 + raster_us * t)` (`cpp:2182`) and draws straight lines between the vertices (`gradientsAt`, `cpp:3611-3651`). A vertex off the raster at a whole µs is held as written (run); one between two µs is rounded (DIS-0036). |
| MATLAB Pulseq | Reads the time shape times `GradientRasterTime` (`Sequence.m:1396`), with no check. `makeExtendedTrapezoid` refuses a time off the raster ("All time points must be on a gradient raster", `makeExtendedTrapezoid.m:84-85`). But `registerGradEvent` writes a time shape for each gradient whose compressed times are not `0.5 1 1 N-3` or `0.5 0.5 N-2` (`Sequence.m:673-685`), and `compressShape` does not compress a shape of 4 samples or fewer (`compressShape.m:20`): an arbitrary gradient of 3 samples is written with the time shape `0.5 1.5 2.5` (run). |
| pypulseq | Reads the time shape times `GradientRasterTime` (`block.py:434`), with no check. `make_extended_trapezoid` refuses a time off the raster (`make_extended_trapezoid.py:115-118`). The registration of a gradient is the same as MATLAB's (`block.py:698-711`), and the same arbitrary gradient of 3 samples is written with the time shape `0.5 1.5 2.5` (run). |

## Reproducer

In [`reproducers/DIS-0035/`](../reproducers/DIS-0035/):

- `vertex_off_raster.seq` (hand-written): one extended trapezoid on a 10 µs
  gradient raster, amplitude shape `0 1 0`, time shape `0 1.5 3`: the inner
  vertex at 15 µs, a raster centre.
- `matlab_short_grad.seq` and `pypulseq_short_grad.seq`: written by
  `make_short_grad.m` (MATLAB Pulseq under Octave 11.3.0) and
  `make_short_grad.py` (pypulseq 1.5.0.post1; master `c977214` writes the same
  file) from an arbitrary gradient of 3 samples `[1000 2000 1000]` Hz/m on the
  default raster. Both files hold:

  ```
  [GRADIENTS]
  1         2000          500          500 1 2 0
  ...
  shape_id 2
  num_samples 3
  0.5
  1.5
  2.5
  ```

Commands as in DIS-0001, and `pulseq-cpp-oracle --dump` and `--sample` for
the times and values of the C++ reader.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Slide set | Slide 6: the three files are outside the format (vertices off the edges). Slide 4: valid, the vertices at their times. | — |
| C++ reader | — | All three read (exit 0; sanitized build exit 0). `vertex_off_raster.seq`: `times_us` `[0, 15, 30]`; `--sample` 66667, 100000, 66667 Hz/m at 10, 15, 20 µs. The two writer files: `times_us` `[5, 15, 25]`. 2026-10-14. |
| MATLAB Pulseq | — | All three read. `vertex_off_raster.seq`: `tt` 0, 15, 30 µs; `waveforms_and_times` points (0, 0), (15, 100000), (30, 0). The writer files: `tt` 5, 15, 25 µs. 2026-10-14. |
| pypulseq | — | 1.5.0.post1 and master: as MATLAB Pulseq, `tt` 0, 15, 30 µs and 5, 15, 25 µs. 2026-10-14. |

On the writer files the readers do not play the same waveform after the last
vertex: the C++ reader plays 0 from 25 to 30 µs (`--sample` at 27.5 µs: 0),
where MATLAB Pulseq and pypulseq ramp to `last` (500 Hz/m at 30 µs). That
difference is the C++ reader's use of `first` and `last` (DIS-0028), not the
position of the vertex.

## Impact

Whether a file with such a time shape is valid depends on which slide a tool
follows. A checker that follows slide 6 rejects every file in which MATLAB
Pulseq or pypulseq wrote an arbitrary gradient of 1 to 4 samples. The readers
all accept such a file and place the vertex at its time; the waveforms differ
only where DIS-0028 (the ends) or DIS-0036 (a time between two µs) applies.

## Suggested resolution

Make slide 6 and slide 4 agree, and state the rule in section 2.6 of the
specification. Either allow a vertex anywhere (slide 4; then say that the
times are rounded to a resolution, see DIS-0036), or require the vertices on
the raster edges (slide 6; then the writers must not write a short arbitrary
gradient as a time shape on the raster centres).

## Report

Draft, to pulseq/pulseq:

> **Slides 4 and 6: may a vertex of a gradient time shape be off the raster?**
>
> Slide 6 of `doc/pulseq_shapes_and_times.pdf` says that the vertices of an
> extended trapezoid are "all aligned on raster edges"; slide 4 says that the
> points of a shape with an explicit time vector are on the edges
> "(typically)", "but this is not a requirement". Section 2.6 of the
> specification refers to the slides and constrains only the start and end of
> a gradient. `makeExtendedTrapezoid` refuses a vertex off the raster, but
> `registerGradEvent` writes an arbitrary gradient of 4 samples or fewer with
> an uncompressed time shape `0.5 1.5 …` (vertices on the raster centres), and
> pypulseq does the same. Which rule holds? Could section 2.6 state it?

## History

- 2026-10-13: found by pulseq-analysis (old ID D26, commit `49a7e2c`, where
  the vertex is one case of a time off its raster; D1.3 at `5bd053a`).
- 2026-10-14: confirmed against the pinned sources; slides 4 and 6 read
  from the PDF at `c7469123`; the writer files written by MATLAB Pulseq
  (Octave 11.3.0) and pypulseq, and all files run in the C++ reader (plain
  and sanitized), MATLAB Pulseq and pypulseq (1.5.1 files). Severity changed
  from `playback` to `documentation`: every reader plays the vertex at its
  time; the waveform differences on these files belong to DIS-0028 and
  DIS-0036.
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, the two pins of `sources.yaml`;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, which are the same on master.
