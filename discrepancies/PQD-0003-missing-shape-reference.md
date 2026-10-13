---
id: PQD-0003
title: A reference to a shape that does not exist, or a [GRADIENTS] row of shape ID 0
kind: spec-vs-implementation
severity: crash
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "events refer to shapes by ID; IDs must be positive"
  - key: cpp-reader
    behavior: "a missing shape: indexes an empty vector; shape ID 0: plays an uninitialised trapezoid"
  - key: matlab-pulseq
    behavior: "rejects both (index errors)"
  - key: pypulseq
    behavior: "rejects both (KeyError)"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D5.1, D5.2]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-13
---

# PQD-0003: A reference to a shape that does not exist, or a [GRADIENTS] row of shape ID 0

## Summary

An event refers to its shapes by ID, and the IDs of shapes are positive. When
an RF or gradient event names a shape ID that `[SHAPES]` does not have, MATLAB
Pulseq and pypulseq reject the file, but the C++ reader takes an empty shape
and indexes an empty vector: a crash, or undefined behaviour. A `[GRADIENTS]`
row of shape ID 0 is rejected by both toolboxes too; the C++ reader plays it
as a trapezoid whose times it never set.

## What each source does

| Source | What it does |
|---|---|
| Specification | Blocks refer to events, and events to shapes, by ID (section 2.2, `spec:179`); "IDs must be positive integers" (`spec:181`). The only shape ID with a meaning of its own is 0 for a time shape, the default raster (`spec:184`). A `[GRADIENTS]` row has a `<shape_id>`, the "Shape ID for arbitrary gradient waveform" (section 2.8.2, `spec:394`). |
| C++ reader | A block that names an event that does not exist is rejected (`checkBlockReferences`, `cpp:1579-1584`, `cpp:2250-2262`), but shape IDs are not checked. `decodeBlock` takes `m_shapeLibrary[id]`, which inserts an empty shape for a missing ID, and then `&waveform[0]` of the empty vector (`cpp:1993-1995` for RF, `cpp:2105-2110` and `cpp:2171-2177` for gradients). A `[GRADIENTS]` row is read into a `GradEvent` that is not initialised (`cpp:1069`); a row of shape ID 0 sets only its amplitude, `first`, `last`, shape IDs and delay (`cpp:1073`), and `isTrapGradient` takes `waveShape == 0` for a trapezoid (`cpp.h:697`), so the block plays a trapezoid with the indeterminate `rampUpTime`, `flatTime` and `rampDownTime` (`cpp.h:118-120`). |
| MATLAB Pulseq | A missing RF shape: error "out of bound" (`rfFromLibData`, `Sequence.m:516`). Shape ID 0 in `[GRADIENTS]`: error "obj(0): subscripts must be either integers 1 to (2^31)-1" (`getBlock`, `Sequence.m:1367`). |
| pypulseq | A missing RF shape: `KeyError` in `read` (`remove_duplicates`, `sequence.py:1174`). Shape ID 0 in `[GRADIENTS]`: `KeyError` in `get_block` (`block.py:409`). |

## Reproducer

In [`reproducers/PQD-0003/`](../reproducers/PQD-0003/):
`shape_missing.seq` is one RF block pulse whose magnitude shape is 3, which
`[SHAPES]` does not have (`[RF]` row `1 1000 3 2 0 50 0 0 0 0 0 e`);
`gradient_shape_0.seq` is one block with the gradient

```
[GRADIENTS]
1 100000 0 0 0 0 0
```

Commands as in PQD-0001 (C++ reader plain and sanitized of pulseq-analysis
`65fc7e8`; MATLAB Pulseq under Octave 11.3.0; pypulseq at the pin), and
`pulseq-cpp-oracle --dump` for what the reader holds.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Each shape reference names a shape of `[SHAPES]`, by a positive ID. | — |
| C++ reader | — | `shape_missing.seq`: crash (exit 70); sanitized: libc++ assertion (`vector::operator[]`) in `decodeBlock` (exit 3). `gradient_shape_0.seq`: read (exit 0); `--dump` gives a trapezoid of ramp-up 8354699472 µs and flat 6531448714 µs in the plain build, and 0 µs in the sanitized build. 2026-10-13. |
| MATLAB Pulseq | — | `shape_missing.seq`: "obj(3): out of bound 2" (`Sequence.m:516`). `gradient_shape_0.seq`: "obj(0): subscripts must be either integers 1 to (2^31)-1 or logicals" (`Sequence.m:1367`). 2026-10-13. |
| pypulseq | — | `shape_missing.seq`: `KeyError: 3.0` (`sequence.py:1174`). `gradient_shape_0.seq`: `KeyError: 0.0` (`block.py:409`). 2026-10-13. |

## Impact

No writer writes these files. A file with a damaged or hand-edited
`[SHAPES]` section, or a `[GRADIENTS]` row of shape ID 0, is rejected by both
toolboxes, but the scanner's reader crashes on it, or plays a gradient whose
timing is whatever is on the stack.

## Suggested resolution

The C++ reader: in `checkBlockReferences`, or in `load` after `[SHAPES]`,
check that each shape ID of each event used by a block is in the shape
library (and is not 0 for a `[GRADIENTS]` waveform), and reject the file
otherwise; initialise `GradEvent` before `sscanf`.

## Report

Draft, to pulseq/pulseq:

> **C++ reader: a shape ID that does not exist, or a `[GRADIENTS]` shape ID of 0**
>
> `checkBlockReferences` checks the event IDs of a block but not the shape IDs
> of its events. `decodeBlock` takes `m_shapeLibrary[id]`, which inserts an
> empty shape for a missing ID, and then `&waveform[0]` of an empty vector
> (`ExternalSequence.cpp:1993-1995`, 2105-2110, 2171-2177). A `[GRADIENTS]`
> row with shape ID 0 is read into an uninitialised `GradEvent` (line 1069),
> and `isTrapGradient` then plays it as a trapezoid with indeterminate ramp
> and flat times (in our run, a ramp-up of 8354699472 µs). MATLAB Pulseq and
> pypulseq reject both files. Reproducers attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D21, commit `49a7e2c`); shape
  ID 0 in `[GRADIENTS]` on 2026-10-12 (D5.2).
- 2026-10-13: confirmed against the pinned sources; reproducers run in the
  C++ reader (plain and sanitized), MATLAB Pulseq and pypulseq (1.5.1 files).
  The record keeps only the shape references of the inventory's row: a
  missing event is rejected by every reader, and a missing extension entry
  or object does not crash the C++ reader. pypulseq's `KeyError` is a
  rejection, so pypulseq is not a maintainer to report to.
