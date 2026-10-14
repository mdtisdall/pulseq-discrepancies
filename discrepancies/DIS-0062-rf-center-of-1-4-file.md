---
id: DIS-0062
title: The RF center of a 1.4 file, which has no center column
kind: spec-gap
severity: round-trip
status: confirmed
format_versions: ["1.4.x"]
sources:
  - key: spec
    behavior: "1.5.0 added the RF center; says nothing of the center of a 1.4 RF event"
  - key: cpp-reader
    behavior: "center -1, 'mark as invalid'"
  - key: matlab-pulseq
    behavior: "computes the center (calcRfCenter); writes it when it saves the file as 1.5"
  - key: pypulseq
    behavior: "computes the center (calc_rf_center); write of the read file fails (KeyError)"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
priority:
  level: high
  written_by: [pypulseq]
  reason: "pypulseq writes a 1.4.1 file with RF through write(v141_compat=True). On it the C++ reader gives the RF center -1 and MATLAB Pulseq and pypulseq give 50 µs."
pulseq_analysis:
  ids: [D4.2]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0062: The RF center of a 1.4 file, which has no center column

## Summary

An `[RF]` row of a 1.4 file has 8 fields and no `center`, which format 1.5.0
added. The specification does not say what the center of such an event is.
The C++ reader sets it to -1, "invalid"; MATLAB Pulseq and pypulseq compute
it from the shape (50 µs for a block pulse of 100 µs), and MATLAB Pulseq
writes that value when it saves the sequence as 1.5. So the same 1.4 file has
no center on the scanner's reader and a center in the toolboxes and in the
1.5 file that MATLAB Pulseq makes from it. The three implementations read the
other 1.4 columns of `[RF]`, `[GRADIENTS]` and `[ADC]` alike.

## What each source does

| Source | What it does |
|---|---|
| Specification | The revision history: 1.5.0 "RF pulses define RF center and intended use fields" (`spec:117-118`). The `[RF]` table has `<center>`, "Time point relative to the beginning of the RF shape at which the effective rotation takes place" (section 2.8.1, `spec:350`). The specification describes only the 1.5 rows, and does not say what a reader takes as the center of a 1.4 RF event. |
| C++ reader | Reads a 1.4 `[RF]` row of 8 values (`cpp:1027-1030`) and sets `center` to -1, "mark as invalid", and `use` to `u` (`cpp:1036-1037`). It reads 5 values of a 1.4 `[GRADIENTS]` row and 6 of an `[ADC]` row (`cpp:1081`, `cpp:1157-1158`). |
| MATLAB Pulseq | Reads the 1.4 rows (`read.m:121-122`, `read.m:131-132`) and computes the center of each RF event with `mr.calcRfCenter` (`read.m:305`); `use` is `u`. `write` then writes a 1.5 row with that center. |
| pypulseq | Reads the 1.4 rows and computes the center with `calc_rf_center` (`read_seq.py:332`); `use` is `u`. Its `write` of the sequence fails with `KeyError` on the RF type (`write_seq.py:118`): the port of the 1.4 RF events sets the types from an empty table (`read_seq.py:326`). |

## Reproducer

[`reproducers/DIS-0062/rf_v141.seq`](../reproducers/DIS-0062/rf_v141.seq): a
1.4.1 file with an RF block pulse of 100 µs (block 1), and a gradient with a
time shape and an ADC (block 2), all in the 1.4 rows:

```
# id amp mag_id phase_id time_id delay freq phase
[RF]
1 1000 1 2 0 0 0 0

# id amp amp_shape_id time_shape_id delay
[GRADIENTS]
1 100000 3 4 0

# id num dwell delay freq phase
[ADC]
1 8 25000 0 0 0
```

Commands as in DIS-0001, and: the center from `pulseq-cpp-oracle --dump`,
from `getBlock(1).rf.center` in MATLAB Pulseq and `get_block(1).rf.center` in
pypulseq; then `write` of the read sequence in MATLAB Pulseq and pypulseq.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent on the center of a 1.4 RF event. | — |
| C++ reader | — | Read (exit 0; sanitized exit 0). `center_us` -1, `use` `u`. 2026-10-14. |
| MATLAB Pulseq | — | Read. Center 50 µs, `use` undefined. `write`: `[RF]` row `1 1000 1 2 0 50 0 0 0 0 0 u`. 2026-10-14. |
| pypulseq | — | Read. Center 49.99999999999999 µs, `use` undefined. `write`: `KeyError: 1` (`write_seq.py:118`). 2026-10-14. |

## Impact

The C++ reader uses the center only to compare RF events
(`findOrInsertRfEvent`, `cpp:2594`), so -1 does not change what it plays.
What the scanner's interpreter does with an invalid center is not in these
sources. The same 1.4 file has a center of 50 µs in MATLAB Pulseq and
pypulseq; a user who converts it to 1.5 with MATLAB Pulseq gets a file whose
center the scanner reads as 50 µs, where the original had none. pypulseq
cannot save a 1.4 file with RF events that it has read.

## Suggested resolution

The specification: say what the center of a 1.4 RF event is (undefined, or
computed as the toolboxes do), so that a reader and a converter agree. The
C++ reader could then compute it as the toolboxes do, or the toolboxes could
keep it undefined.

## Report

Draft, to pulseq/pulseq:

> **The RF center of a 1.4 file**
>
> A 1.4 `[RF]` row has no `center` (1.5.0 added it). `ExternalSequence` sets
> it to -1, "mark as invalid" (`ExternalSequence.cpp:1037`); MATLAB's `read`
> computes it with `mr.calcRfCenter` (`read.m:305`), and `write` then stores
> that value in the 1.5 file; pypulseq computes it too. For a block pulse of
> 100 µs the scanner's reader has -1 and the toolboxes have 50 µs. Could the
> specification say what the center of a 1.4 RF event is, so that the reader
> and the toolboxes agree? Reproducer attached.

The failure of pypulseq's `write` after `read` of a 1.4 file is not a
discrepancy between sources; it can be reported to pulseq/pypulseq on its own.

## History

- 2026-10-09: found by pulseq-analysis (old IDs D01a, D01b, D01c, D38, commit
  `49a7e2c`; D4.2 and D7.5 at `5bd053a`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here). The
  title is narrowed to the center: the three implementations read the other
  1.4 columns alike, so the rows of a 1.4 file are not a discrepancy. The
  `KeyError` of pypulseq's `write` after `read` of a 1.4 file is new.
