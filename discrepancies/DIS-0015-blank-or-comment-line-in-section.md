---
id: DIS-0015
title: "A blank or # line inside a section"
kind: spec-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "a line that starts with # is a comment; silent on a blank line in a table"
  - key: cpp-reader
    behavior: "a blank line ends a table and the rows after it are dropped silently; a # row in [BLOCKS] is rejected"
  - key: matlab-pulseq
    behavior: "a blank or # line ends a section; the next row is an unknown section: rejects"
  - key: pypulseq
    behavior: "a blank line or a lone # ends a section, a # comment row fails: rejects"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
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
  level: medium
  written_by: []
  reason: "The spec allows # comments anywhere and is silent on blank lines. No writer writes either inside a table. All readers reject a comment in [BLOCKS]; pypulseq fails in np.fromstring."
pulseq_analysis:
  ids: [D2.5]
  commit: 5bd053a
found: 2026-10-12
checked: 2026-10-14
---

# DIS-0015: A blank or # line inside a section

## Summary

The specification makes a comment of any line that starts with `#`, and does
not say that a blank line ends a table. When a blank line comes between two
rows of `[BLOCKS]`, the C++ reader ends the table there and plays only the
blocks before it, with no message; MATLAB Pulseq and pypulseq reject the file.
A comment line between two rows is rejected by all three readers in
`[BLOCKS]`; in `[DEFINITIONS]` the C++ reader reads it as a definition named
`#`, and the two toolboxes reject the file.

## What each source does

| Source | What it does |
|---|---|
| Specification | "Comments are specified by a line starting with a hash." (section 2.1, `spec:171`), with no limit on where. Its own example of `[SIGNATURE]` has two comment lines inside the section (section 2.4, `spec:216-220`). "Each subsequence line declares a single block" (section 2.7, `spec:295`); the event sections have one event on each line (section 2.8, `spec:331`). Only a shape is ended by a blank line (section 2.9, `spec:602`); the specification does not say that a blank line can be in, or ends, another section. |
| C++ reader | The tables `[RF]`, `[GRADIENTS]`, `[TRAP]`, `[ADC]`, `[DEFINITIONS]` and `[BLOCKS]` end at an empty line or a `[` line (`cpp:1004`, `cpp:1064`, `cpp:1112`, `cpp:1141`, `cpp:1406`, `cpp:1558`). The rows after a blank line are never read: only a `[` line starts a section (`cpp:1762-1768`), and no message is given. A `#` line is not skipped there: in `[BLOCKS]` it is decoded as a row and the file is rejected ("failed to decode event table entry", `cpp:1565-1577`); in `[DEFINITIONS]` it becomes a definition with the key `#` (`cpp:1427-1445`). `[VERSION]` (`cpp:878`, `cpp:908`, with `skipComments`, `cpp:1725-1731`), the extension region (`cpp:1216-1221`) and `[SIGNATURE]` (`cpp:1610`) skip `#` lines. |
| MATLAB Pulseq | A section ends at an empty line or a line that starts with `#` (`read.m:461`, `read.m:503`, `read.m:564`, `read.m:606`). The main loop then skips blank and `#` lines and takes the next line as a section header (`read.m:50`, `skipComments`, `read.m:675-700`); a data row is "Unknown section code" (`read.m:192`). |
| pypulseq | A table ends at an empty line or a line that is exactly `#` (`read_seq.py:536`, `read_seq.py:597`, `read_seq.py:647`); `[DEFINITIONS]` ends at any line that starts with `#` (`read_seq.py:463`). The main loop then takes the next line that is not blank or `#` as a section header, and a data row is "Unknown section code" (`read_seq.py:228`). A line `# a comment` inside `[BLOCKS]` is decoded as a row by `np.fromstring` and fails (`read_seq.py:537`). The lines are the same on master. |

## Reproducer

Three files in [`reproducers/DIS-0015/`](../reproducers/DIS-0015/), each of
three blocks of one trapezoid (400 µs, 100000 and 200000 Hz/m) and no shapes:

- `blank_in_blocks.seq`: a blank line between block 1 and block 2.
- `comment_in_blocks.seq`: a line `# a comment` between block 1 and block 2.
- `comment_in_definitions.seq`: a line `# a comment` between
  `BlockDurationRaster` and `GradientRasterTime` in `[DEFINITIONS]`.

The `[BLOCKS]` section of `blank_in_blocks.seq`:

```
[BLOCKS]
1 40 0 1 0 0 0 0

2 40 0 2 0 0 0 0
3 40 0 1 0 0 0 0
```

Commands as in DIS-0001 (C++ reader plain and sanitized of pulseq-analysis
`65fc7e8`, with `--dump`; MATLAB Pulseq under Octave 11.3.0; pypulseq
1.5.0.post1 and master `c977214`).

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Three blocks in each file; the `#` lines are comments. For the blank line, the specification is silent. | — |
| C++ reader | — | `blank_in_blocks.seq`: read (exit 0), 1 block (block 1, `duration_ru` 40, trapezoid 100000 Hz/m); blocks 2 and 3 are dropped, with no message. `comment_in_blocks.seq`: rejected (exit 1), "failed to decode event table entry: # a comment". `comment_in_definitions.seq`: read (exit 0), 3 blocks, with a definition `#` = `a comment`. Same exit codes with the sanitized build. 2026-10-14. |
| MATLAB Pulseq | — | `blank_in_blocks.seq` and `comment_in_blocks.seq`: error "Unknown section code: 2 40 0 2 0 0 0 0". `comment_in_definitions.seq`: error "Required definitions GradientRasterTime RadiofrequencyRasterTime are missing in the file" (`read.m:83`). 2026-10-14. |
| pypulseq | — | `blank_in_blocks.seq`: `ValueError: Unknown section code: 2 40 0 2 0 0 0 0` (`read_seq.py:228`). `comment_in_blocks.seq`: `ValueError: string or file could not be read to its end due to unmatched data` (`read_seq.py:537`). `comment_in_definitions.seq`: `ValueError: Unknown section code: GradientRasterTime 1e-05`. 1.5.0.post1 and master the same. 2026-10-14. |

## Impact

MATLAB Pulseq and pypulseq write no blank or `#` line inside a table (their
comments come before each section header, `write.m:56-58`,
`write_seq.py:83-85`), so their files are not affected. A file edited by hand, or
written by another tool, with a blank line inside `[BLOCKS]` is rejected by
both toolboxes, but the scanner's reader plays only the blocks before the
blank line, with no message: a shorter sequence than the file describes. A
comment inside a table, which the specification allows, is rejected by all
three readers in `[BLOCKS]`, and is kept as a definition by the C++ reader in
`[DEFINITIONS]`.

## Suggested resolution

The specification: say where a comment and a blank line can be, for example
"a line that starts with `#` is ignored anywhere in the file; a blank line is
allowed only between sections and at the end of a shape". The C++ reader, MATLAB
Pulseq and pypulseq: skip comment lines inside a table, as the specification
says; and treat a data row after a blank line in the same way (read it, or
reject the file), not drop it without a message as the C++ reader does.

## Report

Draft, to pulseq/pulseq (specification, C++ reader, MATLAB toolbox):

> **A blank line or a comment line inside a table**
>
> The specification says that a line that starts with `#` is a comment
> (section 2.1), and its own `[SIGNATURE]` example has comments inside the
> section. It says nothing about a blank line inside a table. The readers do
> three different things with such a line inside `[BLOCKS]`:
>
> - `ExternalSequence::load` ends the table at a blank line
>   (`ExternalSequence.cpp:1557-1560`) and never reads the rows after it: a
>   file with a blank line after block 1 of 3 is played as 1 block, with no
>   message. A `#` line in `[BLOCKS]` is decoded as a block and the file is
>   rejected; in `[DEFINITIONS]` it becomes a definition named `#`.
> - MATLAB `read.m` ends the section at a blank or `#` line (line 503) and
>   then stops at the next row with "Unknown section code" (line 192).
>
> Could the specification say where comments and blank lines may be, and the
> readers follow it? At least, the C++ reader should not drop rows without a
> message. Reproducers attached.

Draft, to pulseq/pypulseq:

> **`read` rejects a comment line inside a table**
>
> The Pulseq specification makes a comment of any line that starts with `#`
> (section 2.1). `Sequence.read` ends a table only at a line that is exactly
> `#` (`read_seq.py:536`, `:597`, `:647`) and then fails with "Unknown
> section code" on the next row (`:228`); a line `# a comment` inside
> `[BLOCKS]` is decoded as a block and fails in `np.fromstring` (`:537`).
> Could `read` skip comment lines inside a table? Reproducers attached.

## History

- 2026-10-12: found by pulseq-analysis (old ID D06, commit `49a7e2c`; also
  its section 4, S4-8). The case of a data line before the first section,
  also in D06, is DIS-0045.
- 2026-10-14: confirmed against the pinned sources; reproducers written and
  run in the C++ reader (plain and sanitized), MATLAB Pulseq and pypulseq.
  The C++ reader plays 1 of the 3 blocks of `blank_in_blocks.seq`; MATLAB
  Pulseq and pypulseq reject it. The specification was added to `report_to`:
  it is silent on a blank line inside a table.
  The runs used 1.5.1 files; the code paths cited do not depend on the
  version.
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq; the two behave the same here, and the cited
  lines are the same in both.
