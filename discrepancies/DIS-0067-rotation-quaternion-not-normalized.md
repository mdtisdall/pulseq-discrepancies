---
id: DIS-0067
title: A rotation quaternion that is not normalized, or of norm 0
kind: spec-gap
severity: acceptance
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "a rotation is 'a normalized rotation quaternion'; no tolerance, no rule for another"
  - key: cpp-reader
    behavior: "rejects a norm more than 1e-3 from 1 (also norm 0); divides the others by their norm"
  - key: matlab-pulseq
    behavior: "divides any quaternion of norm above 0 by its norm; keeps norm 0 and plays it as no rotation"
  - key: pypulseq
    behavior: "rejects every file with ROTATIONS (DIS-0063)"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D2.18, D3.10]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0067: A rotation quaternion that is not normalized, or of norm 0

## Summary

The specification describes each rotation as "a normalized rotation
quaternion", and says nothing of a quaternion that is not normalized. The C++
reader rejects a quaternion whose norm is more than 1e-3 from 1, and divides
the others by their norm; MATLAB Pulseq divides any quaternion by its norm and
plays it, and keeps a quaternion of norm 0, which it plays as no rotation. So
`1.01 0 0 0`, `1.414214 0 0 1.414214` and `0 0 0 0` are rejected by the
scanner's reader and played by MATLAB Pulseq.

## What each source does

| Source | What it does |
|---|---|
| Specification | "Each rotation operation is described as a normalized rotation quaternion" (section 2.8.4, `spec:567`). No tolerance, and no rule for a quaternion that is not normalized. |
| C++ reader | Computes the norm of each quaternion, rejects one with `fabs(norm - 1) > 1e-3` ("rotation extension loaded a non-normalized quaternion"), and divides the others by their norm (`cpp:1286-1292`). |
| MATLAB Pulseq | `read` divides each quaternion by its norm (`read.m:183`, `mr.aux.quat.normalize`), except one of norm 0, which it keeps (`normalize.m:4-13`). `waveforms_and_times` rotates the gradients of the block (`Sequence.m:1988-1990`, `mr.rotate3D`); the rotation matrix of the zero quaternion is the identity (`toRotMat.m`), so a block with `0 0 0 0` is played unrotated. |
| pypulseq | Rejects every file with `extension ROTATIONS` (`read_seq.py:228`; DIS-0063). |

## Reproducer

Four 1.5.1 files in [`reproducers/DIS-0067/`](../reproducers/DIS-0067/), each
of one block with a trapezoid on x and one rotation (`RequiredExtensions
ROTATIONS`):

| File | `extension ROTATIONS` row | Norm |
|---|---|---|
| `quaternion_norm_1_0005.seq` | `1 1.0005 0 0 0` | 1.0005 |
| `quaternion_norm_1_01.seq` | `1 1.01 0 0 0` | 1.01 |
| `quaternion_norm_2.seq` | `1 1.414214 0 0 1.414214` | 2 (90° about z) |
| `quaternion_norm_0.seq` | `1 0 0 0 0` | 0 |

Commands as in DIS-0057; the rotation of block 1 from `pulseq-cpp-oracle
--dump` and MATLAB's `getBlock(1).rotation`, and the gradient axes from
MATLAB's `waveforms_and_times`.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent: each quaternion is to be normalized. | — |
| C++ reader | — | `1.0005`: read, rotation `[1, 0, 0, 0]`. `1.01`, norm 2 and norm 0: "ERROR: rotation extension loaded a non-normalized quaternion", `load` returned false (exit 1; sanitized exit 1). 2026-10-14. |
| MATLAB Pulseq | — | All four read. Norm 2: quaternion `0.7071 0 0 0.7071`, the trapezoid played on y. Norm 0: quaternion `0 0 0 0`, the trapezoid played on x. 2026-10-14. |
| pypulseq | — | All four: `ValueError: Unknown section code: extension ROTATIONS 1`. 2026-10-14. |

## Impact

A quaternion written with too few digits, or edited by hand, plays in MATLAB
Pulseq and is refused by the scanner when its norm is more than 1e-3 from 1;
every quaternion that the C++ reader accepts, MATLAB Pulseq accepts too. A
quaternion of norm 0 is no rotation: MATLAB Pulseq plays it as the identity,
and the scanner refuses the file. A user who checks such a file in MATLAB
Pulseq learns of the problem only at the scanner.

## Suggested resolution

The specification: give a tolerance for "normalized" (for example 1e-3, as the
C++ reader has), and say that a quaternion outside it, and one of norm 0, makes
the file invalid. MATLAB Pulseq: then reject such a quaternion as the C++
reader does.

## Report

Draft, to pulseq/pulseq:

> **A rotation quaternion that is not normalized**
>
> Section 2.8.4 says that a rotation is "a normalized rotation quaternion",
> with no tolerance. `ExternalSequence` rejects a quaternion whose norm is more
> than 1e-3 from 1 (`ExternalSequence.cpp:1286-1292`), and normalizes the
> others; MATLAB's `read` normalizes any quaternion (`read.m:183`) and keeps
> one of norm 0, which `waveforms_and_times` plays as no rotation. So
> `1.01 0 0 0` and `0 0 0 0` are played by MATLAB and refused by the scanner.
> Could the specification give the tolerance, and say what a quaternion
> outside it (and of norm 0) means? Reproducers attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D49, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here). The
  files of norm 2 and norm 0 in MATLAB Pulseq are new.
