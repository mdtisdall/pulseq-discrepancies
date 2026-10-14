---
id: DIS-0069
title: An extension, or a label flag, in a file older than the revision that introduced it
kind: spec-vs-implementation
severity: acceptance
status: withdrawn
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "gives the revision of each extension and flag; says nothing of an older file"
  - key: cpp-reader
    behavior: "reads them in any version (attaches a rotation to a 1.5.0 block)"
  - key: matlab-pulseq
    behavior: "reads them in any version (rotates the gradients of a 1.5.0 block)"
  - key: pypulseq
    behavior: "reads a 1.4.0 PMC flag and 1.4.1 soft delays; rejects ROTATIONS in any version"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D4.6, D4.7]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0069: An extension, or a label flag, in a file older than the revision that introduced it

## Summary

Withdrawn: not a discrepancy. The specification gives the revision that
introduced each extension and label flag, and says nothing of a file of an
older revision that uses one. The C++ reader and MATLAB Pulseq both read such
a file and give the extension its meaning (a ROTATIONS object in a 1.5.0
file rotates the block in both), and pypulseq reads the older label flag and
soft delay too. No two sources disagree about the file. The rule that a
reader of a revision knows only the mechanisms of that revision is a choice of
pulseq-analysis's interpreter `spec`, which this repository does not record
(`docs/record-format.md`, section 1).

## What each source does

| Source | What it does |
|---|---|
| Specification | The soft delay extension "has been introduced in revision 1.5.0" (`spec:545`); the rotation and RF shimming extensions "in revision 1.5.1" (`spec:567`, `spec:584`); the flags `PMC`, `NOROT`, `NOPOS`, `NOSLC` and `ONCE` "in revision 1.4.1" (`spec:526`). It does not say what a reader does with them in an older file. |
| C++ reader | Recognizes each extension by its name, in any version (`cpp:1233-1244`), and attaches the block's rotation in any version (`cpp:1871-1879`). It decodes a label by its name in any version (`decodeLabel`, `cpp:2392-2395`). It reads `RequiredExtensions` only from 1.5.1 (`cpp:1505`). |
| MATLAB Pulseq | Reads each extension by its name, in any version (`read.m:157-184`), and rotates the gradients of a block with a rotation in `waveforms_and_times` (`Sequence.m:1988-1990`). |
| pypulseq | Reads the label flag and the soft delay in any version (`read_seq.py:195-226`); rejects ROTATIONS in every version (DIS-0063). |

## Reproducer

Four files in [`reproducers/DIS-0069/`](../reproducers/DIS-0069/), each of a
trapezoid block on x:

| File | Version | Content |
|---|---|---|
| `rotation_v150.seq` | 1.5.0 | a ROTATIONS object of 90° about z |
| `rotation_v151.seq` | 1.5.1 | the same (the control) |
| `label_pmc_v140.seq` | 1.4.0 | LABELSET `1 1 PMC` |
| `soft_delay_v141.seq` | 1.4.1 | a delay block with a DELAYS object `1 0 -100 1 TE` |

Commands as in DIS-0057; the rotation of block 1 from `pulseq-cpp-oracle
--dump` and MATLAB's `getBlock`, and the axis of the gradient from MATLAB's
`waveforms_and_times`.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent. | — |
| C++ reader | — | All four read (exit 0; sanitized exit 0). `rotation_v150.seq`: version 1005000, rotation `[0.7071, 0, 0, 0.7071]` attached to block 1. 2026-10-14. |
| MATLAB Pulseq | — | All four read. `rotation_v150.seq` and `rotation_v151.seq`: quaternion `0.7071 0 0 0.7071`, the trapezoid played on y. 2026-10-14. |
| pypulseq | — | `label_pmc_v140.seq` and `soft_delay_v141.seq`: read (with the warning "Loading older Pulseq format file"). Both rotation files: `ValueError: Unknown section code: extension ROTATIONS 1` (DIS-0063). 2026-10-14. |

## Impact

None between the sources: the C++ reader and MATLAB Pulseq give these files
the same meaning, and pypulseq differs only where it differs for every
version (DIS-0063).

## Suggested resolution

Not applicable (withdrawn).

## Report

Not reported: withdrawn.

## History

- 2026-10-09: found by pulseq-analysis (old IDs D45, D49, D50, commit
  `49a7e2c`); the inventory reserved this ID for it.
- 2026-10-14: run in the C++ reader (plain and sanitized), MATLAB Pulseq, and
  pypulseq 1.5.0.post1 and master `c977214` of pulseq/pypulseq: the C++
  reader and MATLAB Pulseq read and apply the extension in the older file.
  Withdrawn under the scope rule of the migration: a record is a disagreement
  between sources about a file, and the only reading that differs is that of
  pulseq-analysis's interpreter `spec`.
