---
id: DIS-0041
title: "A [VERSION] value such as 5.0, an unknown key, or a revision of two digits"
kind: spec-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "three lines major, minor, revision, each with its number; no other key"
  - key: cpp-reader
    behavior: "minor 5.0 is 5; rejects an unknown key; revision 10 is 10"
  - key: matlab-pulseq
    behavior: "minor 5.0 is 5; skips an unknown key; revision 10 is 10"
  - key: pypulseq
    behavior: "rejects minor 5.0 and an unknown key; reads revision 10 as 1"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
  - repo: pulseq/pulseq
    component: specification
    issue: null
pulseq_analysis:
  ids: [D04]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0041: A [VERSION] value such as 5.0, an unknown key, or a revision of two digits

## Summary

The `[VERSION]` section has three lines, `major`, `minor` and `revision`, each
with a number. The readers parse these lines in three ways. `minor 5.0` is 5
for the C++ reader and MATLAB Pulseq, and an error for pypulseq. A fourth key
is an error for the C++ reader and pypulseq, and is skipped by MATLAB Pulseq.
`revision 10` is 10 for the C++ reader and MATLAB Pulseq, but pypulseq keeps
only its first character and reads 1.

## What each source does

| Source | What it does |
|---|---|
| Specification | "The versioning scheme is ⟨major⟩.⟨minor⟩.⟨revision⟩", and the section is the three lines `major ⟨major⟩`, `minor ⟨minor⟩`, `revision ⟨revision⟩` (section 2.3, `spec:191-198`). It does not give the syntax of the numbers or say whether another key can appear. |
| C++ reader | Reads each number with `sscanf("%d")` (`cpp:882-901`), which stops at the `.` of `5.0`: 5. Another key gives "unknown field in the [VERSION] block" and `load` fails (`cpp:902-906`). |
| MATLAB Pulseq | Reads each number with `str2double` (`read.m:479-491`): `5.0` is 5, `10` is 10. A key other than the three is skipped (the `switch` of `read.m:482-489` has no `otherwise`). |
| pypulseq | Reads each number with `int()` (`read_seq.py:497`, `:499`, `:503`): `int('5.0')` raises `ValueError`. Another key raises `RuntimeError("Incompatible version …")` (`read_seq.py:504-505`). A revision of more than one character is cut to its first character (`read_seq.py:501-502`, "Example: x.y.zpostN"): `revision 10` is read as 1. |

## Reproducer

Three changes of a 1.5.1 file of one RF block pulse, in
[`reproducers/DIS-0041/`](../reproducers/DIS-0041/):
`version_minor_5_0.seq` (`minor 5.0`), `version_unknown_key.seq` (a line
`build 7` after `revision 1`) and `version_revision_10.seq` (`revision 10`):

```
[VERSION]
major 1
minor 5.0
revision 1
```

Commands as in DIS-0001. For `version_revision_10.seq`, the version that
each reader took is in the C++ dump (`pulseq-cpp-oracle --dump`), in the
`[VERSION]` that MATLAB Pulseq reads (as the oracle repeats it), and in the
warning of pypulseq "File version … is higher than installed package version".

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | `revision 10`: version 1.5.10. `minor 5.0`, and a fourth key: not described. | — |
| C++ reader | — | `version_minor_5_0.seq`: read (exit 0), version 1005001. `version_unknown_key.seq`: "*** WARNING: unknown field in the [VERSION] block", `load` fails (exit 1). `version_revision_10.seq`: read, version 1005010. Plain and sanitized. 2026-10-14. |
| MATLAB Pulseq | — | All three read; `revision 10` is 10. 2026-10-14. |
| pypulseq | — | `version_minor_5_0.seq`: `ValueError: invalid literal for int() with base 10: '5.0'` (`read_seq.py:499`). `version_unknown_key.seq`: `RuntimeError: Incompatible version. Expected: 151` (`read_seq.py:505`). `version_revision_10.seq`: read, with the warning "File version 1.5.1 is higher than installed package version 1.5.0". Both versions. 2026-10-14. |

## Impact

Both writers write each number as an integer (`write.m:26-28`;
`write_seq.py:57-59`, which writes the revision of the package, 0 for
1.5.0.post1), so their files are not affected. A file from another tool, or
edited by hand, with `5.0` or another key is accepted by one reader and
rejected by another. The cut revision has no effect yet, since no format
revision has two digits; from a revision 1.x.10 on, pypulseq would read such a
file as revision 1 and apply the rules of that revision.

## Suggested resolution

The specification: say that each value is a non-negative integer in decimal
digits, and whether a reader rejects or skips another key. pypulseq: read the
whole revision (for example the leading digits of `0post1`, if that form is
still to be read), not its first character.

## Report

Draft, to pulseq/pypulseq:

> **`read` reads `revision 10` as revision 1, and rejects `minor 5.0`**
>
> `__read_version` cuts a revision of more than one character to its first
> character (`read_seq.py:501-502`), so `revision 10` is read as 1 (the warning
> "File version 1.5.1 is higher than installed package version" shows it). It
> reads the numbers with `int()`, so `minor 5.0`, which the C++ reader and
> MATLAB Pulseq read as 5, raises `ValueError`. Reproducers attached.

Draft, to pulseq/pulseq (specification):

> **Specification: the syntax of the `[VERSION]` values**
>
> Section 2.3 gives the three lines of `[VERSION]` but not the syntax of the
> numbers, or what a reader does with another key. The readers differ: the C++
> reader reads `minor 5.0` as 5 and rejects another key; MATLAB Pulseq reads
> `5.0` as 5 and skips another key; pypulseq rejects both. Could the
> specification say that each value is an integer, and whether another key is
> an error?

## History

- 2026-10-09: found by pulseq-analysis (old ID D04, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducers run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and
  master `c977214`, which agree here. The kind is `spec-vs-implementation` for
  the revision of two digits, which pypulseq misreads; the specification is
  silent on the other two cases, so it is also in `report_to`.
