---
id: DIS-0063
title: An extension that a reader does not know, and that the file does not require
kind: implementation-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "the interpreter must detect an unknown extension and may ignore it, with a warning"
  - key: cpp-reader
    behavior: "warns and ignores it"
  - key: matlab-pulseq
    behavior: "warns and ignores it"
  - key: pypulseq
    behavior: "rejects the file (ValueError 'Unknown section code'), also for ROTATIONS and RF_SHIMS"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq]
  reason: "MATLAB Pulseq writes RF_SHIMS (mr.makeRfShim, addBlock) without listing it in RequiredExtensions. pypulseq rejects this spec-valid file with 'Unknown section code'."
pulseq_analysis:
  ids: [D2.17]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0063: An extension that a reader does not know, and that the file does not require

## Summary

The specification lets an interpreter ignore an extension that it does not
know, with a warning, unless the file lists it in `RequiredExtensions`. The
C++ reader and MATLAB Pulseq do so. pypulseq rejects every file with an
`extension` section other than TRIGGERS, LABELSET, LABELINC and DELAYS,
including ROTATIONS and RF_SHIMS, which the specification defines and MATLAB
Pulseq writes.

## What each source does

| Source | What it does |
|---|---|
| Specification | "The interpreter MUST detect unknown extensions and MAY chose to ignore them. It is recommended that the interpreter issues a warning in this case." Only the extensions in `RequiredExtensions` "must be supported by the interpreter" (section 2.8.4, `spec:460`). |
| C++ reader | "WARNING: unknown extension ignored" for the header (`cpp:1248`) and a message for each row (`cpp:1376`), and goes on; the block's reference to it is skipped with a warning (`cpp:1924`). |
| MATLAB Pulseq | "Ignoring unknown extension, input string: …", and skips the section (`read.m:186-189`). |
| pypulseq | `read` knows only `extension TRIGGERS`, `LABELSET`, `LABELINC` and `DELAYS` (`read_seq.py:191-226`); any other `extension` header is `ValueError: Unknown section code` (`read_seq.py:228`). |

The specification allows a reader to reject such a file (it "MAY" ignore
it), so pypulseq does not break a rule of the specification. The record is
the disagreement between the implementations: the same file is read by the
scanner's reader and by MATLAB Pulseq, and rejected by pypulseq.

## Reproducer

[`reproducers/DIS-0063/unknown_extension.seq`](../reproducers/DIS-0063/unknown_extension.seq):
a 1.5.1 file of one trapezoid block whose extension list refers to an
extension `FOO`, which is not in `RequiredExtensions`:

```
[EXTENSIONS]
1 1 1 0

extension FOO 1
1 2 3
```

Commands as in DIS-0057.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | May be ignored, with a warning. | — |
| C++ reader | — | Read (exit 0; sanitized exit 0), with "WARNING: unknown extension ignored" and "unrecognized extension type 1 in block 0". 2026-10-14. |
| MATLAB Pulseq | — | Read, with "Ignoring unknown extension, input string: FOO 1" and "unknown extension ID 1". 2026-10-14. |
| pypulseq | — | `ValueError: Unknown section code: extension FOO 1` (`read_seq.py:228`). 2026-10-14. |

The files of DIS-0066, DIS-0067 and DIS-0069 show the same rejection for
`extension ROTATIONS` and `extension RF_SHIMS`.

## Impact

pypulseq cannot read a file with an extension that it does not implement, even
one that the file marks as optional. That includes every file with rotations
or RF shims, which MATLAB Pulseq writes: for example
`tests/expected_output/seq_make_radial.seq` of pulseq/pulseq at `c7469123`,
a 1.5.1 file whose ROTATIONS are not in `RequiredExtensions`, is rejected by
pypulseq 1.5.0.post1 and master with the same error (run, 2026-10-14). A user who checks such a file in pypulseq cannot
load it, while the scanner plays it.

## Suggested resolution

pypulseq: skip an `extension` section that it does not know, with a warning,
unless the extension is in `RequiredExtensions` (DIS-0065), as the C++ reader
and MATLAB Pulseq do.

## Report

Draft, to pulseq/pypulseq:

> **`read` rejects a file with an extension that pypulseq does not know**
>
> Section 2.8.4 of the specification says that an interpreter "MUST detect
> unknown extensions and MAY chose to ignore them", with a warning, and that
> only the extensions in `RequiredExtensions` must be supported. The C++
> reader of the interpreter and MATLAB Pulseq warn and skip such a section.
> pypulseq's `read` raises `ValueError: Unknown section code: extension FOO 1`
> (`read_seq.py`, line 228), and so for every file with `extension
> ROTATIONS` or `extension RF_SHIMS`, which MATLAB Pulseq writes. Could `read`
> skip an unknown extension that the file does not require, with a warning?
> Reproducer attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D45, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here). The kind
  is `implementation-vs-implementation`, not the inventory's
  `spec-vs-implementation`: the specification allows a reader to reject an
  unknown extension ("MAY chose to ignore them").
