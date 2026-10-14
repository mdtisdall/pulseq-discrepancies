---
id: DIS-0068
title: A LABELSET or LABELINC row with a label name that a reader does not know
kind: spec-gap
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "lists the labels 'supported at the moment'; says nothing of another name"
  - key: cpp-reader
    behavior: "warns, leaves the label out, and reads the file"
  - key: matlab-pulseq
    behavior: "fails ('nonconformant arguments')"
  - key: pypulseq
    behavior: "fails (ValueError: tuple.index(x): x not in tuple)"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq]
  reason: "MATLAB Pulseq writes a custom label name through mr.addCustomLabel and mr.makeLabel. MATLAB read (in a new session) and pypulseq read crash on it; the C++ reader drops the label."
pulseq_analysis:
  ids: [D2.19]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0068: A LABELSET or LABELINC row with a label name that a reader does not know

## Summary

The specification lists the label names that are "supported at the moment",
and says nothing of a row with another name. The C++ reader warns, leaves the
label out and reads the file. MATLAB Pulseq and pypulseq fail on it, with an
error that does not name the label.

## What each source does

| Source | What it does |
|---|---|
| Specification | "The following counters are supported at the moment: LIN, PAR, ACQ, SLC, SEG, REP, AVG, SET, ECO, PHS … and flags NAV, REV, SMS, OFF, NOISE, REF, IMA, PMC, NOPOS, NOROT, NOSLC …. There is on three-state flag ONCE …. There is also a special label TRID" (section 2.8.4, `spec:519-520`). Nothing on a name that is not in the list. |
| C++ reader | `decodeLabel` warns "unknown label specification" and returns `dl_unknown` (`cpp:2392-2395`); `load` prints the row and goes on without the label (`cpp:1308-1309`, LABELINC `cpp:1323-1324`). |
| MATLAB Pulseq | `read` maps the name to its index in `mr.getSupportedLabels` (`read.m:165`, LABELINC `read.m:169`); an unknown name gives an empty index, and the assignment fails: "=: nonconformant arguments (op1 is 1x1, op2 is 1x0)" (`read.m:614`). |
| pypulseq | `read` maps the name with `get_supported_labels().index(s)` (`read_seq.py:203`, LABELINC `read_seq.py:214`), which raises `ValueError: tuple.index(x): x not in tuple`. |

## Reproducer

Two 1.5.1 files in [`reproducers/DIS-0068/`](../reproducers/DIS-0068/), each
of one trapezoid block with one LABELSET:

- `label_unknown.seq`: `extension LABELSET 1` with the row `1 3 FOO`;
- `label_known.seq`: the same with `1 3 LIN` (the control).

Commands as in DIS-0057.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent. | — |
| C++ reader | — | `label_unknown.seq`: read (exit 0; sanitized exit 0), with "WARNING: unknown label specification" and "decoding labelset event returned dl_unknown". Control: read. 2026-10-14. |
| MATLAB Pulseq | — | `label_unknown.seq`: "=: nonconformant arguments (op1 is 1x1, op2 is 1x0)" in `readAndParseEvents` (`read.m:614`). Control: read. 2026-10-14. |
| pypulseq | — | `label_unknown.seq`: `ValueError: tuple.index(x): x not in tuple` (`read_seq.py:203`). Control: read. 2026-10-14. |

## Impact

A file with a label that a newer revision adds, or that one interpreter
defines for itself, is read by the scanner's reader without the label, and
cannot be read by either toolbox. The errors of the toolboxes do not say which
label is the cause.

## Suggested resolution

The specification: say what a reader does with a label name that it does not
know (ignore it with a warning, as the C++ reader does, or reject the file).
MATLAB Pulseq and pypulseq: then do the same, or at least fail with a message
that names the label.

## Report

Draft, to pulseq/pulseq (specification, MATLAB Pulseq) and pulseq/pypulseq:

> **A label name that a reader does not know**
>
> Section 2.8.4 lists the labels "supported at the moment", and does not say
> what a reader does with another name. For a LABELSET row `1 3 FOO`,
> `ExternalSequence` warns and leaves the label out; MATLAB's `read` fails
> with "nonconformant arguments" (`read.m:614`, after the lookup of line
> 165), and pypulseq's `read` with `ValueError: tuple.index(x): x not in
> tuple` (`read_seq.py:203`). Could the specification say what to do, and the
> toolboxes follow it, or at least name the label in the error? Reproducer
> attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D50, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here).
