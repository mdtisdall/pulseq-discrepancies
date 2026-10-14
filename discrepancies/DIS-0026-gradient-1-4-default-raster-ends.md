---
id: DIS-0026
title: A 1.4 arbitrary gradient on the default raster (no first and last columns)
kind: spec-gap
severity: playback
status: confirmed
format_versions: ["1.4.x"]
sources:
  - key: spec
    behavior: "gives only the 1.5 row with first and last; silent on the ends of a 1.4 gradient"
  - key: cpp-reader
    behavior: "first and last are 1.18e-38 (a marker); plays the gradient to about 0 at both ends"
  - key: matlab-pulseq
    behavior: "first from the block before (else 0); last by an alternating sum from first"
  - key: pypulseq
    behavior: "first from the block before (else 0); last by linear extrapolation of the last two samples"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: C++ reader
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
  reason: "MATLAB write_v141 and pypulseq write(v141_compat=True) write 1.4 arbitrary gradients of time ID 0 with no first and last columns. The spec is silent, and the three readers compute different end values."
pulseq_analysis:
  ids: [D4.4]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0026: A 1.4 arbitrary gradient on the default raster (no first and last columns)

## Summary

A `[GRADIENTS]` row of a 1.4 file has no `first` and `last`, and the samples
of a gradient of time ID 0 are at the centres of the raster cells, so the
file does not give the value of the gradient at the start and at the end of
the event. The specification does not say what a reader takes there. The C++
reader takes a marker of about 0 and plays the gradient down to 0 at both
ends, also where it continues into the next block; MATLAB Pulseq and pypulseq
take `first` from the block before, and compute `last` each with its own
rule, so they also differ from each other.

## What each source does

| Source | What it does |
|---|---|
| Specification | Gives only the row `<id> <amp> <first> <last> <shape_id> <time_id> <delay>` (section 2.8.2, `spec:375-377`); `first` and `last` are "the amplitude of the gradient at the start" and "at the end" (`spec:392-393`). It does not give the 1.4 row, and the table of revisions does not say when `first` and `last` were added (`spec:113`, `spec:117-122`). The samples of time ID 0 are at the centres of the raster cells (section 2.6, `spec:290`; slide 4), and "non-zero start/end values are allowed" (slide 7). |
| C++ reader | Reads a 1.4 row as 5 numbers and sets `first` and `last` to `FLOAT_UNDEFINED` (`cpp:1078-1086`), which is `1.18e-38f` (`cpp.h:128`). `gradientsAt` interpolates from `first` at the start of the event to the first sample, and from the last sample to `last` at the end (`cpp:3679-3688`), so the 1.4 gradient goes to about 0 in the first and in the last half raster. |
| MATLAB Pulseq | Reads 4 numbers (`read.m:131-132`) and marks `first` and `last` as NaN (`read.m:312-318`). A second pass over the blocks (`read.m:323-391`) sets `first` to the `last` of the gradient of the block before on the same axis when that gradient ends at the end of its block and this gradient has no delay, else to 0 (`read.m:344-350`, `read.m:365-368`); `last` is the last of the edge values `e[k+1] = 2 w[k] - e[k]` from `e[0] = first` (`read.m:358-361`). |
| pypulseq | Reads 4 numbers (`read_seq.py:164-165`), marks `first` and `last` as `None` (`read_seq.py:339-348`), and sets `first` as MATLAB does (`read_seq.py:370-378`, `read_seq.py:390-396`); `last` is `(3 w[-1] - w[-2]) / 2`, a linear extrapolation by half a raster (`read_seq.py:385-388`). |

Both writers write such files: MATLAB Pulseq's `write_v141` writes the
`[GRADIENTS]` row as `id amp shape_id time_id delay` (`write_v141.m:93-95`),
and pypulseq's `write(..., v141_compat=True)` does the same
(`write_seq.py:400-410`, `sequence.py:1796` of 1.5.0.post1, `:1859` on master).

## Reproducer

In [`reproducers/DIS-0026/`](../reproducers/DIS-0026/), written by MATLAB
Pulseq under Octave 11.3.0 (`seq.write_v141` and `seq.write`), gradient raster
10 µs, three blocks of 100 µs on x, each an `mr.makeArbitraryGrad` of 10
samples with explicit `first` and `last`:

1. a ramp from 0 to 100000 Hz/m (samples 5000 to 95000 Hz/m, `first` 0, `last` 100000);
2. the ramp back down (`first` 100000, `last` 0);
3. a half sine `sin(pi (i + 0.5) / 10)` of amplitude 98768.8 Hz/m (`first` 0, `last` 0).

- `ends_v141.seq`: the 1.4.1 file (`write_v141`); its `[GRADIENTS]`:

  ```
  [GRADIENTS]
  1        95000 1 0 0
  2        95000 2 0 0
  3      98768.8 3 0 0
  ```

- `ends_v151.seq`: the same sequence as a 1.5.1 file (`write`), with `first`
  and `last`, for comparison.

pypulseq 1.5.0.post1 and master write the same `[GRADIENTS]` and `[SHAPES]`
for the same gradients with `v141_compat=True` (run).

Commands as in DIS-0001. The C++ values are `SeqBlock::gradientsAt` at the
times (`pulseq-cpp-oracle --sample FILE`, lines `block time_us` on stdin);
the MATLAB Pulseq and pypulseq values are the polylines of
`waveforms_and_times`, linearly interpolated at the same times, taken from
inside the block at its two ends. Hz/m, gx.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | `ends_v141.seq`: no value at the ends of the events. `ends_v151.seq`: block 1 ends at 100000, block 2 starts at 100000, block 3 ends at 0. | — |
| C++ reader | — | `ends_v141.seq`: `first` = `last` = 1.18e-38 in each event (`--dump`). Block 1 at 97.5 and 100 µs: 47500 and 0; block 2 at 0 and 2.5 µs: 0 and 47500 (the ramp has a notch to 0 at the block boundary). `ends_v151.seq`: 97500, 100000; 100000, 97500. 2026-10-14. |
| MATLAB Pulseq | — | `ends_v141.seq`: `last` of block 1 = 99999.99993, `first` of block 2 the same; `last` of block 3 = -3.6e-12. Block 1 at 97.5, 100 µs: 97500, 100000; block 2 at 0, 2.5 µs: 100000, 97500; block 3 at 97.5, 100 µs: 7821.7, 0. 2026-10-14. |
| pypulseq | — | `ends_v141.seq`: `last` of block 1 = 100000.000005; `last` of block 3 = 765.6. Blocks 1 and 2 as MATLAB; block 3 at 97.5, 100 µs: 8204.5, 765.6. `ends_v151.seq`: the three implementations give the same values at these times. 2026-10-14. |

## Impact

Every 1.4 file with an arbitrary gradient of time ID 0 is affected; MATLAB
Pulseq and pypulseq still write such files on request, and older files in use
are 1.4. On the scanner's reader, a shaped gradient that continues from one
block into the next (a spiral or a ramp split over blocks) drops to 0 in the
last half raster of one block and the first half raster of the next, which
changes its moment; the toolboxes, which compute k-space and plots from the
same file, do not show this, and differ from each other at the end of a
gradient that is not linear there.

## Suggested resolution

The specification: give the 1.4 row of `[GRADIENTS]`, and say what value a
reader takes at the start and at the end of a 1.4 arbitrary gradient of time
ID 0 (for example: from the gradient of the block before on the same axis
when it ends at the boundary, else 0; and at the end, the linear extrapolation
by half a raster). The C++ reader, MATLAB Pulseq and pypulseq: follow that
rule. The C++ reader should not use `FLOAT_UNDEFINED` as a value.

## Report

Draft, to pulseq/pulseq (specification, C++ reader, MATLAB Pulseq) and
pulseq/pypulseq:

> **The ends of an arbitrary gradient in a 1.4 file**
>
> A 1.4 `[GRADIENTS]` row has no `first` and `last`, and the samples of time
> ID 0 are at the cell centres (specification section 2.6), so a 1.4 file
> does not give the gradient at the start and the end of the event. The
> readers fill it in three ways. `ExternalSequence` sets `first` and `last`
> to `FLOAT_UNDEFINED` (1.18e-38, `ExternalSequence.cpp:1085-1086`), and
> `gradientsAt` ramps to it (lines 3681 and 3686): a ramp split over two
> blocks of the attached file (written by `write_v141`) goes 95000 ->
> 0 -> 95000 Hz/m across the boundary. MATLAB Pulseq takes `first` from the
> block before and `last` by an alternating sum (`read.m:344-368`); pypulseq
> takes `last` by linear extrapolation (`read_seq.py:387`): for a half sine
> they give 0 and 765.6 Hz/m. Could the specification give the 1.4 row and
> one rule for the ends, and the readers follow it?

## History

- 2026-10-09: found by pulseq-analysis (old ID D39, commit `49a7e2c`; D4.4,
  `5bd053a`).
- 2026-10-14: confirmed against the pinned sources; the reproducers written
  by MATLAB Pulseq under Octave 11.3.0 (pypulseq writes the same sections),
  and run in the C++ reader (plain and sanitized: both exit 0), MATLAB Pulseq
  and pypulseq, with the values sampled at the same times.
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq; the two behave the same here, and the
  citations give the lines of 1.5.0.post1, with those of master where they
  differ.
