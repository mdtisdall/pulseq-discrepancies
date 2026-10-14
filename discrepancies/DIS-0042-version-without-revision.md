---
id: DIS-0042
title: "A [VERSION] section with no revision line"
kind: spec-gap
severity: acceptance
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "gives the three lines; silent on a missing one"
  - key: cpp-reader
    behavior: "takes revision 0: a 1.5.1 file is read as 1.5.0, without the checks of 1.5.1"
  - key: matlab-pulseq
    behavior: "the version becomes empty; reads [RF] with the layout of 1.3 and fails"
  - key: pypulseq
    behavior: "takes revision 0"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
pulseq_analysis:
  ids: [S4-2]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0042: A [VERSION] section with no revision line

## Summary

The specification gives three lines in `[VERSION]` and does not say what a
missing one means. With no `revision` line, the C++ reader and pypulseq take
revision 0, so a file meant as 1.5.1 is read as 1.5.0; the C++ reader then
skips the check of `RequiredExtensions` that 1.5.1 introduced, and plays a file
that it rejects when the line is there. MATLAB Pulseq adds an empty revision
to the version, which makes the version empty: every test on it is false, it
reads the `[RF]` row with the layout of 1.3, and fails.

## What each source does

| Source | What it does |
|---|---|
| Specification | The three lines `major`, `minor`, `revision` (section 2.3, `spec:193-198`). "Providing the version of the standard is vital for sequence execution" (`spec:200`). Silent on a missing line. `RequiredExtensions` is a concept "since the format revision v1.5.1" (`spec:460`). |
| C++ reader | Starts the three numbers at 0 (`cpp:96-98`) and sets only those that the section has (`cpp:879-909`), so the version is 1.5.0 (`cpp:910`). The check of `RequiredExtensions` runs only from 1.5.1 (`cpp:1505`). |
| MATLAB Pulseq | Starts the numbers empty (`read.m:476-478`). `version_combined=1000000*version_major+1000*version_minor+version_revision` (`read.m:101`) with an empty revision is empty, so the tests `version_combined >= 1005000` and `>= 1004000` are false, and `[RF]` is read with the scale of 1.3 and before (`read.m:119-125`): 6 scales against the 10 values after the ID fail at `read.m:570`. |
| pypulseq | Starts the numbers at 0 (`read_seq.py:493`): the version is 1.5.0. |

## Reproducer

[`reproducers/DIS-0042/`](../reproducers/DIS-0042/):
`version_no_revision.seq`, a 1.5.1 file of one RF block pulse without the
`revision` line; `version_no_revision_required_unknown.seq`, the same with
`RequiredExtensions FOO` (an extension that no reader knows); and
`version_1_5_1_required_unknown.seq`, that file with `revision 1`:

```
[VERSION]
major 1
minor 5

[DEFINITIONS]
…
RequiredExtensions FOO
```

Commands as in DIS-0001; the version that the C++ reader took is in its dump
(`pulseq-cpp-oracle --dump`).

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent. With `revision 1`, a reader that does not know `FOO` "MUST generate an error" (`spec:460`). | — |
| C++ reader | — | `version_no_revision.seq`: read, version 1005000 (exit 0). `version_no_revision_required_unknown.seq`: read (exit 0). `version_1_5_1_required_unknown.seq`: "The extension 'FOO' is unknown to this interpreter but is defined as REQUIRED", `load` fails (exit 1). Plain and sanitized. 2026-10-14. |
| MATLAB Pulseq | — | Both files without `revision`: error "product: nonconformant arguments (op1 is 1x6, op2 is 1x10)" (`read.m:570`, from `read.m:125`). 2026-10-14. |
| pypulseq | — | Both files without `revision`: read. Both versions. 2026-10-14. |

## Impact

Both writers write the three lines (`write.m:26-28`, `write_seq.py:57-59`).
A file from another tool, or edited by hand, without `revision` is read as
1.5.0 by the scanner's reader and pypulseq, and rejected by MATLAB Pulseq. The
scanner's reader then skips the rules of 1.5.1: a file that requires an
extension that the scanner does not know is played, where the same file with
`revision 1` is refused. (MATLAB Pulseq and pypulseq do not check
`RequiredExtensions`, with or without the line; that is a separate
condition.)

## Suggested resolution

The specification: say that the three lines are required, or the value of a
missing one. MATLAB Pulseq: start the numbers at 0, as the other readers do,
or reject a section with a missing line with a message.

## Report

Draft, to pulseq/pulseq:

> **A `[VERSION]` section with no `revision` line**
>
> The specification does not say what a missing line of `[VERSION]` means.
> The C++ reader takes 0 (`ExternalSequence.cpp:96-98`), so a 1.5.1 file
> without `revision` is read as 1.5.0, and the check of `RequiredExtensions`
> (line 1505, from 1.5.1) is skipped: a file that requires an unknown
> extension is accepted without the line and rejected with it. MATLAB Pulseq
> computes an empty version (`read.m:101`, with `version_revision = []`), reads
> `[RF]` with the layout of 1.3 (line 125) and fails with "nonconformant
> arguments". Could the specification require the three lines, or give the
> default? Reproducers attached.

## History

- 2026-10-09: found by pulseq-analysis (section 4 of `docs/discrepancies.md`,
  commit `49a7e2c`, the runs of 2026-10-09: the C++ reader has version 1.5.0
  without the `revision` line).
- 2026-10-14: confirmed against the pinned sources; reproducers run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and
  master `c977214`, which agree here. The failure of MATLAB Pulseq is new
  (pulseq-analysis did not run it), so MATLAB Pulseq is added to `report_to`;
  the inventory's "C++" is replaced by the specification and MATLAB Pulseq,
  because the C++ reader's default of 0 is one answer to the gap, not an error.
