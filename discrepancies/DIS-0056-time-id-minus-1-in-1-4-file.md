---
id: DIS-0056
title: Time ID -1 in a 1.4 file
kind: spec-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.4.x"]
sources:
  - key: spec
    behavior: "defines time ID -1 for gradients, with no revision"
  - key: spec-slides
    behavior: "time ID -1 is new in 1.5.0; first and last are stored in the event"
  - key: cpp-reader
    behavior: "reads it as oversampled, with first and last 1.18e-38 Hz/m"
  - key: matlab-pulseq
    behavior: "reads it, with last = the last sample; its 1.4.1 writer refuses it"
  - key: pypulseq
    behavior: "rejects time ID -1 when it reads (KeyError, DIS-0031); write(v141_compat=True, remove_duplicates=False) writes it in a 1.4.1 file"
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
pulseq_analysis:
  ids: [D4.3]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0056: Time ID -1 in a 1.4 file

## Summary

Time ID -1 (an oversampled arbitrary gradient) is new in format 1.5.0, by the
slide set that the specification cites, and MATLAB Pulseq's own 1.4.1 writer
refuses to write it. pypulseq's 1.4.1 writer writes it, and the C++ reader
and MATLAB Pulseq read it in a 1.4 file. A 1.4 `[GRADIENTS]` row has no `first` and `last`, which an
oversampled shape needs, and the two readers fill them in differently: at the
end of the event the C++ reader plays about 0 and MATLAB Pulseq plays the last
sample.

## What each source does

| Source | What it does |
|---|---|
| Specification | Gradient `<time_id>`: "… -1 means 1/2 of the default time raster (gradient oversampling case)" (section 2.8.2, `spec:395`). The text gives no revision for it. The revision history lists what 1.5.0 added (`spec:117-122`), and does not name time ID -1. |
| Slide set | "Two types of time representation (three since v1.5.0)"; "Updated in v1.5.0: regular sampling with oversampling … Marked by time_shape_id = -1"; "first and last points are not included into the shape vector" (slide 4). "First and last values are not stored as a part of the shape, but only in the 'Grad' object" (slide 8). |
| C++ reader | Reads a 1.4 `[GRADIENTS]` row of 5 values (`cpp:1081`) and sets `first` and `last` to `FLOAT_UNDEFINED`, 1.18e-38 (`cpp:1085-1086`, `cpp.h:128`). A shape with time ID -1 is oversampled in any version (`isArbGradWithOversampling`, `cpp.h:700`). `gradientsAt` interpolates to `first` and `last` at the two ends of the event (`cpp:3681`, `cpp:3686`). |
| MATLAB Pulseq | `read` of a file older than 1.5.0 marks `first` and `last` as unknown (`read.m:317`), then sets `first` to the `last` of the gradient of the previous block (`read.m:350`) and, for a time ID other than 0, `last` to the last sample of the shape (`read.m:353`). `write_v141` refuses the same event: "Current sequence contains arbitrary gradients with oversampling, which are not compatible with the format 1.4.1" (`write_v141.m:90-91`). |
| pypulseq | `read` fails with `KeyError: -1` for time ID -1 in a 1.4 file and in a 1.5 file alike (`sequence.py:1167`; `:1199` on master). That is DIS-0031, and not specific to 1.4. The writer makes time ID -1 itself: a gradient on the half raster, as `make_arbitrary_grad(..., oversampling=True)` makes, gets the time shape ID -1 (`block.py:703-706`). `write(..., v141_compat=True)` calls `write_v141` (`sequence.py:1796-1797`; `:1859-1860` on master), which writes `[VERSION]` 1.4.1 (`write_seq.py:324-327`) and each arbitrary gradient as `id amplitude amp_shape_id time_shape_id delay` (`write_seq.py:400-411`), with no check for time ID -1 and no `first` and `last`. With the default `remove_duplicates=True`, `write` first fails with `KeyError: -1` in `remove_duplicates` (`sequence.py:1167`; `:1199` on master), the line of DIS-0031; with `remove_duplicates=False` it writes the file. |

## Reproducer

Two files in [`reproducers/DIS-0056/`](../reproducers/DIS-0056/), each of one
block of 50 µs with an oversampled gradient on z (9 samples, a triangle of
peak 100000 Hz/m). `time_id_minus_1_v141.seq` is a 1.4.1 file:

```
[BLOCKS]
1 5 0 0 0 1 0 0

# id amp amp_shape_id time_shape_id delay
[GRADIENTS]
1 100000 1 -1 0
```

`time_id_minus_1_v151.seq` is the same event in a 1.5.1 file, with
`first` and `last` 0 (`1 100000 0 0 1 -1 0`).

pypulseq writes such a file itself:
[`reproducers/DIS-0056/write_v141_oversampled.py`](../reproducers/DIS-0056/write_v141_oversampled.py)
makes the same triangle with `make_arbitrary_grad(channel='z', ...,
oversampling=True)` and writes it with `Sequence.write(...,
v141_compat=True)`, first with `remove_duplicates=False`, then with the
default `remove_duplicates=True`. With `remove_duplicates=False`, the file
is 1.4.1 and has the row

```
[GRADIENTS]
1       100000 1 -1 0
```

Commands as in DIS-0001 (C++ reader plain and sanitized of pulseq-analysis
`65fc7e8`; MATLAB Pulseq under Octave 11.3.0; pypulseq 1.5.0.post1 and master
`c977214`). The values at the ends of the event are from `pulseq-cpp-oracle
--sample` (`SeqBlock::gradientsAt`) and MATLAB's `waveforms_and_times`.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification and slide set | Time ID -1 is not in a 1.4 file; a 1.4 row has no `first` and `last`. | — |
| C++ reader | — | 1.4.1 file: read (exit 0; sanitized exit 0). z at 0 µs: 0; at 50 µs: 1.18e-38 Hz/m. 1.5.1 file: 0 at both ends. 2026-10-14. |
| MATLAB Pulseq | — | 1.4.1 file: read; `first` 0, `last` 20000 Hz/m; the waveform holds 20000 Hz/m from 45 to 50 µs. 1.5.1 file: `last` 0, the waveform falls to 0 at 50 µs. 2026-10-14. |
| pypulseq | — | Both files: `KeyError: -1.0` (`sequence.py:1167`; `:1199` on master). `write_v141_oversampled.py` (`python -I`), 1.5.0.post1 and master the same: with `remove_duplicates=False`, a 1.4.1 file with the `[GRADIENTS]` row `1 100000 1 -1 0`; with `remove_duplicates=True`, `KeyError: -1`. 2026-10-14. |

## Impact

pypulseq writes such a file: a script that makes an oversampled gradient
and writes with `v141_compat=True` and `remove_duplicates=False` gets a
1.4.1 file with time ID -1, and no warning. (MATLAB Pulseq's 1.4.1 writer
refuses it.) This file, or one from another tool that writes 1.4 rows with
time ID -1, is played by the scanner's reader with a gradient that ends at
about 0, and by MATLAB Pulseq with one that ends at the last sample, so the
toolbox does not show what the scanner plays. Both readers accept a file that
the slide set does not define.

## Suggested resolution

The C++ reader and MATLAB Pulseq: reject time ID -1 in a file older than
1.5.0, as MATLAB Pulseq's `write_v141` does. pypulseq: refuse an
oversampled gradient in `write_v141`, as MATLAB Pulseq does. Or the specification says what
time ID -1 means in a 1.4 file, and where `first` and `last` come from. The
specification could also give the revision of time ID -1 in its text, as the
slide set does.

## Report

Draft, to pulseq/pulseq:

> **Time ID -1 in a 1.4 file**
>
> The slide set `doc/pulseq_shapes_and_times.pdf` dates time ID -1 from
> v1.5.0 (slide 4), and an oversampled shape needs the `first` and `last` of
> the event (slide 8), which a 1.4 `[GRADIENTS]` row does not have.
> `write_v141.m` refuses an oversampled gradient (lines 90-91). Yet both
> readers accept it in a 1.4 file: `ExternalSequence` sets `first` and `last`
> to `FLOAT_UNDEFINED` (lines 1085-1086) and plays about 0 at the end of the
> event; `read.m` sets `last` to the last sample (line 353) and plays it. For
> the attached file the end of the gradient is 1.18e-38 Hz/m in the C++
> reader and 20000 Hz/m in MATLAB. Could both readers reject time ID -1 in a
> file older than 1.5.0, as the 1.4.1 writer does?

Draft, to pulseq/pypulseq:

> **`write(v141_compat=True)` writes time ID -1 in a 1.4.1 file**
>
> Time ID -1 (an oversampled gradient) is new in format 1.5.0 (slide 4 of
> `doc/pulseq_shapes_and_times.pdf` in pulseq/pulseq), and needs the `first`
> and `last` of the event, which a 1.4 `[GRADIENTS]` row does not have.
> MATLAB Pulseq's `write_v141.m` refuses such a gradient (lines 90-91).
> `write_v141` in `write_seq.py` writes it (lines 400-411): a gradient from
> `make_arbitrary_grad(..., oversampling=True)`, written with
> `seq.write(fn, v141_compat=True, remove_duplicates=False)`, gives the row
> `1 100000 1 -1 0` in a 1.4.1 file. The C++ reader plays the end of that
> gradient as about 0, MATLAB Pulseq as the last sample. (With the default
> `remove_duplicates=True`, `write` fails with `KeyError: -1` in
> `remove_duplicates`, as in the reading issue of time ID -1.) Could
> `write_v141` refuse an oversampled gradient with a message? Script
> attached (`write_v141_oversampled.py`).

## History

- 2026-10-09: found by pulseq-analysis (old ID D22, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here; the
  citations give the lines of 1.5.0.post1, with those of master where they
  differ). The severity is `playback`, not the inventory's `acceptance`: the
  C++ reader and MATLAB Pulseq play the end of the gradient differently.
- 2026-10-14: corrected. The record said that no current writer writes time
  ID -1 in a 1.4 file. pypulseq 1.5.0.post1 and master `c977214` do, with
  `write(..., v141_compat=True, remove_duplicates=False)`
  (`write_v141_oversampled.py`, run on both versions). The pypulseq rows,
  the Summary, the Reproducer, the Impact, the Suggested resolution and the
  Report are updated, and pulseq/pypulseq is added to `report_to`.
