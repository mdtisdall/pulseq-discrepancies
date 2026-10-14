---
id: DIS-0021
title: Block IDs that are not in increasing order
kind: spec-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "no restriction on the order of IDs; the blocks are executed sequentially"
  - key: cpp-reader
    behavior: "plays the blocks in file order; does not keep the block ID"
  - key: matlab-pulseq
    behavior: "stores each block at its ID, and plays the blocks in the order of their IDs"
  - key: pypulseq
    behavior: "keeps the blocks in a dict by ID in file order, and plays them in file order"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
priority:
  level: high
  written_by: [pypulseq]
  reason: "pypulseq's public set_block writes blocks in insertion order with IDs such as 1, 3, 2. MATLAB Pulseq plays them in the order of their IDs, not in file order as the spec and the C++ reader do."
pulseq_analysis:
  ids: [D7.3]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0021: Block IDs that are not in increasing order

## Summary

The specification puts no restriction on the order of IDs and executes the
blocks sequentially. In a file whose `[BLOCKS]` rows are 1, 3, 2, the C++
reader and pypulseq play the blocks in file order, 1, 3, 2. MATLAB Pulseq
stores each block at the index of its ID, so it plays 1, 2, 3: the same file
gives a different sequence.

## What each source does

| Source | What it does |
|---|---|
| Specification | "There are no restrictions on the ordering of IDs, although sequential ordering is often implemented." (section 2.2, `spec:185`). The block row starts with `<id>`, the "ID of the sequence block" (section 2.7, `spec:306`); "Each subsequence line declares a single block" (`spec:295`), and "The blocks are executed sequentially." (`spec:318`). The text does not say whether "sequentially" means the order of the lines or the order of the IDs; with no restriction on the order of the IDs, the order of the lines is the reading that gives a block ID no other use. |
| C++ reader | Reads the block ID into `blockIdx` (`cpp:1565`) and does not use it: each row is appended to `m_blocks` in file order (`cpp:1586`), and `GetBlock(index)` takes the position (`cpp:1819`). |
| MATLAB Pulseq | Stores each row at its ID: `eventTable{blockEvents(1)}` and `blockDurations(blockEvents(1))` (`read.m:504-512`). `getBlock(index)` takes the block at that index (`Sequence.m:1229`, `Sequence.m:1173`), and `waveforms_and_times` goes through the indices 1 to N (`Sequence.m:1985-1986`), so the blocks play in the order of their IDs. |
| pypulseq | Keeps the blocks in a `dict` by ID, in file order (`read_seq.py:537-546`). `waveforms` goes through `self.block_events` in that order (`sequence.py:1557`, `:1574`; `:1620`, `:1637` on master), so the blocks play in file order. |

## Reproducer

[`reproducers/DIS-0021/blocks_out_of_order.seq`](../reproducers/DIS-0021/blocks_out_of_order.seq),
written by hand (MATLAB Pulseq and pypulseq number the blocks 1, 2, … when
they write). Three blocks: an RF pulse, a gz trapezoid and an ADC, with the
IDs 1, 3, 2:

```
# NUM DUR RF GX GY GZ ADC EXT
[BLOCKS]
1 20 1 0 0 0 0 0
3 12 0 0 0 1 0 0
2 20 0 0 0 0 1 0
```

Commands as in DIS-0001, and `pulseq-cpp-oracle --dump` for the blocks in
the order that the C++ reader plays them.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | The blocks executed sequentially: in file order, the RF pulse (0-200 µs), the gz trapezoid (200-320 µs), the ADC (320-520 µs). | — |
| C++ reader | — | Read (exit 0; sanitized build exit 0). Blocks in play order: RF (20 block rasters), gz (12), ADC (20). 2026-10-14. |
| MATLAB Pulseq | — | Block durations 200, 200, 120 µs; `getBlock(2)` is the ADC, `getBlock(3)` the gz trapezoid. `waveforms_and_times`: the ADC samples from 205 to 295 µs, gz from 400 to 520 µs. 2026-10-14. |
| pypulseq | — | 1.5.0.post1 and master, the same: block durations 200, 120, 200 µs, in file order; `waveforms_and_times`: gz from 200 to 320 µs. 2026-10-14. |

## Impact

The writers number the blocks 1, 2, … in order, so their files are not
affected. A file that another tool writes, or that is edited by hand (for
example a block moved or inserted without renumbering), is played in one
order by the scanner and pypulseq, and in another by MATLAB Pulseq: what
MATLAB Pulseq shows and checks for such a file is not what the scanner
plays.

## Suggested resolution

MATLAB Pulseq: keep the blocks in file order, and the block IDs only as
labels (or reject IDs that are not 1, 2, … in order, with a message). The
specification: state that the blocks are executed in the order of the
lines of `[BLOCKS]`.

## Report

Draft, to pulseq/pulseq:

> **MATLAB Pulseq plays the blocks in the order of their IDs, not in file
> order**
>
> The specification puts "no restrictions on the ordering of IDs" (section
> 2.2) and executes the blocks sequentially (section 2.7). `read.m` stores
> each block row at the index of its ID (`eventTable{blockEvents(1)}`,
> lines 504-512), so a file with the block IDs 1, 3, 2 is played as 1, 2,
> 3. `ExternalSequence::load` does not use the block ID and plays the rows
> in file order (`ExternalSequence.cpp:1565`, `:1586`), and so does
> pypulseq. Reproducer attached (`blocks_out_of_order.seq`: MATLAB Pulseq
> plays the ADC before the gz trapezoid, the C++ reader after it). Could
> `read.m` keep the file order, or reject such a file with a message? The
> specification could also say "in the order of the lines".

## History

- 2026-10-09: found by pulseq-analysis (old ID D20, commit `49a7e2c`; D7.3
  of `packages/pulseq-cpp-siemens/docs/specification.md` at `5bd053a`).
- 2026-10-14: confirmed against the pinned sources; the reproducer run in
  the C++ reader (plain and sanitized), MATLAB Pulseq under Octave 11.3.0
  and pypulseq 1.5.0.post1 and master `c977214` (a 1.5.1 file; the cited
  code does not depend on the version). The citations give the lines of
  1.5.0.post1, with those of master where they differ.
