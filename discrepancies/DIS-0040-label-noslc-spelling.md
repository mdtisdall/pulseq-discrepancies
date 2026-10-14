---
id: DIS-0040
title: The label flag NOSLC of the specification, which every implementation spells NOSCL
kind: spec-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "lists and describes the flag NOSLC"
  - key: cpp-reader
    behavior: "knows NOSCL; leaves out a NOSLC label with a message, and reads the file"
  - key: matlab-pulseq
    behavior: "knows NOSCL; rejects a NOSLC label"
  - key: pypulseq
    behavior: "knows NOSCL; rejects a NOSLC label (ValueError)"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
pulseq_analysis:
  ids: [D2.19]
  commit: 5bd053a
found: 2026-10-13
checked: 2026-10-14
---

# DIS-0040: The label flag NOSLC of the specification, which every implementation spells NOSCL

## Summary

The specification lists, and describes, a label flag `NOSLC` ("ignore FOV /
gradient scaling"). The C++ reader, MATLAB Pulseq and pypulseq all spell this
flag `NOSCL` (for "no scaling"), and none of them knows `NOSLC`. A file written
from the specification, with `LABELSET` of `NOSLC`, is rejected by both
toolboxes, and the C++ reader reads it but leaves the flag out.

## What each source does

| Source | What it does |
|---|---|
| Specification | Lists the flags "NAV, REV, SMS, OFF, NOISE, REF, IMA, PMC, NOPOS, NOROT, NOSLC" (section 2.8.4, `spec:520`); "New experimental labels have been introduced in revision 1.4.1. These include `PMC`, `NOROT`, `NOPOS`, `NOSLC` and `ONCE`" (`spec:526`); the table describes `NOSLC`: "Instructs the interpreter to ignore FOV / gradient scaling parameters applied through the UI on the scanner" (`spec:537`). `NOSCL` does not appear. |
| C++ reader | Its labels have `NOSCL` (`cpp.h:260`, `cpp:2380`; and `cpp:825` for the binary format). An unknown name gives "unknown label specification" and `dl_unknown` (`cpp:2394-2395`); the reader prints a message and does not keep the label (`cpp:1308-1310`), and reads the file. |
| MATLAB Pulseq | `getSupportedLabels` has `'NOROT','NOPOS','NOSCL'` (`getSupportedLabels.m:17`). `read` looks the name up in that list (`read.m:165`); for `NOSLC` the lookup is empty and the assignment fails (`read.m:614`). |
| pypulseq | `get_supported_labels` has `'NOSCL'` (`supported_labels_rf_use.py:31`). `read` looks the name up with `tuple.index` (`read_seq.py:203`), which raises `ValueError` for `NOSLC`. |

## Reproducer

[`reproducers/DIS-0040/`](../reproducers/DIS-0040/): `label_noslc.seq`, one RF
block pulse with a `LABELSET` of `NOSLC` to 1, and `label_noscl.seq`, the same
with `NOSCL`:

```
[EXTENSIONS]
1 1 1 0

extension LABELSET 1
1 1 NOSLC
```

Commands as in DIS-0001.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | `label_noslc.seq`: the flag NOSLC set to 1. `label_noscl.seq`: a label that the specification does not list. | — |
| C++ reader | — | `label_noslc.seq`: read (exit 0), with "*** WARNING: unknown label specification" and "decoding labelset event returned dl_unknown"; the block has no label. `label_noscl.seq`: read (exit 0). Plain and sanitized. 2026-10-14. |
| MATLAB Pulseq | — | `label_noslc.seq`: error "=: nonconformant arguments (op1 is 1x1, op2 is 1x0)" (`read.m:614`, from `read.m:165`). `label_noscl.seq`: read. 2026-10-14. |
| pypulseq | — | `label_noslc.seq`: `ValueError: tuple.index(x): x not in tuple` (`read_seq.py:203`). `label_noscl.seq`: read. Both versions. 2026-10-14. |

## Impact

MATLAB Pulseq and pypulseq write `NOSCL`, which all three implementations
read, so their files are not affected. A file of another tool written from the
specification, with `NOSLC`, is rejected by both toolboxes; the scanner's
reader plays it without the flag, so the FOV scaling of the user interface is
not switched off as the file asks.

## Suggested resolution

The specification: spell the flag `NOSCL`, as the implementations do, in
`spec:520`, `spec:526`, `spec:528` and `spec:537`.

## Report

Draft, to pulseq/pulseq:

> **Specification: the label flag `NOSLC` is `NOSCL` in every implementation**
>
> Section 2.8.4 lists and describes a flag `NOSLC` ("ignore FOV / gradient
> scaling", lines 520, 526, 528 and 537 of `specification.tex`). The C++
> reader (`ExternalSequence.cpp:2380`), MATLAB Pulseq
> (`getSupportedLabels.m:17`) and pypulseq spell it `NOSCL` and do not know
> `NOSLC`: a file with `NOSLC` is rejected by MATLAB Pulseq and pypulseq, and
> the C++ reader drops the label with a warning. Could the specification spell
> it `NOSCL`?

## History

- 2026-10-13: found by pulseq-analysis (the note of D2.19, commit `5bd053a`;
  under D50 at `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducers run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and
  master `c977214`, which agree here. The MATLAB error was checked to come from
  `read.m`, not from the dump of the oracle.
