---
id: DIS-0014
title: "[SHAPES] as the last section, with no blank line after its last sample"
kind: implementation-vs-implementation
severity: crash
status: resolved
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "[SIGNATURE] is optional; a shape ends with a blank line"
  - key: cpp-reader
    behavior: "reads the file"
  - key: matlab-pulseq
    behavior: "reads the file"
  - key: pypulseq
    version: "1.5.0.post1"
    behavior: "does not end (the shape loop never sees the end of the file)"
  - key: pypulseq
    version: "master c977214"
    behavior: "reads the file (fixed by pulseq/pypulseq#359)"
report_to:
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: https://github.com/pulseq/pypulseq/issues/358
priority:
  level: medium
  written_by: []
  reason: "In pypulseq 1.5.0.post1, read hangs when [SHAPES] ends the file with no blank line. The spec is silent on the end of the file. Both writers end each shape with a blank line."
  fixed:
    by: "https://github.com/pulseq/pypulseq/pull/359 (commit 36d9fa3)"
    last_release: "pypulseq 1.5.0.post1"
found: 2026-02-02
checked: 2026-10-13
---

# DIS-0014: [SHAPES] as the last section, with no blank line after its last sample

## Summary

A file with no `[SIGNATURE]` often ends with `[SHAPES]`. When its last sample
is the last line of the file, with no blank line after it, the C++ reader and
MATLAB Pulseq read the file, but `read` of pypulseq 1.5.0.post1 never ends:
its loop over the samples of a shape does not stop at the end of the file.
Fixed upstream by pulseq/pypulseq#359 (merged 2026-02-03), which is not in a
release yet: 1.5.0.post1 is still the latest.

## What each source does

| Source | What it does |
|---|---|
| Specification | The file "may end with an optional section `[SIGNATURE]`" (section 2.4, `spec:213`), so a file can end with `[SHAPES]`. "The end of the shape definition is declared with a blank line" (section 2.9, `spec:602`); it does not say whether the end of the file also ends a shape. |
| C++ reader | `getline` returns false at the end of the file (`cpp:2321-2327`), which ends the loop over the samples (`cpp:955`); the stream is cleared after `[SHAPES]` (`cpp:980`). |
| MATLAB Pulseq | `fgetl` returns -1 at the end of the file, which is not a `char`, so the loop over the samples ends (`read.m:653`). |
| pypulseq 1.5.0.post1 | `__strip_line` returns -1 at the end of the file, and the loop `while line != '' and line != '#'` (`read_seq.py:688` of 1.5.0.post1) never ends. |
| pypulseq master `c977214` | The loop also stops at -1 (`read_seq.py:690`), the fix of #359 (`36d9fa3`). |

## Reproducer

[`reproducers/DIS-0014/shapes_last.seq`](../reproducers/DIS-0014/shapes_last.seq):
one RF block pulse, with `[SHAPES]` last and no `[SIGNATURE]`; the file ends:

```
shape_id 2
num_samples 100
0
0
98
```

with a line end after `98` and no blank line. (With a blank line after it,
pypulseq 1.5.0.post1 reads the file.) The issue
[pulseq/pypulseq#358](https://github.com/pulseq/pypulseq/issues/358) has a
file of the same form.

Commands as in DIS-0001; pypulseq 1.5.0.post1 (the tag `v1.5.0.post1`) and
master `c977214` of pulseq/pypulseq, each installed in its own environment.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | A file without `[SIGNATURE]`; the last shape ends at the end of the file. | — |
| C++ reader | — | Read (exit 0), plain and sanitized. 2026-10-13. |
| MATLAB Pulseq | — | Read. 2026-10-13. |
| pypulseq 1.5.0.post1 | — | `read` does not end in 20 s (killed). 2026-10-13. |
| pypulseq master `c977214` | — | Read. 2026-10-13. |

## Impact

Users of the released pypulseq (1.5.0.post1) hang on such a file, for example
one written without a signature and then trimmed, or written by another tool.
The fix is on the default branch of pulseq/pypulseq and will be in the next
release.

## Suggested resolution

Done upstream (#359). The specification could say that the end of the file
also ends the last shape.

## Report

- pulseq/pypulseq#358 (opened 2026-02-02, closed 2026-02-03): the issue.
- pulseq/pypulseq#359 (merged 2026-02-03 as `36d9fa3`): the fix, "Avoid
  infinite loop when reading seq files without signature". Not in a release:
  the latest release is 1.5.0.post1 (2026-01-29).

## History

- 2026-02-02: reported upstream, pulseq/pypulseq#358.
- 2026-02-03: fixed upstream by pulseq/pypulseq#359 (`36d9fa3`).
- 2026-10-13: recorded from pulseq-analysis `TODO.md` (F-TODO-10, commit
  `5bd053a`); the hang run in pypulseq 1.5.0.post1, and the file read by
  pypulseq master `c977214`, the C++ reader and MATLAB Pulseq.
