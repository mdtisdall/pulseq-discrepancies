---
id: PQD-0004
title: An RF event with time ID -1
kind: spec-vs-implementation
severity: crash
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "-1 is defined for gradients only; for RF, 0 is the default raster"
  - key: cpp-reader
    behavior: "looks up time shape -1, an empty shape, and indexes an empty vector"
  - key: matlab-pulseq
    behavior: "reads it on the default RF raster"
  - key: pypulseq
    behavior: "rejects it (KeyError)"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
pulseq_analysis:
  ids: [D5.3]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-13
---

# PQD-0004: An RF event with time ID -1

## Summary

The specification defines time ID -1 for an arbitrary gradient (half the
gradient raster), and for an RF event only 0, the default raster. MATLAB
Pulseq reads an RF event of time ID -1 on the default raster, pypulseq rejects
it, and the C++ reader takes time shape -1, an empty shape, and indexes an
empty vector: a crash, or undefined behaviour.

## What each source does

| Source | What it does |
|---|---|
| Specification | RF `<time_id>`: "Shape ID for the time sampling points … 0 means default time raster" (section 2.8.1, `spec:349`). Gradient `<time_id>`: "… -1 means 1/2 of the default time raster (gradient oversampling case)" (section 2.8.2, `spec:395`). Shape IDs "must be positive integers" (`spec:181`). |
| C++ reader | Any RF time ID other than 0 is a time shape (`cpp:2010`). `m_shapeLibrary[-1]` inserts an empty shape (`cpp:2013`); it is not of 3 or 4 values, so the reader decompresses it into `&waveform_t[0]` of an empty vector (`cpp:2024-2026`). |
| MATLAB Pulseq | A time ID that is not above 0 is the default raster (`Sequence.m:526`, `Sequence.m:532-535`). |
| pypulseq | `read` fails with `KeyError: -1`: `remove_duplicates` maps the time ID through its table of shapes (`sequence.py:1174`; `:1206` on master). |

## Reproducer

[`reproducers/PQD-0004/rf_time_id_minus_1.seq`](../reproducers/PQD-0004/rf_time_id_minus_1.seq):
one RF block pulse of 100 samples with the row

```
[RF]
1 1000 1 2 -1 50 0 0 0 0 0 e
```

Commands as in PQD-0001 (C++ reader plain and sanitized of pulseq-analysis
`65fc7e8`; MATLAB Pulseq under Octave 11.3.0; pypulseq 1.5.0.post1 and master `c977214`).

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Time ID -1 has no meaning for RF. | — |
| C++ reader | — | Crash (exit 70); sanitized: libc++ assertion (`vector::operator[]`) in `decodeBlock` (exit 3). 2026-10-13. |
| MATLAB Pulseq | — | Read, with the samples on the default RF raster. 2026-10-13. |
| pypulseq | — | `KeyError: -1.0` (`sequence.py:1174`; `:1206` on master). 2026-10-13. |

## Impact

No writer writes an RF event of time ID -1. A file that has one (from a tool
that takes -1 to mean "oversampled" for every event) is played on the default
raster by MATLAB Pulseq, so it looks valid in the toolbox, and crashes the
scanner's reader.

## Suggested resolution

The C++ reader: reject an RF time ID below 0 with a message (or treat it as
0, as MATLAB Pulseq does, if the specification says so). MATLAB Pulseq: reject
an RF time ID below 0, as the specification defines none, so that the
toolbox does not accept a file that the scanner cannot read.

## Report

Draft, to pulseq/pulseq:

> **An RF event with time ID -1**
>
> The specification defines time ID -1 for gradients only (section 2.8.2); for
> RF only 0 (section 2.8.1). The C++ reader takes RF time ID -1 as a time shape:
> `m_shapeLibrary[-1]` is a new empty shape, and `decompressShape` writes into
> `&waveform_t[0]` of an empty vector (`ExternalSequence.cpp:2013-2026`): a
> crash. MATLAB Pulseq reads the same event on the default raster
> (`Sequence.m:526`, 532-535). Could the C++ reader reject it with a message,
> and MATLAB Pulseq reject it too (or the specification define it)?
> Reproducer attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D22, commit `49a7e2c`).
- 2026-10-13: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq (a 1.5.1 file).
- 2026-10-13: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, not at the fork that `sources.yaml` pins;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
