---
id: DIS-0072
title: Event values with more digits than pypulseq keeps, or equal events with different IDs
kind: implementation-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "amplitudes are floats; IDs of events within a class must be unique; no rule on precision or on equal events"
  - key: cpp-reader
    behavior: "keeps each event by its ID, with the value of the file (as float32)"
  - key: matlab-pulseq
    behavior: "keeps each event by its ID, with the value of the file"
  - key: pypulseq
    behavior: "read rounds each value (amplitudes to 6 digits), merges equal events and renumbers them"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
pulseq_analysis:
  ids: [D51]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0072: Event values with more digits than pypulseq keeps, or equal events with different IDs

## Summary

pypulseq's `read` calls `remove_duplicates` by default: it rounds the values
of each event (gradient and RF amplitudes to 6 significant digits, shape
samples to 9), merges the events that have become equal, and renumbers them.
So a trapezoid of amplitude 123456.789 Hz/m is played by pypulseq at
123457 Hz/m, where the C++ reader and MATLAB Pulseq play the value of the file,
and pypulseq writes the rounded, merged events back. Two rows that differ only
in the sign of 0 are merged too, which changes no waveform.

## What each source does

| Source | What it does |
|---|---|
| Specification | `<amp>` of a trapezoid is a float (section 2.8.2); "The ID of events within a single class must be unique" (section 2.2). It has no rule on the precision of a value, and none on two events with equal values. |
| C++ reader | Keeps each event by its ID with the value of the file, as a 32-bit float (run: 123456.789 is held as 123456.789, 123456.7 as 123456.703). |
| MATLAB Pulseq | Keeps each event by its ID with the value of the file (run: 123456.789 and 123456.7). |
| pypulseq | `read(…, remove_duplicates=True)` is the default (`read_seq.py:16`, `read_seq.py:443-444`). `Sequence.remove_duplicates` rounds the shapes to 9 significant digits, the gradient amplitudes to 6 and their times to 6 decimal places in s, the RF events likewise (`sequence.py:1161`, `sequence.py:1179`, `sequence.py:1188`; `:1193`, `:1211`, `:1220` on master), with `EventLibrary.remove_duplicates` (`event_lib.py:249-315`), merges the events that are then equal, and maps the block IDs to the merged ones. |

Both writers write amplitudes with `%12g`, that is 6 significant digits
(`write.m:118` for `[TRAP]`; `write_seq.py:151`), so a file of theirs has no
more digits than pypulseq keeps. A file from another tool, or edited by hand,
can.

## Reproducer

Two 1.5.1 files in [`reproducers/DIS-0072/`](../reproducers/DIS-0072/), each
of two trapezoid blocks of 1 ms on x:

- `amplitude_digits.seq`: `[TRAP]` rows `1 123456.789 10 980 10 0` and
  `2 123456.7 10 980 10 0`;
- `equal_events.seq`: `[TRAP]` rows `1 0 10 980 10 0` and `2 -0 10 980 10 0`.

Commands as in DIS-0057; the amplitudes from `pulseq-cpp-oracle --dump`,
MATLAB's `getBlock`, pypulseq's `get_block` and `waveforms_and_times`, with
`read` by default and with `remove_duplicates=False`; then pypulseq's `write`
of the read sequence.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent on precision and on equal events. | — |
| C++ reader | — | `amplitude_digits.seq`: amplitudes 123456.789 and 123456.703 Hz/m. `equal_events.seq`: two trapezoids. 2026-10-14. |
| MATLAB Pulseq | — | `amplitude_digits.seq`: 123456.789 and 123456.7 Hz/m. 2026-10-14. |
| pypulseq | — | Default `read`: one gradient event, 123457 Hz/m in both blocks, and `waveforms_and_times` peaks at 123457; `write` gives one `[TRAP]` row `1 123457 10 980 10 0` used by both blocks. `equal_events.seq`: one event of amplitude 0 used by both blocks. With `remove_duplicates=False`: the two events with the values of the file. 2026-10-14. |

## Impact

The difference is in the 6th significant digit, far below what a gradient
system resolves, so the change of the waveform is small. It matters to a tool
that compares pypulseq's reading of a file with another reader's, or that
checks that `read` and `write` give back the file: pypulseq's default `read`
does not hold the values and the IDs of the file, and the file it writes
back differs from the one it read.

## Suggested resolution

pypulseq: make `read` keep the values and the IDs of the file by default
(`remove_duplicates=False`), and leave the rounding to `write`, where it
matches the precision of the written text.

## Report

Draft, to pulseq/pypulseq:

> **`read` changes the values of the file**
>
> `Sequence.read` calls `remove_duplicates` by default, which rounds gradient
> and RF amplitudes to 6 significant digits and shape samples to 9, merges the
> events that become equal and renumbers them. A trapezoid of 123456.789 Hz/m
> is read as 123457 Hz/m (the C++ reader of the interpreter and MATLAB Pulseq
> keep 123456.789), and two rows that differ only in the sign of 0 become one.
> A `write` after `read` gives a different file. Could `read` keep the values
> and IDs of the file by default? Reproducers attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D51, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here; the
  citations give the lines of 1.5.0.post1, with those of master where they
  differ). The severity is `playback`, not the inventory's `round-trip`: the
  file `amplitude_digits.seq` plays a different amplitude in pypulseq than in
  the C++ reader and MATLAB Pulseq.
