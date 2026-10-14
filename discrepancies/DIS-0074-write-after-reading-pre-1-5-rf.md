---
id: DIS-0074
title: A file before 1.5.0 with an [RF] event, read and written again
kind: implementation-vs-implementation
severity: round-trip
status: confirmed
format_versions: ["1.3.x", "1.4.x"]
sources:
  - key: matlab-pulseq
    behavior: "reads the file, gives each RF the use u, and writes it again as 1.5.1"
  - key: pypulseq
    behavior: "reads the file, but write fails with KeyError (default detect_rf_use=False) and leaves a cut file"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
found: 2026-10-14
checked: 2026-10-14
---

# DIS-0074: A file before 1.5.0 with an [RF] event, read and written again

## Summary

A Pulseq file of version 1.3.x or 1.4.x has no RF use field; the field came
with 1.5.0. MATLAB Pulseq reads such a file, gives each RF event the use `u`
(undefined), and writes it again as a 1.5.1 file. pypulseq reads the same
file, but its `write` fails with `KeyError` on the first RF event, unless
`read` was given `detect_rf_use=True`, and the failed write leaves a cut
file. So pypulseq cannot convert an older file with RF to the current
format, which MATLAB Pulseq can.

## What each source does

| Source | What it does |
|---|---|
| MATLAB Pulseq | `read` sets `detectRFuse` to false unless the caller asks for it (`read.m:18-21`). For a file before 1.4.0 and for a 1.4.x file, it sets the type (the use) of each RF event to `u` (`read.m:232`, `read.m:301`) and then changes only the data of the event (`read.m:242-245`, `read.m:306-309`), with `update_data`, which passes no type to `insert`; `insert` changes the type only when it gets one (`EventLibrary.m:206-212`, `:198-202`, `:167-168`). `write` writes the type as the last field of each `[RF]` row (`write.m:86`), and writes the version of the toolbox, 1.5.1 (`write.m:24-28`). |
| pypulseq | `Sequence.read` has `detect_rf_use=False` as its default (`sequence.py:1099`; `:1130` on master), so the default of `read_seq.read` (`None`, which becomes true for a file before 1.5.0, `read_seq.py:129-130`) does not apply. For a file before 1.4.0 and for a 1.4.x file, `read_seq.read` sets the RF types with `dict.fromkeys(self.rf_library.type.keys(), 'u')` (`read_seq.py:262`, `read_seq.py:326`): the type dictionary is empty after the `[RF]` section of an older file, so it stays empty. It then calls `rf_library.update` with `'u'` as the last element of the data, not as the `data_type` argument (`read_seq.py:270-274`, `read_seq.py:333-337`), and `insert` sets a type only for a `data_type` that is not empty (`event_lib.py:164-165`). Only `detect_rf_use` sets the types (`read_seq.py:419-433`). `write` then reads `self.rf_library.type[k]` for each RF event (`write_seq.py:118`), which raises `KeyError`, after it has written the file up to the `[RF]` header. |

## Reproducer

Two hand-written files of one block with one RF event, the same pulse in the
format of 1.3.1 and of 1.4.1, and a script for each toolbox that reads each
file and writes it again, in
[`reproducers/DIS-0074/`](../reproducers/DIS-0074/): `v131_rf.seq`,
`v141_rf.seq`, `write_after_read.py`, `write_after_read.m`. The `[RF]`
section of `v141_rf.seq`:

```
[RF]
1 250 1 2 0 100 0 0
```

The scripts ran in the folder of the files: `python -I write_after_read.py`
with pypulseq 1.5.0.post1 and with master `c977214`, and
`write_after_read.m` with MATLAB Pulseq `c7469123` under GNU Octave 11.3.0.
The C++ reader (`pulseq-cpp-oracle --dump FILE` and
`pulseq-cpp-oracle-sanitized FILE` of pulseq-analysis `65fc7e8`) ran on the
two files and on the two files that MATLAB Pulseq wrote. All on 2026-10-14,
macOS.

| Source | Expected | Observed (command, date) |
|---|---|---|
| MATLAB Pulseq | — | Both files: read, and written as 1.5.1 with the `[RF]` row `1 250 1 2 0 99.5 100 0 0 0 0 u`. 2026-10-14. |
| pypulseq | — | 1.5.0.post1 and master: both files read; `rf_library.type` is `{}`; `write` raises `KeyError: 1` at `write_seq.py:118` and leaves a file of 624 bytes that ends with the `[RF]` header. With `read(..., detect_rf_use=True)`: `rf_library.type` is `{1: 'r'}`, and `write` writes the row `1 250 1 2 0 99.5 100 0 0 0 0 r`. 2026-10-14. |

The C++ reader reads the four files (exit 0, sanitized exit 0): the same RF
event (amplitude 250 Hz, delay 100 µs, 100 samples of magnitude 1, use `u`)
in each, with a center of 99.5 µs in the files that MATLAB Pulseq wrote. The
pydump runs of both pypulseq versions read the four files too.

## Impact

A user who reads an older sequence file with RF in pypulseq, to change it or
to convert it to the current format, gets an exception from `write`, and a
cut file on disk with the name that was asked for. A cut file has no `[RF]`
rows, no `[SHAPES]` and no `[SIGNATURE]`. MATLAB Pulseq converts the same
file. The workaround is `read(..., detect_rf_use=True)`, which guesses the
use of each pulse from its flip angle (`read_seq.py:419-433`): it writes `r`
or `e` or `s` where MATLAB Pulseq writes `u`.

## Suggested resolution

pypulseq: in the two version-porting branches of `read_seq.read`, set the
type of each RF event to `'u'` as MATLAB Pulseq does, for example with
`dict.fromkeys(self.rf_library.data.keys(), 'u')`, and pass `'u'` as the
`data_type` of `update`, not as an element of the data.

## Report

Draft, to pulseq/pypulseq:

> **`write` after `read` of a 1.3.x or 1.4.x file with RF fails with KeyError**
>
> With pypulseq 1.5.0.post1 and master (`c977214`), reading a Pulseq file of
> version 1.3.x or 1.4.x that has an `[RF]` section and then writing it
> fails: `write_seq.py:118` raises `KeyError: 1` on
> `self.rf_library.type[k]`, after it has written the file up to the `[RF]`
> header. The RF types are never set: `read_seq.py:262` and `:326` build
> them from `self.rf_library.type.keys()`, which is empty for an older file,
> and `read_seq.py:270-274` and `:333-337` pass `'u'` as the last element of
> the data instead of as `data_type`. `Sequence.read` has
> `detect_rf_use=False` as its default, so the detection that would set the
> types does not run. MATLAB Pulseq sets the use of each RF of an older file
> to `u` (`read.m:232`, `:301`) and writes the file as 1.5.1. Files
> attached (`v131_rf.seq`, `v141_rf.seq`, `write_after_read.py`).

## History

- 2026-10-14: found while checking DIS-0037 (the 1.3.1 file of that record);
  noted in batch 4 of the migration for a 1.4.x file.
- 2026-10-14: confirmed against the pinned sources; reproducer run in
  pypulseq 1.5.0.post1 and master `c977214` (the cited lines of
  `read_seq.py`, `event_lib.py` and `write_seq.py` are the same in both),
  MATLAB Pulseq under Octave 11.3.0, and the C++ reader (plain and
  sanitized).
