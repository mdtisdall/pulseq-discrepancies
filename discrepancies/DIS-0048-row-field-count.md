---
id: DIS-0048
title: A row with too few or too many values (a [BLOCKS] row of 7 values, a [TRAP] row of 7)
kind: spec-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "a [BLOCKS] row has 8 fields, a [TRAP] row 6"
  - key: cpp-reader
    behavior: "reads a [BLOCKS] row of 7 values (extension 0) and a [TRAP] row of 7 (the last is not read)"
  - key: matlab-pulseq
    behavior: "rejects both: an index error in getBlock, and nonconformant arguments in read"
  - key: pypulseq
    behavior: "rejects both: IndexError in get_block, and ValueError in read"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
priority:
  level: low
  written_by: []
  reason: "No writer writes a row of the wrong length. The C++ reader accepts it silently, and the toolboxes fail on it, but the file is not spec-valid."
pulseq_analysis:
  ids: [D14]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0048: A row with too few or too many values (a [BLOCKS] row of 7 values, a [TRAP] row of 7)

## Summary

The specification gives the fields of each row. The C++ reader reads its rows
with `sscanf`, which reads as many values as the format has and does not look
further: a `[BLOCKS]` row of 7 values is read, with extension 0, and a
`[TRAP]` row of 7 is read without its last value. MATLAB Pulseq and pypulseq
reject both files. A row with too few values for the reader (a `[TRAP]` row
of 5) is rejected by all three, and a `[BLOCKS]` row of 9 values is read by
all three.

## What each source does

| Source | What it does |
|---|---|
| Specification | A block is "specified by a duration and a list of six event IDs", the line `<id> <duration> <rf> <gx> <gy> <gz> <adc> <ext>` (section 2.8, `spec:295-298`). A trapezoid is "specified by six numbers", `<id> <amp> <rise> <flat> <fall> <delay>` (`spec:379-381`). |
| C++ reader | Reads a block row with `sscanf` of 8 values and fails only when fewer than 7 are read (`cpp:1565-1577`); the extension starts at 0 (`cpp:1562`). Reads a trapezoid row with `sscanf` of 6 values and fails when fewer are read (`cpp:1117-1121`); a seventh value is not read. |
| MATLAB Pulseq | Reads a row with `sscanf('%f')` (`read.m:504`, `read.m:565`), so it keeps every value. A block of 7 values has 6 event entries, and `getBlock` (`Sequence.m:1230`) fails at `eventInd(7)` in `getRawBlockContentIDs` (`Sequence.m:1175`). A trapezoid row of 7 values gives 6 numbers against the 5 scales of `[TRAP]`, and the product fails (`read.m:570`, from `read.m:137`). |
| pypulseq | Reads a block row with `np.fromstring` (`read_seq.py:537`); a row of 7 values is read, and `get_block` fails at `event_ind[6]` (`block.py:491`). Reads a trapezoid row with a format of one field per column, and a row of another length raises `ValueError("Mismatch between number of tokens and format spec")` (`read_seq.py:815`; `:823` on master). |

## Reproducer

Changes of a 1.5.1 file of one RF block pulse and one block of a trapezoid and
an ADC, in [`reproducers/DIS-0048/`](../reproducers/DIS-0048/):
`block_row_7_values.seq` (block 1 is `1 20 1 0 0 0 0`),
`block_row_9_values.seq` (`1 20 1 0 0 0 0 0 5`), `trap_row_5_values.seq`
(`1 100000 100 200 100`) and `trap_row_7_values.seq`
(`1 100000 100 200 100 0 50`).

Commands as in DIS-0001.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Each changed row does not have the fields of its table: not a file that the specification describes. | — |
| C++ reader | — | `block_row_7_values.seq`, `block_row_9_values.seq`, `trap_row_7_values.seq`: read, each block decoded (exit 0). `trap_row_5_values.seq`: "failed to decode trapezoid gradient entry" (exit 1). Plain and sanitized. 2026-10-14. |
| MATLAB Pulseq | — | `block_row_7_values.seq`: error "eventInd(7): out of bound 6" (`Sequence.m:1175`, in `getBlock`). Both `[TRAP]` files: "product: nonconformant arguments" (`read.m:570`). `block_row_9_values.seq`: read. 2026-10-14. |
| pypulseq | — | `block_row_7_values.seq`: `IndexError: index 6 is out of bounds for axis 0 with size 6` (`block.py:491`, in `get_block`). Both `[TRAP]` files: `ValueError: Mismatch between number of tokens and format spec` (`read_seq.py:815`; `:823` on master). `block_row_9_values.seq`: read. Both versions. 2026-10-14. |

## Impact

Both writers write each row with all its fields, so their files are not
affected. A file from another tool, or edited by hand, with a short block row
or a long trapezoid row is played by the scanner's reader, which takes a value
that the file does not have (no extension) or drops one that it has, and is
rejected by both toolboxes; the scanner then plays a file that the toolboxes
cannot check.

## Suggested resolution

The C++ reader: in a file of 1.4.0 or later, reject a row that does not have
the number of fields of its table (for example, check that `sscanf` read every
field and that only white space follows).

## Report

Draft, to pulseq/pulseq:

> **C++ reader: rows with a missing or an extra value are read**
>
> `ExternalSequence::load` reads a `[BLOCKS]` row with `sscanf` of 8 values,
> and fails only when fewer than 7 are read (`ExternalSequence.cpp:1565-1577`):
> a row of 7 values is read with extension 0. It reads a `[TRAP]` row with
> `sscanf` of 6 values (line 1117), so a seventh value is not read. MATLAB
> Pulseq and pypulseq reject both files. Could the reader reject a row that
> does not have the fields of its table, in a file of 1.4.0 or later?
> Reproducers attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D14, commit `49a7e2c`, the
  block row of 7 values).
- 2026-10-14: confirmed against the pinned sources; reproducers run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and
  master `c977214`, which agree here. New: the `[TRAP]` row of 7 values, read
  by the C++ reader only. `report_to` is the C++ reader only (the inventory
  also had MATLAB Pulseq, which rejects both files, as pypulseq does).
