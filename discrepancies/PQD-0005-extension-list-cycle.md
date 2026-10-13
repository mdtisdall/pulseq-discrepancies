---
id: PQD-0005
title: A cycle in an extension list
kind: spec-vs-implementation
severity: crash
status: withdrawn
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "extensions form a zero-terminated single-linked list"
  - key: cpp-reader
    behavior: "follows the list with no end"
  - key: matlab-pulseq
    behavior: "follows the list with no end"
  - key: pypulseq
    behavior: "read ends; get_block follows the list with no end"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D5.4]
  commit: 5bd053a
found: 2026-10-08
checked: 2026-10-13
---

# PQD-0005: A cycle in an extension list

## Summary

Withdrawn: not a discrepancy. A file whose extension list has a cycle is not
a file that the specification describes (the list is "zero-terminated"), no
writer writes one, and every implementation does the same with it: it follows
the list and does not end. No two sources disagree about the file, so it is a
defect that the three implementations share (no check for a cycle), not a
record of this repository (`docs/record-format.md`, section 1).

## What each source does

| Source | What it does |
|---|---|
| Specification | "Extensions form zero-terminated single-linked list." (section 2.8.4, `spec:478`) |
| C++ reader | `GetBlock` follows `next` until it is 0 (`cpp:1849-1928`), with no check for a cycle. |
| MATLAB Pulseq | `getBlock` follows `next` until it is 0 to count the entries (`Sequence.m:1178-1184`), with no check for a cycle. |
| pypulseq | `read` does not follow the lists; `get_block` follows the list with no end (run). |

## Reproducer

[`reproducers/PQD-0005/extension_cycle.seq`](../reproducers/PQD-0005/extension_cycle.seq):
one RF block pulse whose extension list is 1 → 2 → 1, of one `TRIGGERS`
object:

```
[EXTENSIONS]
1 1 1 2
2 1 1 1

extension TRIGGERS 1
1 1 2 0 10
```

Commands as in PQD-0001.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | The list is zero-terminated: not a file that the specification describes. | — |
| C++ reader | — | No end in 10 s, plain and sanitized builds (killed). 2026-10-13. |
| MATLAB Pulseq | — | No end in about 10 minutes under Octave 11.3.0 (killed). 2026-10-13. |
| pypulseq | — | `read` ends; `get_block` has no end in 20 s (killed). 2026-10-13. |

## Impact

None between the sources: each implementation hangs on such a file. A check
for a cycle (or a bound on the length of a list) in each reader would be a
robustness fix, which can be suggested to the maintainers apart from this
repository.

## Suggested resolution

Not applicable (withdrawn).

## Report

Not reported: withdrawn.

## History

- 2026-10-08: found by pulseq-analysis (old ID D23, commit `49a7e2c`); the
  inventory reserved this ID for it.
- 2026-10-13: run in the C++ reader, MATLAB Pulseq and pypulseq 1.5.0.post1 and master `c977214`s:
  all three hang. Withdrawn under the scope rule of the migration: a crash is
  a record only when the file is allowed by the specification, is written by
  a writer, or another implementation handles it differently. None holds.
- 2026-10-13: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, not at the fork that `sources.yaml` pins;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
