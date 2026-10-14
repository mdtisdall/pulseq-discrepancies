---
id: DIS-0057
title: A file with no block
kind: spec-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "the sequence must declare at least one block"
  - key: cpp-reader
    behavior: "reads it as a sequence of 0 blocks"
  - key: matlab-pulseq
    behavior: "reads it as a sequence of 0 blocks"
  - key: pypulseq
    behavior: "reads it as a sequence of 0 blocks"
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
  written_by: [matlab-pulseq]
  reason: "MATLAB Pulseq writes a sequence with no block, which the spec forbids. All three readers read it as 0 blocks with no error."
pulseq_analysis:
  ids: [D24]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0057: A file with no block

## Summary

The specification says that a sequence must declare at least one block. A
file whose `[BLOCKS]` section is empty is read without an error or a warning
by the C++ reader, MATLAB Pulseq and pypulseq, as a sequence of 0 blocks.

## What each source does

| Source | What it does |
|---|---|
| Specification | "The sequence must declare at least one block. Any non-zero number of blocks may be defined." (section 2.7, `spec:318`) |
| C++ reader | `load` and the decoding of the blocks do not check the number of blocks (run: exit 0, 0 blocks). |
| MATLAB Pulseq | `read` does not check the number of blocks (run: 0 blocks). `checkTiming` fails on the result with "'ev' undefined" (`checkTiming.m:377`). |
| pypulseq | `read` does not check the number of blocks (run: 0 blocks); `check_timing` reports no error. |

## Reproducer

[`reproducers/DIS-0057/no_blocks.seq`](../reproducers/DIS-0057/no_blocks.seq):
a 1.5.1 file with `[VERSION]`, the four required definitions, an empty
`[BLOCKS]` section and a `[SIGNATURE]`:

```
# NUM DUR RF GX GY GZ ADC EXT
[BLOCKS]

[SIGNATURE]
```

Commands as in DIS-0001 (C++ reader plain and sanitized of pulseq-analysis
`65fc7e8`; MATLAB Pulseq under Octave 11.3.0 with `seq.read`, `getBlock` of
each block, `waveforms_and_times` and `checkTiming`; pypulseq 1.5.0.post1 and
master `c977214` with `Sequence.read`, `get_block` of each block,
`waveforms_and_times` and `check_timing`).

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Not a valid file: no block. | — |
| C++ reader | — | Read, 0 blocks (exit 0; sanitized exit 0). 2026-10-14. |
| MATLAB Pulseq | — | Read, 0 blocks; `checkTiming`: "'ev' undefined near line 377". 2026-10-14. |
| pypulseq | — | Read, 0 blocks; `check_timing`: no error. 2026-10-14. |

## Impact

Small. A file with no block is most likely truncated or written by a faulty
tool. The scanner's reader takes it as a sequence that plays nothing, where
the specification asks for at least one block, so the fault is not reported.

## Suggested resolution

Each reader: reject a file with no block, with a message that cites the rule
of section 2.7. Or, if an empty sequence is to be allowed, the specification
drops the rule.

## Report

Draft, to pulseq/pulseq (C++ reader and MATLAB Pulseq) and pulseq/pypulseq:

> **A file with no block is accepted**
>
> Section 2.7 of the specification says "The sequence must declare at least
> one block." A file whose `[BLOCKS]` section is empty is read without an
> error by `ExternalSequence::load`, by MATLAB's `read` and by pypulseq's
> `read`, as a sequence of 0 blocks. Could the readers reject such a file
> with a message? Reproducer attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D24, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here).
