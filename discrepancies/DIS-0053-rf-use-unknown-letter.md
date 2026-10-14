---
id: DIS-0053
title: An RF use letter that is not one of e r i s p o u
kind: spec-vs-implementation
severity: acceptance
status: withdrawn
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "the use is the initial of one of seven words"
  - key: cpp-reader
    behavior: "reads any character, and holds it"
  - key: matlab-pulseq
    behavior: "reads any character; getBlock gives undefined; write writes the letter back"
  - key: pypulseq
    behavior: "reads any text; get_block gives undefined; write writes the letter back"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
pulseq_analysis:
  ids: [D17]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0053: An RF use letter that is not one of e r i s p o u

## Summary

Withdrawn: not a discrepancy. An `[RF]` row whose use is `x` is not a file
that the specification describes (the use is the initial of one of seven
words), and every implementation does the same with it: it reads the file,
keeps the letter, and writes it back unchanged. The toolboxes report the use
as "undefined" in memory, which is not a statement about the file. No two
sources disagree about the file, so this is not a record of this repository
(`docs/record-format.md`, section 1).

## What each source does

| Source | What it does |
|---|---|
| Specification | `<use>`: "it is the initial of one of: excitation, refocusing, inversion, saturation, preparation, other or undefined" (section 2.8.1, `spec:356-357`). No rule for another letter. |
| C++ reader | Reads the use with `%c` (`cpp:1042`) and holds the character. |
| MATLAB Pulseq | Reads the character as the type of the event (`read.m:120`, `read.m:568`); `getBlock` gives `undefined` for a letter that it does not map (`Sequence.m:563-576`); `write` writes the stored letter (`write.m:86`). |
| pypulseq | Reads the text as the type of the event (`read_seq.py:149`, `read_seq.py:601-602`); `get_block` gives `undefined` for a letter that it does not map (`sequence.py:1255-1263`; `:1287-1295` on master); `write` writes the stored letter. |

## Reproducer

[`reproducers/DIS-0053/rf_use_x.seq`](../reproducers/DIS-0053/rf_use_x.seq):
a 1.5.1 file of one RF block pulse of use `x` and one block of a trapezoid and
an ADC:

```
[RF]
1 1000 1 2 0 50 0 0 0 0 0 x
```

Commands as in DIS-0001; each toolbox also read the file and wrote it again.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Not a letter of the specification: not a file that it describes. | — |
| C++ reader | — | Read (exit 0); the dump has the use `x`. 2026-10-14. |
| MATLAB Pulseq | — | Read; `getBlock` gives the use `undefined`; a read and a write give the row `1 1000 1 2 0 50 0 0 0 0 0 x`. 2026-10-14. |
| pypulseq | — | Read; `get_block` gives `undefined`; a read and a write give the row with `x`. Both versions. 2026-10-14. |

## Impact

None between the sources: all three accept the file and keep the letter. What
the scanner's interpreter does with an unknown use is outside the reader.

## Suggested resolution

Not applicable (withdrawn).

## Report

Not reported: withdrawn.

## History

- 2026-10-09: found by pulseq-analysis (old ID D17, commit `49a7e2c`); the
  inventory reserved this ID for it.
- 2026-10-14: run in the C++ reader, MATLAB Pulseq and pypulseq 1.5.0.post1
  and master `c977214`, with a read and a write in each toolbox: all accept the
  file and keep `x`. Withdrawn under the scope rule of the migration: no two
  sources disagree about the file.
