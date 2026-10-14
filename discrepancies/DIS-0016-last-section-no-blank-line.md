---
id: DIS-0016
title: The last section with no blank line after it
kind: spec-gap
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "silent on a blank line after a section other than a shape, and on the end of the file"
  - key: cpp-reader
    behavior: "the end of the file fails its stream; the sections that it reads later are skipped"
  - key: matlab-pulseq
    behavior: "reads the file"
  - key: pypulseq
    behavior: "an event table or [BLOCKS] at the end of the file fails; [DEFINITIONS] is read"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
pulseq_analysis:
  ids: [D2.2]
  commit: 5bd053a
found: 2026-10-12
checked: 2026-10-14
---

# DIS-0016: The last section with no blank line after it

## Summary

A file with no `[SIGNATURE]` ends with its last section. When the last row of
that section is the last line of the file, with no blank line after it, the C++
reader's stream fails at the end of the file, and the reader skips each section
that it reads after that one, in its own order. With `[DEFINITIONS]` last, it
reads no block and plays an empty sequence, with no message; with `[TRAP]` last,
it rejects the file. MATLAB Pulseq reads both files; pypulseq reads the first
and fails on the second.

## What each source does

| Source | What it does |
|---|---|
| Specification | The file "may end with an optional section `[SIGNATURE]`" (section 2.4, `spec:213`), so another section can be last. Only a shape is ended by a blank line (section 2.9, `spec:602`). It does not say whether the end of the file also ends a section. |
| C++ reader | `load` reads the sections in a fixed order, not in file order: `[VERSION]`, `[SHAPES]`, `[RF]`, `[GRADIENTS]`, `[TRAP]`, `[ADC]`, the extensions, `[DEFINITIONS]`, `[BLOCKS]`, `[SIGNATURE]` (`cpp:873`, `cpp:932`, `cpp:998`, `cpp:1060`, `cpp:1108`, `cpp:1135`, `cpp:1202`, `cpp:1398`, `cpp:1546`, `cpp:1601`), each by a seek to the position of its header (`cpp:1768`). A table ends at an empty line (for example `cpp:1111-1114`). When the last row is the end of the file, the next `getline` reads nothing, seeks to -1 "to create error on stream" and returns false (`cpp:2321-2327`): the stream is left failed. Only `[SHAPES]` clears it (`cpp:980`). The later seeks fail, and each later section is read as empty. With `[DEFINITIONS]` last, `[BLOCKS]` (`cpp:1550-1560`) reads no block and `load` returns true. With `[TRAP]` last, no definition is read, and `load` fails: "Required: definition AdcRasterTime is not present in the file" (`cpp:1477-1480`). |
| MATLAB Pulseq | Reads the sections in file order. `fgetl` returns -1 at the end of the file, which is not a `char`, so each section loop ends (`read.m:461`, `read.m:503`, `read.m:564`), and the main loop ends (`read.m:50-53`). |
| pypulseq | Reads the sections in file order. At the end of the file `__strip_line` returns -1 (`read_seq.py:755`; `:763` on master). `__read_definitions` stops at -1 (`read_seq.py:463`). `__read_events` and `__read_blocks` stop only at `''` or `'#'` (`read_seq.py:597`, `read_seq.py:536`), so they pass -1 on: to `__fromstring`, which fails with `AttributeError` (`read_seq.py:813`; `:821` on master), and to `np.fromstring`, which fails with `TypeError` (`read_seq.py:537`). |

## Reproducer

Two files in [`reproducers/DIS-0016/`](../reproducers/DIS-0016/), each of two
blocks of one trapezoid (400 µs, 100000 and 200000 Hz/m), no `[SHAPES]` and no
`[SIGNATURE]`. Each ends with a line end after its last row, and no blank line:

- `definitions_last.seq`: `[VERSION]`, `[BLOCKS]`, `[TRAP]`, `[DEFINITIONS]`.
- `trap_last.seq`: `[VERSION]`, `[DEFINITIONS]`, `[BLOCKS]`, `[TRAP]`.

The tail of `definitions_last.seq`:

```
[DEFINITIONS]
AdcRasterTime 1e-07
BlockDurationRaster 1e-05
GradientRasterTime 1e-05
RadiofrequencyRasterTime 1e-06
```

With one blank line added at the end, each file is read by the three readers
(2 blocks; run on 2026-10-14). `[BLOCKS]` as the last section was also run: the
C++ reader and MATLAB Pulseq read it (2 blocks), and pypulseq fails with
`TypeError: a bytes-like object is required, not 'int'` (`read_seq.py:537`).

Commands as in DIS-0001 (C++ reader plain and sanitized of pulseq-analysis
`65fc7e8`, with `--dump`; MATLAB Pulseq under Octave 11.3.0; pypulseq
1.5.0.post1 and master `c977214`).

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent; read as written, each file has 2 blocks of 400 µs. | — |
| C++ reader | — | `definitions_last.seq`: read (exit 0), 0 blocks, with the four definitions; no message. `trap_last.seq`: rejected (exit 1), "Required: definition AdcRasterTime is not present in the file". Same exit codes with the sanitized build. 2026-10-14. |
| MATLAB Pulseq | — | Both files: read, 2 blocks of 0.4 ms, trapezoids of 100000 and 200000 Hz/m. 2026-10-14. |
| pypulseq | — | `definitions_last.seq`: read, 2 blocks of 0.4 ms (trapezoids 100000 and 200000 Hz/m). `trap_last.seq`: `AttributeError: 'int' object has no attribute 'strip'` (`read_seq.py:813`; `:821` on master). 1.5.0.post1 and master the same. 2026-10-14. |

## Impact

MATLAB Pulseq and pypulseq end every section with a blank line, also when they
write no signature: a file of one trapezoid written by `write` with no signature
by MATLAB Pulseq, pypulseq 1.5.0.post1 and master ends with `[TRAP]` and a blank
line (run on 2026-10-14). A file whose last blank line is removed, for example
by an editor or a tool that trims trailing blank lines, or a file written by
another tool, is affected: the scanner's reader rejects it or, with
`[DEFINITIONS]` last, plays an empty sequence with no message, while MATLAB
Pulseq plays it in full and pypulseq plays it or fails, by section.

## Suggested resolution

The specification: say that the end of the file ends the last section (and the
last shape, DIS-0014), or that a file must end with a blank line. The C++
reader: clear the stream state before each seek in `load` (as it does after
`[SHAPES]`), so that a section at the end of the file does not hide the
sections read after it. pypulseq: stop `__read_events`, `__read_and_parse_events`
and `__read_blocks` at the end of the file (-1), as `__read_definitions` does and
as master does for shapes (DIS-0014).

## Report

Draft, to pulseq/pulseq (specification, C++ reader):

> **The last section of a file with no blank line after it**
>
> The specification does not say whether the end of the file ends the last
> section. In `ExternalSequence::load`, when the last row of the file has no
> blank line after it, `getline` hits the end of the file and puts the stream
> in error (`ExternalSequence.cpp:2321-2327`). The reader reads the sections in
> its own order, so every section that it reads after the last one of the file
> is then read as empty: with `[DEFINITIONS]` last, the file loads as a
> sequence of 0 blocks with no message; with `[TRAP]` last, no definition is
> read and the file is rejected. MATLAB Pulseq reads both files. A
> `data_stream.clear()` before each `seekg` would fix it. Reproducers attached.

Draft, to pulseq/pypulseq:

> **`read` fails when an event table or `[BLOCKS]` is the last section**
>
> When the last row of a `.seq` file is in `[TRAP]` (or another event table,
> or `[BLOCKS]`) with no blank line after it, `__strip_line` returns -1, and
> `__read_events` passes it to `__fromstring` (`AttributeError: 'int' object
> has no attribute 'strip'`), `__read_blocks` to `np.fromstring` (`TypeError`).
> This is the case of #358 for the other sections; it is also on master
> `c977214`. Reproducer attached.

## History

- 2026-10-12: found by pulseq-analysis (old ID D56, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducers written and
  run in the C++ reader (plain and sanitized), MATLAB Pulseq and pypulseq, with
  and without a blank line at the end; unsigned files written by MATLAB Pulseq
  and pypulseq checked for the blank line at their end. `[VERSION]` as the last
  section is DIS-0001, and `[SHAPES]` last is DIS-0014.
  The runs used 1.5.1 files; the code paths cited do not depend on the
  version.
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq; the two behave the same here, and the
  citations give the lines of 1.5.0.post1, with those of master where they
  differ.
