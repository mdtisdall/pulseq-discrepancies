---
id: DIS-0002
title: A shape with no blank line after its last sample
kind: spec-vs-implementation
severity: crash
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "the end of a shape is declared with a blank line"
  - key: cpp-reader
    behavior: "ends the shape at the shape_id line, then stops reading [SHAPES]; a block that uses a lost shape crashes"
  - key: matlab-pulseq
    behavior: "reads the shape_id line as a sample; rejects the file"
  - key: pypulseq
    behavior: "reads the shape_id line as a sample; rejects the file"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
priority:
  level: low
  written_by: []
  reason: "The spec ends a shape with a blank line, so the file is not valid. Both writers write the blank line. Only the C++ reader crashes, on this invalid file."
pulseq_analysis:
  ids: [D3.11, D5.1]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-13
---

# DIS-0002: A shape with no blank line after its last sample

## Summary

The specification ends a shape with a blank line. When the next `shape_id`
line comes right after the last sample, MATLAB Pulseq and pypulseq reject the
file, but the C++ reader ends the shape at that line, reads the next line as
the start of the next shape, and stops reading `[SHAPES]`. The later shapes are
lost without a message, and a block that uses one of them makes the reader
index an empty vector: a crash, or undefined behaviour.

## What each source does

| Source | What it does |
|---|---|
| Specification | "The end of the shape definition is declared with a blank line." (section 2.9, `spec:602`) |
| C++ reader | The samples of a shape end at an empty line or at a line that starts with `s` (`cpp:955-958`). After a shape, `skipComments` reads the next non-empty line (`cpp:978`); when the `shape_id` line was the end of the samples, that next line is its `num_samples` line, which does not start with `s`, so the loop over the shapes ends (`cpp:939`). The shapes from there on are not read, with no message. A block that uses one of them takes `m_shapeLibrary[id]`, a new empty shape, and `&waveform[0]` of an empty vector (`cpp:1993-1995`, and `cpp:2176-2177` for a gradient). |
| MATLAB Pulseq | The samples end at an empty line or a `#` line (`read.m:653`); the `shape_id` line is read as a sample by `sscanf` (`read.m:654`). Reading the file fails ("out of bound", in `rfFromLibData`, `Sequence.m:520`). |
| pypulseq | The samples end at an empty line or a lone `#` (`read_seq.py:688`; `:690` on master); the `shape_id` line is read with `float()` and `read` fails with `ValueError` (`read_seq.py:689`; `:691` on master). |

## Reproducer

[`reproducers/DIS-0002/shape_no_blank_line.seq`](../reproducers/DIS-0002/shape_no_blank_line.seq):
one RF block pulse whose magnitude (shape 1) and phase (shape 2) are in
`[SHAPES]` with no blank line between them:

```
[SHAPES]

shape_id 1
num_samples 100
1
0
0
97
shape_id 2
num_samples 100
0
0
98
```

Commands as in DIS-0001 (C++ reader plain and sanitized of pulseq-analysis
`65fc7e8`; MATLAB Pulseq under Octave 11.3.0; pypulseq 1.5.0.post1 and master `c977214`).

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | The shape has no blank line after it: not a file that the specification describes. | — |
| C++ reader | — | Crash (exit 70); sanitized build: libc++ assertion (`vector::operator[]`) in `decodeBlock` (exit 3). 2026-10-13. |
| MATLAB Pulseq | — | Error "obj(2): out of bound 1" (`rfFromLibData`, `Sequence.m:520`). 2026-10-13. |
| pypulseq | — | `ValueError: could not convert string to float: 'shape_id 2'` (`read_seq.py:689`; `:691` on master). 2026-10-13. |

## Impact

MATLAB Pulseq and pypulseq end every shape with a blank line, so their files
are not affected. A file from another tool, or edited by hand, that lacks one
blank line is rejected by both toolboxes; the scanner's reader drops the
shapes after it without a message, and crashes if a block uses one. When no
block uses the lost shapes, the scanner's reader reads the file silently.

## Suggested resolution

The C++ reader: end the samples only at an empty line, as the specification
says, so that a `shape_id` line among the samples is a decoding error (as in
both toolboxes); or, if a `shape_id` line is to end a shape, go on with the
next shape from that line. In both cases, reject a block that uses a shape
that was not read.

## Report

Draft, to pulseq/pulseq:

> **C++ reader: a shape with no blank line after it drops the later shapes**
>
> `ExternalSequence::load` ends the samples of a shape at a line that starts
> with `s` (`ExternalSequence.cpp:955-958`). When the next `shape_id` line
> follows the last sample with no blank line, `skipComments` (line 978) then
> reads that shape's `num_samples` line, and the loop over the shapes (line
> 939) stops: the remaining shapes are not read, with no message. A block that
> uses one of them reads element 0 of an empty vector (lines 1993-1995). MATLAB
> Pulseq and pypulseq reject such a file. Reproducer attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D07, commit `49a7e2c`).
- 2026-10-13: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq (a 1.5.1 file).
- 2026-10-13: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, not at the fork that `sources.yaml` pins;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
