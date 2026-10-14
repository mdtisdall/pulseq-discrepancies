---
id: DIS-0054
title: "An RF pulse of use other: pypulseq writes u, and MATLAB Pulseq reads o as undefined"
kind: spec-vs-implementation
severity: round-trip
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "the use is the initial of its word: o for other"
  - key: cpp-reader
    behavior: "reads and holds the letter o"
  - key: matlab-pulseq
    behavior: "writes o for other; reads o as undefined"
  - key: pypulseq
    behavior: "writes u for other; reads o as other"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq]
  reason: "MATLAB Pulseq writes o for a pulse of use other, and its own read gives undefined. pypulseq writes the same pulse as u."
found: 2026-10-05
checked: 2026-10-14
---

# DIS-0054: An RF pulse of use other: pypulseq writes u, and MATLAB Pulseq reads o as undefined

## Summary

The use of an RF pulse is written as the initial of its word, so "other" is
`o`. The two toolboxes each get one half of it wrong. pypulseq accepts
`use='other'` but stores and writes `u` (undefined), while it reads `o` back
as other. MATLAB Pulseq writes `o`, but reads `o` back as undefined. So a
pulse of use other does not survive a write and a read in either toolbox, and
the two toolboxes give a file with `o` different uses.

## What each source does

| Source | What it does |
|---|---|
| Specification | `<use>`: "it is the initial of one of: excitation, refocusing, inversion, saturation, preparation, other or undefined" (section 2.8.1, `spec:356-357`): `o` for other, `u` for undefined. |
| C++ reader | Reads the use with `%c` and holds the letter (`cpp:1042-1044`). |
| MATLAB Pulseq | `registerRfEvent` stores the initial for the six uses, other among them (`Sequence.m:619-621`), and `write` writes it (`write.m:86`). `rfFromLibData` maps `e r i s p` back and gives `undefined` for any other letter, `o` among them (`Sequence.m:563-576`). |
| pypulseq | `register_rf_event` stores the initial only for five uses, and `u` for any other, other among them (`block.py:868-879`); `write` writes the stored letter (`write_seq.py:111`), under a comment that lists other as a use (`write_seq.py:108`). The reader maps `o` to other (`sequence.py:1255-1263`; `:1287-1295` on master). |

## Reproducer

[`reproducers/DIS-0054/`](../reproducers/DIS-0054/): `rf_use_other.py` and
`rf_use_other.m` make a block pulse of use other, write it, print the `[RF]`
section, and read the file back. The Python script is draft 08 of
`mdtisdall/pypulseq-issues`. They ran with pypulseq 1.5.0.post1 and master
`c977214`, and with MATLAB Pulseq of `c7469123` under GNU Octave 11.3.0.
`rf_use_other_matlab.seq` is the file that `rf_use_other.m` wrote; it was read
by the three readers as in DIS-0001, and the C++ dump
(`pulseq-cpp-oracle --dump`) gives the use that the reader holds.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | The row ends in `o`, and reads back as other. | — |
| C++ reader | — | `rf_use_other_matlab.seq`: read (exit 0), the use is `o`. 2026-10-14. |
| MATLAB Pulseq | — | `rf_use_other.m`: the row `1          250 1 2 3 500 0 0 0 0 0 o`; after the read, the use is `undefined` (also for `rf_use_other_matlab.seq`). 2026-10-14. |
| pypulseq | — | `rf_use_other.py`: `get_block` gives `undefined` before the write; the row `1          250 1 2 3 500 0 0 0 0 0 u`; after the read, `undefined`. `rf_use_other_matlab.seq`: the use is `other`. Both versions. 2026-10-14. |

## Impact

A pulse of use other, made in pypulseq, reaches the scanner's reader as
undefined. A pulse of use other, made in MATLAB Pulseq, reaches the scanner's
reader as `o`, but MATLAB Pulseq's own read of the file gives undefined, and
a tool that reads the file with pypulseq gives other. A check or a
reconstruction that relies on the use sees different values for one pulse.

## Suggested resolution

pypulseq: store the initial of each supported use in `register_rf_event`
(test the use against `get_supported_rf_uses()`, as draft 08 suggests), so that
other is `o`. MATLAB Pulseq: map `o` to other in `rfFromLibData`, for example
from `mr.getSupportedRfUse` as its comment `TODO: fixme` says.

## Report

Draft, to pulseq/pypulseq (draft 08 of `mdtisdall/pypulseq-issues`):

> **add_block stores an RF event with use='other' as undefined**
>
> `'other'` is one of the supported RF uses (`get_supported_rf_uses()`), and
> the `make_*` RF functions accept `use='other'`. But `register_rf_event`
> stores its use as `'u'` (undefined), not `'o'`: its list of uses has five
> entries (`Sequence/block.py:868-879`). So `get_block` returns
> `use='undefined'`, and `write` writes `u`, so the use is also lost after a
> write and a read. The reader maps `o` back to `'other'`, and MATLAB Pulseq
> writes `o`. Suggested fix: test the use against `get_supported_rf_uses()`.
> Reproducer attached.

Draft, to pulseq/pulseq (MATLAB Pulseq):

> **`read` gives the use `undefined` for an RF pulse of use `o` (other)**
>
> `registerRfEvent` writes `o` for a pulse of use `'other'`
> (`Sequence.m:619-621`), as the specification says, but `rfFromLibData` maps
> only `e r i s p` back and gives `'undefined'` for `o` (`Sequence.m:563-576`).
> So a pulse of use other reads back as undefined from the toolbox's own file.
> Could the `switch` also map `o` to `'other'`? Reproducer attached.

## History

- 2026-10-05: found (draft 08 of `mdtisdall/pypulseq-issues`, pypulseq's
  write).
- 2026-10-14: confirmed against the pinned sources; scripts run in pypulseq
  1.5.0.post1 and master `c977214` (the same code in both) and in MATLAB
  Pulseq. New: MATLAB Pulseq reads `o` as undefined, so it is added to the
  record and to `report_to`. The kind is changed from
  `implementation-vs-implementation` to `spec-vs-implementation`: the
  specification gives `o` for other. The title names both halves.
