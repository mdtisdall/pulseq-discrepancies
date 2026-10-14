---
id: DIS-0066
title: Two ROTATIONS or two RF_SHIMS objects in one block
kind: spec-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "only one rotation, and only one RF shimming object, can be specified per block"
  - key: cpp-reader
    behavior: "warns and keeps the first"
  - key: matlab-pulseq
    behavior: "read accepts the file; getBlock fails with an error"
  - key: pypulseq
    behavior: "rejects every file with ROTATIONS or RF_SHIMS (DIS-0063)"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D48]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0066: Two ROTATIONS or two RF_SHIMS objects in one block

## Summary

The specification allows one rotation and one RF shimming object per block.
A block whose extension list has two of either is played by the C++ reader
with the first and a warning, and rejected by MATLAB Pulseq with an error. The
C++ reader's warning for two RF shims also names the wrong extension ("soft
delay").

## What each source does

| Source | What it does |
|---|---|
| Specification | "Only one rotation extension object can be specified per block." (section 2.8.4, `spec:567`) "Only one RF shimming extension object can be specified per block." (`spec:584`) |
| C++ reader | `GetBlock` keeps the first rotation and warns "only one rotation per block is supported" (`cpp:1871-1878`); for RF shims it keeps the first and warns "only one soft delay per block is supported" (`cpp:1909-1915`), the text of the soft-delay case (`cpp:1902`). |
| MATLAB Pulseq | `read` accepts the file. `getBlock` fails: "Only one rotation extension object per block is allowed" (`Sequence.m:1300`), "Only one RF shim extension object per block is allowed" (`Sequence.m:1287`). |
| pypulseq | Rejects every file with `extension ROTATIONS` or `extension RF_SHIMS` (`read_seq.py:228`; DIS-0063), whatever the number per block. |

## Reproducer

Two 1.5.1 files in [`reproducers/DIS-0066/`](../reproducers/DIS-0066/):

- `two_rotations.seq`: one trapezoid block whose extension list has two
  ROTATIONS objects (`RequiredExtensions ROTATIONS`):

  ```
  [EXTENSIONS]
  1 1 1 2
  2 1 2 0

  extension ROTATIONS 1
  1 0.707107 0 0 0.707107
  2 0 0 0 1
  ```

- `two_rf_shims.seq`: one RF block whose extension list has two RF_SHIMS
  objects (`RequiredExtensions RF_SHIMS`).

Commands as in DIS-0057.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Not valid: two objects of one kind in one block. | — |
| C++ reader | — | Both read (exit 0; sanitized exit 0), with "WARNING: only one rotation per block is supported; error block: 0" and "WARNING: only one soft delay per block is supported; error block: 0". 2026-10-14. |
| MATLAB Pulseq | — | `getBlock(1)`: "Only one rotation extension object per block is allowed" / "Only one RF shim extension object per block is allowed". 2026-10-14. |
| pypulseq | — | Both: `ValueError: Unknown section code: extension ROTATIONS 1` / `… RF_SHIMS 1`. 2026-10-14. |

## Impact

MATLAB Pulseq's own `getBlock` refuses two objects of one kind in one block.
A file from another tool with two rotations in a
block is played by the scanner's reader with the first, while MATLAB Pulseq
refuses it; the user of the toolbox cannot see what the scanner plays. The
RF-shim warning names the soft delay, which misleads whoever reads the log.

## Suggested resolution

The C++ reader: reject a block with two rotations or two RF shims, as MATLAB
Pulseq does and as the specification's "only one … can be specified" says;
and fix the text of the RF-shim warning.

## Report

Draft, to pulseq/pulseq:

> **Two ROTATIONS or RF_SHIMS objects in one block**
>
> Section 2.8.4 allows one rotation and one RF shimming object per block.
> `ExternalSequence::GetBlock` keeps the first of two and warns
> (`ExternalSequence.cpp:1871-1878`, 1909-1915); MATLAB's `getBlock` fails
> with "Only one rotation extension object per block is allowed"
> (`Sequence.m:1300`; RF shims at line 1287). Could the C++ reader reject such
> a block too? Its RF-shim warning also says "only one soft delay per block is
> supported" (line 1911), the text of the soft-delay case. Reproducers
> attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D48, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here). The
  file with two RF shims, and the wrong text of its warning, are new.
