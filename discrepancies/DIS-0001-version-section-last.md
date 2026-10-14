---
id: DIS-0001
title: "[VERSION] after [BLOCKS], or as the last section"
kind: spec-gap
severity: crash
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "silent on the order of the sections; only [SIGNATURE] is placed (last)"
  - key: cpp-reader
    behavior: "reads any order; with [VERSION] last it reads no shape, then indexes an empty vector"
  - key: matlab-pulseq
    behavior: "rejects [VERSION] after [BLOCKS]"
  - key: pypulseq
    behavior: "fails with UnboundLocalError on [VERSION] after [BLOCKS]"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
priority:
  level: medium
  written_by: []
  reason: "The spec gives no section order, so the file is valid. No writer puts [VERSION] late. The C++ reader crashes with [VERSION] last; pypulseq fails with UnboundLocalError."
pulseq_analysis:
  ids: [D2.1, D5.1]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-13
---

# DIS-0001: [VERSION] after [BLOCKS], or as the last section

## Summary

The specification does not say in which order the sections of a file come.
The C++ reader finds each section by name, so it reads `[VERSION]` after
`[BLOCKS]`; MATLAB Pulseq and pypulseq read the sections in file order and
reject such a file. When `[VERSION]` is the last section, the C++ reader
leaves its stream failed, reads no shape, and then indexes an empty vector
when a block uses a shape: a crash, or undefined behaviour.

## What each source does

| Source | What it does |
|---|---|
| Specification | Section 2 gives the sections and no order. The only placement is that the file "may end with" `[SIGNATURE]` (section 2.4, `spec:213`). |
| C++ reader | Builds an index of the section headers (`cpp:870`, `cpp:1762-1768`) and seeks to each section by name, so `[VERSION]` after `[BLOCKS]` is read. When `[VERSION]` is the last section, its loop (`cpp:873-912`) reads to the end of the file; `getline` then seeks to -1 to put the stream in error (`cpp:2321-2326`). The seek to `[SHAPES]` (`cpp:933`) fails on the failed stream, `skipComments` reads nothing, the loop of `cpp:939` does not run, and the stream is cleared only after it (`cpp:980`): no shape is read. A block that uses a shape then takes `m_shapeLibrary[id]`, a new empty shape, and `&waveform[0]` of an empty vector (`cpp:1993-1995`). |
| MATLAB Pulseq | Reads the sections in file order and rejects `[BLOCKS]` before `[VERSION]`: "Pulseq file MUST include [VERSION] section prior to [BLOCKS] section" (`read.m:114-116`). |
| pypulseq | Reads the sections in file order. `[BLOCKS]` before `[VERSION]` fails with `UnboundLocalError` (`read_seq.py:137`): the check that would raise "MUST include [VERSION] section prior to [BLOCKS]" reads `file_version_major`, which is not set yet. |

## Reproducer

Two files of one RF block pulse, in
[`reproducers/DIS-0001/`](../reproducers/DIS-0001/):
`version_after_blocks.seq` has the sections `[DEFINITIONS]`, `[BLOCKS]`,
`[VERSION]`, `[RF]`, `[SHAPES]` and a `[SIGNATURE]`; `version_last.seq` has
`[DEFINITIONS]`, `[BLOCKS]`, `[RF]`, `[SHAPES]`, `[VERSION]` and no
`[SIGNATURE]`. The tail of `version_last.seq`:

```
shape_id 2
num_samples 100
0
0
98

[VERSION]
major 1
minor 5
revision 1
```

The C++ reader ran as `pulseq-cpp-oracle FILE` and
`pulseq-cpp-oracle-sanitized FILE` of pulseq-analysis `65fc7e8` (`nix build
.#pulseq-cpp-oracle .#pulseq-cpp-oracle-sanitized`): the reader of `c7469123`
with a driver that runs `load` and `decodeBlock` of each block; the second
build has AddressSanitizer, UndefinedBehaviorSanitizer and the assertions of
libc++. MATLAB Pulseq ran under GNU Octave 11.3.0 (`seq.read`, `getBlock` of
each block, `waveforms_and_times`); pypulseq 1.5.0.post1 and master `c977214` (`Sequence.read`,
`get_block` of each block, `waveforms_and_times`). All on 2026-10-13, macOS
arm64.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent on the order. | — |
| C++ reader | — | `version_after_blocks.seq`: read (exit 0). `version_last.seq`: crash (exit 70); sanitized build: libc++ assertion (`vector::operator[]` index out of range) in `decodeBlock` (exit 3). 2026-10-13. |
| MATLAB Pulseq | — | Both files: error "Pulseq file MUST include [VERSION] section prior to [BLOCKS] section" (`read.m:115`). 2026-10-13. |
| pypulseq | — | Both files: `UnboundLocalError: cannot access local variable 'file_version_major'` (`read_seq.py:137`). 2026-10-13. |

## Impact

MATLAB Pulseq and pypulseq write `[VERSION]` first, so their files are not
affected. A file written by another tool, or edited by hand, with
`[VERSION]` later is played by the scanner's reader and rejected by both
toolboxes; with `[VERSION]` last, the scanner's reader crashes or reads
memory that it does not own as soon as a block uses a shape.

## Suggested resolution

The specification: state that `[VERSION]` comes first (as MATLAB Pulseq and
pypulseq require), or that the sections can come in any order. The C++ reader:
clear the stream state before each seek in `load`, so that a section that
runs to the end of the file does not hide the sections read after it; and
reject a block that uses a shape that was not read, in place of indexing an
empty shape.

## Report

Draft, to pulseq/pulseq:

> **The order of the sections, and `[VERSION]` as the last section**
>
> The specification does not say in which order the sections of a `.seq` file
> come (only that the file "may end with" `[SIGNATURE]`, section 2.4). MATLAB
> Pulseq rejects `[BLOCKS]` before `[VERSION]` (`read.m:114-116`); the C++
> reader reads any order. Could the specification state the order, or that
> any order is allowed?
>
> With `[VERSION]` as the last section, `ExternalSequence::load` reads it to
> the end of the file, which leaves the stream failed (`getline`,
> `ExternalSequence.cpp:2321-2326`). The seek to `[SHAPES]` (line 933) then
> fails, no shape is read, and `decodeBlock` takes `&waveform[0]` of an empty
> vector for the first RF event (lines 1993-1995): a crash in a release
> build, an assertion with the hardened libc++. Reproducer attached
> (`version_last.seq`).

## History

- 2026-10-09: found by pulseq-analysis (old ID D05, commit `49a7e2c`).
- 2026-10-13: confirmed against the pinned sources; reproducers written and
  run in the C++ reader (plain and sanitized), MATLAB Pulseq and pypulseq.
  The runs used 1.5.1 files; the code paths cited do not depend on the
  version.
- 2026-10-13: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, not at the fork that `sources.yaml` pins;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
