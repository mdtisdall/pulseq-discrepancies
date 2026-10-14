---
id: DIS-0045
title: A data line before the first section
kind: spec-gap
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "no line outside a section, except a comment"
  - key: cpp-reader
    behavior: "never reads the line; reads the file"
  - key: matlab-pulseq
    behavior: "rejects: Unknown section code"
  - key: pypulseq
    behavior: "rejects: ValueError Unknown section code"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
pulseq_analysis:
  ids: [D3.2]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0045: A data line before the first section

## Summary

The specification has no line outside a section, except a comment, and says
nothing of a data line before the first section header. The C++ reader finds
the sections by their headers and never reads such a line; MATLAB Pulseq and
pypulseq read the file line by line, take the line for a section header, and
reject the file.

## What each source does

| Source | What it does |
|---|---|
| Specification | "Comments are specified by a line starting with a hash" (section 2.1, `spec:171`). Every other line belongs to a section (sections 2.3 to 2.9). Silent on a line before the first header. |
| C++ reader | Indexes the lines that start with `[` (`cpp:1762-1769`) and reads each section from its header (for example `cpp:877`, `cpp:999`): a line before the first header is never read. |
| MATLAB Pulseq | `skipComments` gives the first line that is not blank or a comment (`read.m:50`); the line is not a section that it knows, so "Unknown section code" (`read.m:192`). |
| pypulseq | The same (`read_seq.py:70`): `ValueError("Unknown section code: …")` (`read_seq.py:228`). |

## Reproducer

[`reproducers/DIS-0045/line_before_first_section.seq`](../reproducers/DIS-0045/line_before_first_section.seq):
the 1.5.1 file of DIS-0043 with a line `1 2 3` after the first comment:

```
# Pulseq sequence file

1 2 3

[VERSION]
```

Commands as in DIS-0001.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent. | — |
| C++ reader | — | Read, each block decoded (exit 0), plain and sanitized. 2026-10-14. |
| MATLAB Pulseq | — | Error "Unknown section code: 1 2 3" (`read.m:192`). 2026-10-14. |
| pypulseq | — | `ValueError: Unknown section code: 1 2 3` (`read_seq.py:228`). Both versions. 2026-10-14. |

## Impact

Both writers start the file with comment lines and a blank line, then
`[VERSION]` (`write.m:19-25`, `write_seq.py:53-56`), so their files are not
affected. A file with a stray line before the first section, for example a
header of another tool that is not a comment, is played by the scanner's
reader and rejected by both toolboxes.

## Suggested resolution

The specification: say that every line before the first section is blank or a
comment, and what a reader does with another (reject it, or ignore it as the
C++ reader does).

## Report

Draft, to pulseq/pulseq:

> **Specification: a data line before the first section**
>
> A line such as `1 2 3` before the first section header is not described by
> the specification. The C++ reader ignores it (it reads only from the section
> headers); MATLAB Pulseq and pypulseq reject the file with "Unknown section
> code: 1 2 3" (`read.m:192`). Could the specification say that only blank
> lines and comments come before the first section, and whether a reader must
> reject another line?

## History

- 2026-10-09: found by pulseq-analysis (old ID D06, commit `49a7e2c`; D3.2 at
  `5bd053a`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and
  master `c977214`, which agree here.
