---
id: DIS-0030
title: A gap between two gradient events on one axis, next to a value other than 0
kind: spec-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "a gradient that starts or ends at a value other than 0 must touch the block boundary; no tolerance; silent on what plays in a gap"
  - key: spec-slides
    behavior: "vertices with a value other than 0 must touch the block boundary, to connect to the neighbours"
  - key: cpp-reader
    behavior: "decodes one block at a time: 0 before an event's delay, after its end, and in a block with no gradient (a step)"
  - key: matlab-pulseq
    behavior: "writes it below maxSlew * gradRasterTime (any negative end value); waveforms_and_times ramps to 0 and from 0 in half a raster"
  - key: pypulseq
    behavior: "writes it below max_slew * grad_raster_time; waveforms draws a straight line across the gap"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq, pypulseq]
  reason: "Both writers accept a non-zero gradient end or start next to a gap, below maxSlew*gradRasterTime, and MATLAB accepts any negative end value. The spec forbids this with no tolerance, and the three readers play the gap differently."
pulseq_analysis:
  ids: [D2.14, D7.4]
  commit: 5bd053a
found: 2026-10-07
checked: 2026-10-14
---

# DIS-0030: A gap between two gradient events on one axis, next to a value other than 0

## Summary

The specification says that a gradient that starts at a value other than 0
must have no delay, and that one that ends at a value other than 0 must end
at the end of its block, followed by a gradient in the next block. It gives
no tolerance. MATLAB Pulseq and pypulseq check these rules only above
`maxSlew * gradRasterTime`, so they write files where a value other than 0
is next to a gap on one axis. The three readers then play the gap
differently: the C++ reader steps to 0, MATLAB Pulseq ramps to 0 in half a
gradient raster, and pypulseq draws a straight line across the gap.

## What each source does

| Source | What it does |
|---|---|
| Specification | "Because both these gradients end at non-zero values, they need to be aligned to the end of the block", and "They also require additional 'ramp down' gradients in the next block"; "Gradients that start at non-zero values must be aligned to the beginning of the block, meaning that the start delay of such gradients must be 0" (section 2.8.2, `spec:420`). It gives no tolerance, and does not say what plays in a gap between two events. |
| Slide set | Extended trapezoids: "Vertices with non-zero amplitude must touch block boundary (to connect to neighbors)" (slide 6). Arbitrary gradients: "As for extended trapezoids: non-zero start/end values are allowed" (slide 7). |
| C++ reader | Decodes one block at a time. `gradientsAt` gives 0 before the delay of an extended trapezoid (`cpp:3614-3618`) and after its last time (`cpp:3621-3625`), the same for an arbitrary gradient (`cpp:3656-3667`) and a trapezoid (`cpp:3574-3585`), and 0 on an axis with no event in the block (`cpp:3695-3696`). So the gradient steps from the value at the end of one event to 0, and from 0 to the value at the start of the next. |
| MATLAB Pulseq | `setBlock` refuses a delay before a start value, a start value that does not connect to the previous block, an end value before the end of the block, and a block with no gradient after an end value, only when the value is above `maxSlew * gradRasterTime` (`Sequence.m:1104-1106`, `:1114-1125`, `:1128-1130`). The check of the end value has no `abs` (`Sequence.m:1128`): a negative end value of any size before the end of the block is accepted (run: -144758.4 Hz/m, twice the limit, accepted; +144758.4 Hz/m refused). `waveforms_and_times`, across a gap of more than one gradient raster, adds a point at 0 half a raster after an event that ends at a value other than 0, and half a raster before one that starts at such a value, with a warning; a value of at most 1e-6 Hz/m is set to 0 (`Sequence.m:2114-2134`). |
| pypulseq | `add_block` makes the same checks with the same limit, `max_slew * grad_raster_time` (`block.py:223-225`, `:262-263`, `:290-294`), with `abs` on the end value. `waveforms` joins the points of the events of an axis in play order and adds nothing at a gap (`sequence.py:1683-1691`; `:1746-1754` on master), so the gradient is the straight line from the last point of one event to the first point of the next. |

## Reproducer

Three files written by MATLAB Pulseq under Octave 11.3.0 with `mr.opts()`
(limit `maxSlew * gradRasterTime` = 72379.2 Hz/m), in
[`reproducers/DIS-0030/`](../reproducers/DIS-0030/). Each has the extended
trapezoid `0 → a → a` (0, 100, 200 µs) on x, with `a` = 36189.6 Hz/m (half
the limit), then the extended trapezoid `a → 0` (100 µs), from the script of
P12 of mdtisdall/pypulseq-issues:

- `gap_delay.seq`: block 1 (200 µs), then block 2 (200 µs) with the ramp down
  after a delay of 100 µs: a start value after a delay.
- `gap_early_end.seq`: block 1 of 300 µs with the first event (it ends at
  `a` at 200 µs), then block 2 with the ramp down: an end value before the end
  of the block.
- `gap_delay_block.seq`: block 1 (200 µs), a delay block of 100 µs, then the
  ramp down in block 3: both events touch their block boundaries, but the
  block between has no gradient.

```matlab
sys = mr.opts(); a = 0.5 * sys.maxSlew * sys.gradRasterTime;
ramp_and_hold = mr.makeExtendedTrapezoid('x', 'times', [0 100e-6 200e-6], 'amplitudes', [0 a a], 'system', sys);
ramp_down = mr.makeExtendedTrapezoid('x', 'times', [0 100e-6], 'amplitudes', [a 0], 'system', sys);
s = mr.Sequence(sys); s.addBlock(ramp_and_hold); s.addBlock(mr.makeDelay(100e-6)); s.addBlock(ramp_down);
s.write('gap_delay_block.seq');
```

In each file the gap on x is from 200 to 300 µs of the sequence. Commands as
in DIS-0001; the C++ values from `pulseq-cpp-oracle --sample FILE` (block
index from 0, time in the block in µs, `SeqBlock::gradientsAt`); pypulseq's
`P12` script (`repro.py` of mdtisdall/pypulseq-issues at `1de4a1d`) run in
both versions.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | The three files break the rules of `spec:420` (no tolerance); what plays in the gap is not defined. | — |
| C++ reader | — | All three read (exit 0, sanitized exit 0). x at the end of the first event: 36189.6 Hz/m; in the gap 0 (`gap_delay.seq`: block 1 at 0, 5, 50, 95 µs; `gap_early_end.seq`: block 0 at 205, 250, 295 µs; `gap_delay_block.seq`: block 1 at 0, 50, 100 µs); 36189.6 Hz/m at the start of the ramp down. Steps of 36189.6 Hz/m at 200 and 300 µs. 2026-10-14. |
| MATLAB Pulseq | — | All three read. `waveforms_and_times` x, the same for the three files: times 0, 100, 200, 205, 295, 300, 400 µs; values 0, 36189.6, 36189.6, 0, 0, 36189.6, 0 Hz/m: ramps of half a raster to and from 0, and 0 in the gap. 2026-10-14. |
| pypulseq | — | All three read. `waveforms_and_times` x, the same for the three files: times 0, 100, 200, 300, 400 µs; values 0, 36189.6, 36189.6, 36189.6, 0 Hz/m: 36189.6 Hz/m across the whole gap. P12's script: `add_block` accepts both cases, and `get_gradients()` gives 36189.6 Hz/m at 205, 250 and 295 µs. 1.5.0.post1 and master `c977214`. 2026-10-14. |

## Impact

A sequence that ends an event at a small value other than 0 before a gap,
or starts one after a gap, is written by both toolboxes. In the 100 µs gap
of the reproducer, pypulseq's waveform (and so its `calculate_pns`, gradient
spectrum and k-space) has 36189.6 Hz/m where the scanner's reader and MATLAB
Pulseq have 0: a moment of 3.6 1/m that the scanner does not play. MATLAB's
ramps of half a raster have up to twice `maxSlew` (each step is up to
`maxSlew * gradRasterTime`), and the scanner's reader plays an instant step.
MATLAB's `setBlock` accepts a negative end value of any size before the end
of a block, so on that axis the step can be large.

## Suggested resolution

The specification: give the tolerance for "non-zero" in the rules of
`spec:420` (for example `maxSlew * gradRasterTime`, as both toolboxes use), and
say what an interpreter plays where no event plays (0, as the C++ reader
does). MATLAB Pulseq: use `abs(cg.stop(2))` in the check of `Sequence.m:1128`.
pypulseq: apply the gap rule of MATLAB's `waveforms_and_times` in `waveforms`
(P12's suggested fix), so that the two toolboxes agree.

## Report

Drafts, to pulseq/pulseq (specification, MATLAB toolbox) and pulseq/pypulseq:

> **What plays in a gap next to a gradient value that is not 0**
>
> The specification requires a gradient that starts or ends at a value other
> than 0 to touch the block boundary, with no tolerance (section 2.8.2). MATLAB
> Pulseq (`setBlock`, `Sequence.m:1104-1130`) and pypulseq (`add_block`,
> `block.py:223-294`) check this only above `maxSlew * gradRasterTime`, so they
> write files with such a value next to a gap. The readers then differ in the
> gap: the C++ reader steps to 0, MATLAB's `waveforms_and_times` ramps to 0 in
> half a raster (`Sequence.m:2114-2134`), and pypulseq's `waveforms` draws a
> straight line across the gap. Could the specification give the tolerance
> and say that the gradient is 0 where no event plays? Files attached
> (`gap_delay.seq`, `gap_early_end.seq`, `gap_delay_block.seq`, written by
> MATLAB Pulseq).
>
> Also, MATLAB: `Sequence.m:1128` tests `cg.stop(2) > maxSlew * gradRasterTime`
> without `abs`, so a gradient that ends at a large negative value before the
> end of its block is accepted.

pypulseq: P12 of mdtisdall/pypulseq-issues (`1de4a1d`) is the draft.

## History

- 2026-10-07: found (P12 of mdtisdall/pypulseq-issues, commit `898f0d8`).
- 2026-10-12: in pulseq-analysis as D42 (commit `49a7e2c`); D2.14 and D7.4 at
  `5bd053a`.
- 2026-10-14: confirmed against the pinned sources: reproducers written by
  MATLAB Pulseq under Octave 11.3.0 and run in the C++ reader (plain and
  sanitized), MATLAB Pulseq and pypulseq (1.5.1 files). The missing `abs` of
  `Sequence.m:1128` found and run. Kind changed from the inventory's
  `spec-gap` to `spec-vs-implementation`: the specification states the rule
  (`spec:420`, slide 6), and the writers accept files that break it.
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, the two pins of `sources.yaml`;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
