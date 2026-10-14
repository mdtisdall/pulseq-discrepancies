---
id: DIS-0071
title: A [SIGNATURE] section without Type or Hash
kind: spec-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "the [SIGNATURE] section must contain Type and Hash"
  - key: cpp-reader
    behavior: "no Hash: takes the file as unsigned; no Type: does not verify; reads both"
  - key: matlab-pulseq
    behavior: "reads either, both or neither"
  - key: pypulseq
    behavior: "reads either, both or neither"
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
pulseq_analysis:
  ids: [D54]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0071: A [SIGNATURE] section without Type or Hash

## Summary

The specification says that the `[SIGNATURE]` section must contain the two
fields `Type` and `Hash`. A file whose `[SIGNATURE]` section lacks one of
them is read with no error by the C++ reader, MATLAB Pulseq and pypulseq. The
C++ reader takes a section with no `Hash` as no signature, and does not verify
a hash with no `Type`.

## What each source does

| Source | What it does |
|---|---|
| Specification | "The [SIGNATURE] section must contain two following fields": `Type`, "ID of the hashing algorithm", and `Hash`, "Hash value produced by the hashing function" (section 2.4, `spec:223-232`). |
| C++ reader | Takes the file as signed only when `Hash` is present, and reads `Type` only then (`cpp:1629-1634`). With no `Hash`: "signature block not found" (`cpp:1640-1641`), at the normal message level. With no `Type`: "signature validation is not supported for " and an empty name (`cpp:1645-1646`). The file is read in both cases. |
| MATLAB Pulseq | `read` stores `Type` and `Hash` when each is there, and checks neither (`read.m:85-93`). |
| pypulseq | `read` stores `Type` and `Hash` when each is there, and checks neither (`read_seq.py:94-99`). |

## Reproducer

Two 1.5.1 files of one RF block in
[`reproducers/DIS-0071/`](../reproducers/DIS-0071/), each signed and then
with one line removed from `[SIGNATURE]`:

- `signature_no_hash.seq`: `Type md5` and no `Hash`;
- `signature_no_type.seq`: `Hash …` and no `Type`.

Commands as in DIS-0070.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Not valid: the section lacks a required field. | — |
| C++ reader | — | `signature_no_hash.seq`: "signature block not found", read (exit 0). `signature_no_type.seq`: "signature validation is not supported for ", read (exit 0). `signature_ok` false for both; sanitized exit 0. 2026-10-14. |
| MATLAB Pulseq | — | Both read. 2026-10-14. |
| pypulseq | — | Both read. 2026-10-14. |

## Impact

Small. Both writers write both fields. A section with a missing field is a
broken signature, which every reader takes as a missing one, so a file that
was signed and then damaged is not reported as such; the C++ reader's message
for a missing `Hash` says that there is no signature block, though there is
one.

## Suggested resolution

Each reader: warn (or reject, as the specification's "must" allows) when the
`[SIGNATURE]` section lacks `Type` or `Hash`. Or the specification relaxes the
rule, if a section with one field is meant to be allowed.

## Report

Draft, to pulseq/pulseq (C++ reader, MATLAB Pulseq) and pulseq/pypulseq:

> **A `[SIGNATURE]` section without `Type` or `Hash`**
>
> Section 2.4 says that the `[SIGNATURE]` section must contain `Type` and
> `Hash`. A file whose section lacks one of them is read with no error by
> `ExternalSequence`, which prints "signature block not found" with no
> `Hash`, and "signature validation is not supported for " with no `Type`
> (`ExternalSequence.cpp:1629-1646`), and by MATLAB's and pypulseq's `read`.
> Could the readers warn that the section is incomplete? Reproducers
> attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D54, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here).
