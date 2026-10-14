---
id: DIS-0055
title: IDs of events or blocks that are not positive or not unique
kind: spec-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "IDs are positive; event IDs of one class are unique, [GRADIENTS] and [TRAP] together; silent on block IDs used twice"
  - key: cpp-reader
    behavior: "a later row replaces an earlier one; an RF ID of -2 is no RF; plays every block row, whatever its ID"
  - key: matlab-pulseq
    behavior: "rejects a negative RF ID; a later row replaces an earlier one; a later block of one ID replaces the earlier block"
  - key: pypulseq
    behavior: "plays an RF ID of -2; a later row replaces an earlier one; a later block of one ID replaces the earlier block"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
  - repo: pulseq/pulseq
    component: specification
    issue: null
pulseq_analysis:
  ids: [D19, D3.4]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0055: IDs of events or blocks that are not positive or not unique

## Summary

The specification requires positive IDs, and unique IDs within one class of
events. No reader checks either rule, and two of the breaches are played
differently. A block that uses RF event -2 plays no RF in the C++ reader (it
takes an ID of 0 or below as no event), plays the RF in pypulseq, and is
rejected by MATLAB Pulseq. Two block rows with one ID are two blocks for the C++
reader, which does not use the block ID, and one block (the later) for both
toolboxes, which store the blocks by ID. An ADC ID used twice, and one ID in
both `[GRADIENTS]` and `[TRAP]`, are read the same way by all three: the later
row replaces the earlier one.

## What each source does

| Source | What it does |
|---|---|
| Specification | "IDs must be positive integers"; "The ID of each shape must be unique"; "The ID of events within a single class must be unique … An exception is the `[GRADIENTS]` and `[TRAP]` events where the union of these sets must contain unique event IDs" (section 2.2, `spec:181-183`; also `spec:403`). A block has an `<id>`, "ID of the sequence block" (`spec:306`); the rule of uniqueness is not stated for blocks. "The blocks are executed sequentially" (`spec:318`). |
| C++ reader | Keeps each event table in a map by ID: a later row replaces an earlier one (`cpp:1051`, `cpp:1100`, `cpp:1124`, `cpp:1168`), and `[TRAP]`, read after `[GRADIENTS]`, replaces a gradient of the same ID. A block uses an event only when its ID is above 0 (`cpp:1842`, `cpp.h:696`), so RF -2 is no RF. Reads the block ID but does not use it: the blocks are in file order (`cpp:1565`, `cpp:1586`). |
| MATLAB Pulseq | Stores an event in its `EventLibrary` by ID (`EventLibrary.m:164`): ID -2 fails ("subscripts must be either integers 1 to (2^31)-1"), and a later row replaces an earlier one. Stores a block by its ID (`read.m:509`, `read.m:512`), so a later block of one ID replaces the earlier block. |
| pypulseq | Stores an event by ID (`read_seq.py:612-620`): -2 is a key like another, and a later row replaces an earlier one. Stores a block by its ID (`read_seq.py:542`, `read_seq.py:546`), so a later block of one ID replaces the earlier block. |

## Reproducer

Changes of a 1.5.1 file of one RF block pulse (block 1, 200 µs) and one block
of a trapezoid and an ADC of 8 samples (block 2, 500 µs), in
[`reproducers/DIS-0055/`](../reproducers/DIS-0055/):

| File | Change |
|---|---|
| `rf_id_negative.seq` | The RF event has ID -2, and block 1 uses -2. |
| `block_id_twice.seq` | Block 2 has ID 1 (`1 50 0 1 0 0 1 0`). |
| `adc_id_twice.seq` | A second ADC row of ID 1, of 4 samples. |
| `grad_id_both_tables.seq` | An arbitrary gradient of ID 1 in `[GRADIENTS]`, used by a third block on y, and the trapezoid of ID 1. |

Commands as in DIS-0001; the events of each block are from the C++ dump
(`pulseq-cpp-oracle --dump`), the dump of the MATLAB oracle (`getBlock`), and
`get_block` of pypulseq.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Each file breaks a rule of section 2.2, except `block_id_twice.seq`, on which it is silent: two blocks, executed in order. | — |
| C++ reader | — | All four read (exit 0), plain and sanitized. `rf_id_negative.seq`: block 1 has no RF. `block_id_twice.seq`: two blocks, the RF pulse then the trapezoid and ADC. `adc_id_twice.seq`: the ADC has 4 samples. `grad_id_both_tables.seq`: both gradient blocks have the trapezoid. 2026-10-14. |
| MATLAB Pulseq | — | `rf_id_negative.seq`: error "obj(-2): subscripts must be either integers 1 to (2^31)-1 or logicals" (`EventLibrary.m:164`, from `read.m:120`). `block_id_twice.seq`: read, one block, the trapezoid and ADC. `adc_id_twice.seq`: 4 samples. `grad_id_both_tables.seq`: the trapezoid. 2026-10-14. |
| pypulseq | — | `rf_id_negative.seq`: read, block 1 has the RF pulse. `block_id_twice.seq`: read, one block, the trapezoid and ADC. `adc_id_twice.seq`: 4 samples. `grad_id_both_tables.seq`: the trapezoid. Both versions. 2026-10-14. |

## Impact

Both writers number the events from 1 in their libraries and the blocks 1,
2, … (`write.m:61-68`; `write_seq.py:88-99`), so their files are not affected.
A file from another tool, a merge of two files, or a hand edit that reuses a
block ID is played in full by the scanner's reader, while both toolboxes see
only the later block: their plots, checks and simulations miss a block that
the scanner plays. A negative RF ID gives a block with no RF on the scanner,
and with the RF in pypulseq. The reuse of an event ID is read the same way
everywhere, but no reader reports it.

## Suggested resolution

The readers: reject an ID of 0 or below, and an event ID used twice in one
class (with `[GRADIENTS]` and `[TRAP]` as one class), as section 2.2 requires.
The specification: say whether block IDs must be unique (and in order); the
C++ reader, which ignores them, and the toolboxes, which store blocks by ID,
then agree. Until then, the toolboxes can reject a block ID used twice.

## Report

Draft, to pulseq/pulseq (C++ reader, MATLAB Pulseq and the specification), and
the part on the toolbox to pulseq/pypulseq:

> **IDs that are not positive or not unique are not checked, and are read differently**
>
> Section 2.2 of the specification requires positive IDs, unique within one
> class of events. No reader checks it:
>
> - A block that uses RF event -2: the C++ reader plays no RF (it uses an event
>   only when its ID is above 0, `ExternalSequence.cpp:1842`), pypulseq plays
>   the RF, and MATLAB Pulseq fails in `EventLibrary.insert`
>   ("obj(-2): subscripts must be …").
> - Two block rows with one ID: the C++ reader plays both (it does not use the
>   block ID); MATLAB Pulseq (`read.m:509`) and pypulseq (`read_seq.py:542`)
>   store blocks by ID and keep only the later one. The specification does not
>   say whether block IDs must be unique.
> - An event ID used twice in one class, or in both `[GRADIENTS]` and
>   `[TRAP]`: all three keep the later row, with no message.
>
> Could the readers reject these files, and the specification say whether
> block IDs must be unique? Reproducers attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D19, commit `49a7e2c`; the
  block ID used twice is D3.4 at `5bd053a`).
- 2026-10-14: confirmed against the pinned sources; reproducers run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and
  master `c977214`, which agree here. Severity changed from `acceptance` to
  `playback`: the dumps show that the C++ reader plays the block of the
  negative RF ID without RF and both blocks of one ID, where the toolboxes
  play the RF and one block. pulseq-analysis gave a failure of MATLAB Pulseq
  on the block ID used twice: its fixture has the IDs 1, 2, 2, 4, …, so block 3
  is an empty entry and `getBlock(3)` fails. This file has no such gap, and
  MATLAB Pulseq reads it as one block. The title drops shapes:
  shape IDs were not run.
