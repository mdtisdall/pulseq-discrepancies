---
id: DIS-0058
title: An event that lasts longer than its block
kind: spec-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "not allowed; the interpreters must throw an error"
  - key: cpp-reader
    behavior: "reads it with no error or warning"
  - key: matlab-pulseq
    behavior: "read accepts it; checkTiming reports it"
  - key: pypulseq
    behavior: "read accepts it; check_timing reports it"
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
  level: low
  written_by: []
  reason: "Neither writer writes a block shorter than its events. The readers accept such a file without the error that the spec requires, but no master writer makes it."
pulseq_analysis:
  ids: [D25]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0058: An event that lasts longer than its block

## Summary

The specification forbids an event that lasts longer than its block, and says
that the interpreters must throw an error when they detect one. The C++
reader, MATLAB Pulseq's `read` and pypulseq's `read` accept such a file with
no error or warning. The timing checks of the two toolboxes report it, but
only when the user calls them.

## What each source does

| Source | What it does |
|---|---|
| Specification | "No event comprising this block is allowed to last longer than the specified block duration. The interpreters must to throw an error, should they detect such condition." (section 2.7, `spec:318`) |
| C++ reader | `load` and `decodeBlock` do not compare the end of an event with the duration of its block (run: exit 0, no message). |
| MATLAB Pulseq | `read` and `getBlock` do not check it (run). `checkTiming` (`Sequence.m:211`) reports "inconsistency between the stored block duration and the duration of the block content" (`Sequence.m:242-243`). |
| pypulseq | `read` and `get_block` do not check it (run). `check_timing` (`check_timing.py:23`) reports `BLOCK_DURATION_MISMATCH`. |

## Reproducer

Two 1.5.1 files in [`reproducers/DIS-0058/`](../reproducers/DIS-0058/):
`rf_longer_than_block.seq`, an RF block pulse of 100 µs in a block of 50 µs,

```
[BLOCKS]
1 5 1 0 0 0 0 0

[RF]
1 1000 1 2 0 50 0 0 0 0 0 e
```

and `adc_longer_than_block.seq`, an ADC of 8 samples of 25 µs (200 µs) in a
block of 100 µs (`1 10 0 0 0 0 1 0`; `[ADC]` row `1 8 25000 0 0 0 0 0 0`).

Commands as in DIS-0057 (`read`, each block, the waveforms, and the timing
check of each toolbox).

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | An error for both files. | — |
| C++ reader | — | Both read, no message (exit 0; sanitized exit 0). 2026-10-14. |
| MATLAB Pulseq | — | Both read. `checkTiming`: false, "inconsistency between the stored block duration and the duration of the block content" for each. 2026-10-14. |
| pypulseq | — | Both read. `check_timing`: false, `BLOCK_DURATION_MISMATCH` for each. 2026-10-14. |

## Impact

The scanner's reader accepts a file in which an RF pulse or an ADC goes on
after the end of its block, into the next block. The specification asks the
interpreter to stop such a file. A user who reads such a file in MATLAB
Pulseq or pypulseq is told only if they call the timing check.

## Suggested resolution

The C++ reader: reject a block whose events end after the block duration, as
section 2.7 asks ("must throw an error"). The `read` of MATLAB Pulseq and
pypulseq could do the same, or warn, since they also play the file.

## Report

Draft, to pulseq/pulseq (C++ reader, MATLAB Pulseq) and pulseq/pypulseq:

> **An event that lasts longer than its block is accepted**
>
> Section 2.7 says: "No event comprising this block is allowed to last longer
> than the specified block duration. The interpreters must to throw an error,
> should they detect such condition." `ExternalSequence::load` and
> `decodeBlock` accept a block of 50 µs with an RF pulse of 100 µs, and a
> block of 100 µs with an ADC of 200 µs, with no message. MATLAB's `read` and
> pypulseq's `read` accept them too; only `checkTiming` / `check_timing`
> report them. Could the readers reject them, as the specification asks?
> Reproducers attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D25, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here; the
  citations give the lines of 1.5.0.post1).
