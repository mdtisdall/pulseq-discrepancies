---
id: DIS-0032
title: "The area of an oversampled arbitrary gradient (time ID -1): MATLAB Pulseq counts only the raster-centre samples"
kind: spec-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "the gradient has a sample on every raster centre and edge, with first and last at its edges; no definition of an area"
  - key: spec-slides
    behavior: "draws the samples on centres and edges joined by straight lines, from Grad.first to Grad.last"
  - key: matlab-pulseq
    behavior: "area = sum of the centre samples * gradRasterTime; its own waveforms_and_times integrates to a different area"
  - key: cpp-reader
    behavior: "plays the centre samples (default); the area of what it plays is the waveform's, not MATLAB's, for a gradient linear across each raster cell"
  - key: pypulseq
    behavior: "the same formula as MATLAB in make_arbitrary_grad and get_block; read of the file fails (DIS-0031)"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
found: 2026-09-24
checked: 2026-10-14
---

# DIS-0032: The area of an oversampled arbitrary gradient (time ID -1): MATLAB Pulseq counts only the raster-centre samples

## Summary

For a gradient of time ID -1, MATLAB Pulseq's `area` (in `makeArbitraryGrad`
and in `getBlock` of a read file) is the sum of the samples on the raster
centres times the gradient raster. The edge samples, `first` and `last` do
not count. This is not the area of the waveform that the specification and
the slide set define, nor of the waveform that MATLAB's own
`waveforms_and_times` gives for the same file: 7.8553 1/m against 7.7595 1/m
(+1.2 %) for the reproducer. A gradient made to cancel `area` (a rephaser
with `-g.area`) leaves a moment that every reader plays.

## What each source does

| Source | What it does |
|---|---|
| Specification | Defines the samples of an oversampled gradient: the nominal samples at the raster centres (section 2.6, `spec:290`) and "N-1 additional points between the nominal samples sampled at the gradient raster cell edges" (section 2.8.2, `spec:420`); `<first>` and `<last>` are the amplitudes at the start and the end of the gradient (`spec:392-393`). It does not define an area. |
| Slide set | The samples alternate between centres and edges, and the shape starts and ends at the centres (slide 4). Slide 8 draws them on every centre and edge, joined by straight lines, from `Grad.first` at the start of the event to `Grad.last` at its end. |
| MATLAB Pulseq | `makeArbitraryGrad`: `grad.area=sum(grad.waveform(1:2:end))*system.gradRasterTime` for `'oversampling'` (`makeArbitraryGrad.m:88`). `getBlock` of a gradient of time ID -1 in a read file: the same (`Sequence.m:1390`). `waveforms_and_times` gives the gradient through `first`, all the samples and `last` (`Sequence.m:2026-2028`), whose area is different. `area` is not used elsewhere in `@Sequence`; it is what a sequence uses to size other gradients, for example `mr.makeTrapezoid(..., 'Area', -g.area)`. |
| C++ reader | Has no area of an event. In its default mode it plays the centre samples, with `first` and `last` at the event's edges (`cpp:2123-2147`, `cpp:3661-3692`; DIS-0031). |
| pypulseq | The same formula: `make_arbitrary_grad.py:119` and `block.py:429` (both versions). It does not read a file with time ID -1 (`KeyError`, DIS-0031). |

## Reproducer

[`reproducers/DIS-0032/oversampled_area_rephaser.seq`](../reproducers/DIS-0032/oversampled_area_rephaser.seq),
written by MATLAB Pulseq under Octave 11.3.0 from the triangle of P05 of
mdtisdall/pypulseq-issues and a rephaser of its `area`:

```matlab
sys = mr.opts('MaxSlew', 100, 'SlewUnit', 'T/m/s');
step = 0.9 * sys.maxSlew * sys.gradRasterTime / 2;  % 19159.2 Hz/m
g = mr.makeArbitraryGrad('x', step * [1:9, 8:-1:1], sys, 'oversampling', true, 'first', 0, 'last', 0);
r = mr.makeTrapezoid('x', sys, 'Area', -g.area);
s = mr.Sequence(sys); s.addBlock(g); s.addBlock(r); s.write('oversampled_area_rephaser.seq');
```

Block 1 (90 µs): a triangle of 17 samples, 0 to 172433 Hz/m and back,
`first` and `last` 0. Block 2 (100 µs): the trapezoid `-157105 50 0 50 0`
(area -7.85525 1/m). The waveform of block 1 is linear across each raster
cell except the one of its peak, so the waveforms of the specification and of
the C++ reader's default mode are the same triangle.

Commands as in DIS-0001. The areas of the C++ reader: the trapezoid rule on
`pulseq-cpp-oracle --sample` at a step of 0.05 µs over each block; of MATLAB's
`waveforms_and_times` and of the specification's waveform (straight lines
through `first`, the 17 samples and `last`, as slide 8 draws it): the
trapezoid rule on the points.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification, slides | Area of block 1: 7.7595 1/m (the triangle, 0.5 × 90 µs × 172432.8 Hz/m); with the rephaser, a moment of -0.0958 1/m at the end of block 2. | — |
| MATLAB Pulseq | — | `getBlock(1).gx.area` 7.85528 1/m (+1.2 %), `getBlock(2).gx.area` -7.85525 1/m: the two cancel to 3e-5 1/m. `waveforms_and_times` of the same file: area of block 1 7.75949 1/m (19 points), moment at the end of block 2 -0.09577 1/m. `makeArbitraryGrad` gave `g.area` 7.855272 before the write. 2026-10-14. |
| C++ reader | — | Read (exit 0, sanitized exit 0). Default mode (`center`): area of block 1 7.75948 1/m, block 2 -7.85525 1/m, moment -0.09577 1/m. Modes `edge` and `preserve` (DIS-0031): -0.38315 and +0.69455 1/m. 2026-10-14. |
| pypulseq | — | `read`: `KeyError(np.float64(-1.0))` (both versions). P05's script (`repro.py`, the same triangle with `make_arbitrary_grad`): `area` 7.8553, the area through the edge samples 7.6637, through all samples 7.7595 1/m; 1.5.0.post1 and master `c977214`. 2026-10-14. |

## Impact

No reader plays this file differently because of `area`: the value is
MATLAB's own, and the scanner plays the samples. But a sequence that MATLAB
Pulseq (or pypulseq) builds from `area` (a rephaser, a spoiler, a balanced
moment) writes a file whose played moment is not the one that `area` says:
here -0.0958 1/m, 1.2 % of the lobe, where `getBlock` says 0. For a smooth
gradient the difference is smaller (P05: 1.0 % between the centre and the
edge areas of a half sine of 21 samples). MATLAB's `area` and its own k-space
(from `waveforms_and_times`) disagree for the same file.

## Suggested resolution

MATLAB Pulseq: compute `area` of an oversampled gradient as the area of the
waveform through `first`, all the samples and `last` (the waveform of
`waveforms_and_times` and of slide 8), or document that `area` is the area of
the centre samples. pypulseq would follow the same choice.

## Report

P05 of mdtisdall/pypulseq-issues (`1de4a1d`) is the draft, to pulseq/pulseq
(MATLAB toolbox). Its question: is `grad.area` meant to be the area of the
centre samples, also for an interpreter that plays the edge samples? Attach
`oversampled_area_rephaser.seq`, and add the observation of this record: a
rephaser of `-g.area` written to the file leaves -0.0958 1/m in MATLAB's own
`waveforms_and_times`.

## History

- 2026-09-24: found (P05 of mdtisdall/pypulseq-issues, commit `fcca26d`). Not
  in pulseq-analysis.
- 2026-10-14: checked against the pinned sources: the reproducer written by
  MATLAB Pulseq under Octave 11.3.0 and run in MATLAB Pulseq, the C++ reader
  (three modes; plain and sanitized) and pypulseq (a 1.5.1 file); P05's
  script run in both versions of pypulseq.
- 2026-10-14: in scope by the decision of the user: MATLAB's `area` of an
  event read from a file disagrees with the waveform that the specification
  defines for that file. Severity kept at `playback`: the area that MATLAB
  gives the event differs from the area of the waveform that is played, so a
  rephaser built from `area` plays a moment that is not 0 (Impact). No
  other value fits better: `documentation` would mean that only a text is
  wrong, and here MATLAB's code computes the value.
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, the two pins of `sources.yaml`;
  the two behave the same here.
