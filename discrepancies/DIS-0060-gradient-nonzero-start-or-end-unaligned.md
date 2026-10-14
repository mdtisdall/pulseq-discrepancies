---
id: DIS-0060
title: A gradient that is not 0 at a start after a delay, or at an end before the end of its block
kind: spec-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "a gradient that starts above 0 must have delay 0; one that ends above 0 must end with its block"
  - key: spec-slides
    behavior: "vertices with non-zero amplitude must touch the block boundary"
  - key: cpp-reader
    behavior: "reads it with no error or warning"
  - key: matlab-pulseq
    behavior: "read accepts it; checkTiming reports it"
  - key: pypulseq
    behavior: "read accepts it; check_timing does not report it"
    version: "1.5.0.post1 and master c977214"
report_to:
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
  reason: "MATLAB's addBlock passes a gradient that ends at a negative value before the block end, and both writers pass a small nonzero start after a delay. Every reader accepts it."
pulseq_analysis:
  ids: [D27]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0060: A gradient that is not 0 at a start after a delay, or at an end before the end of its block

## Summary

The specification and its slide set say that a gradient that starts at a value
other than 0 must start with its block (delay 0), and that one that ends at a
value other than 0 must end with its block. Otherwise the gradient jumps from
or to 0 inside the block. The C++ reader, MATLAB Pulseq's `read` and
pypulseq's `read` accept both cases with no error or warning. MATLAB
Pulseq's `checkTiming` reports both; pypulseq's `check_timing` reports
neither.

## What each source does

| Source | What it does |
|---|---|
| Specification | "Because both these gradients end at non-zero values, they need to be aligned to the end of the block …. Gradients that start at non-zero values must be aligned to the beginning of the block, meaning that the start delay of such gradients must be 0." (section 2.8.2, `spec:420`) |
| Slide set | For an extended trapezoid: "Vertices with non-zero amplitude must touch block boundary (to connect to neighbors)" (slide 6). For a regularly sampled gradient: "As for extended trapezoids: non-zero start/end values are allowed" (slide 7). |
| C++ reader | Does not check `first`, `last` or the delay against the block (run: exit 0, no message). |
| MATLAB Pulseq | `read` does not check (run). `checkTiming` (`Sequence.m:211`) reports "gradient starts at a non-zero value but defines a delay" (`Sequence.m:308-310`) and "gradient ends at a non-zero value but does not last until the end of the block" (`Sequence.m:319-321`). |
| pypulseq | `read` does not check (run), and `check_timing` (`check_timing.py:23`) reports no error for either file. |

## Reproducer

Two 1.5.1 files in [`reproducers/DIS-0060/`](../reproducers/DIS-0060/), each
of one block with an arbitrary gradient on x (10 samples, peak
500000 Hz/m):

- `nonzero_start_after_delay.seq`: `first` 500000 Hz/m and a delay of 10 µs,
  `[GRADIENTS]` row `1 500000 500000 0 1 0 10` in a block of 110 µs;
- `nonzero_end_before_block_end.seq`: `last` 500000 Hz/m, the gradient ends at
  100 µs in a block of 200 µs, row `1 500000 0 500000 1 0 0`.

Commands as in DIS-0057.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification and slide set | Not valid: the gradient does not touch the block boundary where it is not 0. | — |
| C++ reader | — | Both read, no message (exit 0; sanitized exit 0). 2026-10-14. |
| MATLAB Pulseq | — | Both read. `checkTiming`: false, with the two messages above. 2026-10-14. |
| pypulseq | — | Both read. `check_timing`: true, no error. 2026-10-14. |

## Impact

Such a gradient jumps between 0 and a large value inside the block, which no
gradient amplifier can follow; the scanner's reader takes the file as it is,
with no message. A user of pypulseq is not told even after `check_timing`.

## Suggested resolution

The C++ reader: reject such a gradient, as the specification and the slide
set say "must". pypulseq's `check_timing`: report the two cases, as MATLAB
Pulseq's `checkTiming` does. The `read` of both toolboxes could warn.

## Report

Draft, to pulseq/pulseq (C++ reader, MATLAB Pulseq) and pulseq/pypulseq:

> **A gradient that starts or ends above 0 away from the block boundary is
> accepted**
>
> Section 2.8.2 says that a gradient that starts at a non-zero value must
> have a delay of 0, and one that ends at a non-zero value must be aligned to
> the end of the block; slide 6 of `pulseq_shapes_and_times.pdf` says
> "Vertices with non-zero amplitude must touch block boundary", and slide 7
> applies it to sampled gradients.
> `ExternalSequence` reads a gradient with `first` 500000 Hz/m and a delay of
> 10 µs, and one with `last` 500000 Hz/m that ends 100 µs before its block,
> with no message; so does `read` of MATLAB and pypulseq. MATLAB's
> `checkTiming` reports both, pypulseq's `check_timing` neither. Could the
> C++ reader reject them, and `check_timing` report them? Reproducers
> attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D27, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here). The run
  of `check_timing` is new: pypulseq's timing check does not report the
  two cases.
