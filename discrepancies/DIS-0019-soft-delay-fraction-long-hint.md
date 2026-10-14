---
id: DIS-0019
title: A soft delay offset with a fraction, or a hint longer than 31 characters
kind: spec-gap
severity: playback
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "an example with whole-µs offsets and short hints; no types, no length of the hint"
  - key: cpp-reader
    behavior: "reads the offset with %d: -100.5 is offset -100, factor 0.5, hint '2 TE'; keeps 31 characters of a hint"
  - key: matlab-pulseq
    behavior: "writes and reads an offset with a fraction and a hint of any length"
  - key: pypulseq
    behavior: "rejects an offset with a fraction (ValueError); writes the offset rounded to a whole µs; keeps a long hint"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq, pypulseq]
  reason: "MATLAB Pulseq writes a soft delay offset of -100.5 with %g, and both writers write hints longer than 31 characters. The C++ reader misreads the offset and cuts the hint; pypulseq fails with ValueError."
pulseq_analysis:
  ids: [D2.16]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0019: A soft delay offset with a fraction, or a hint longer than 31 characters

## Summary

The specification gives the soft delay row only by an example, with
whole-µs offsets and short hints. MATLAB Pulseq writes the offset with `%g`,
so an offset of -100.5 µs is written `-100.5`, and it writes a hint of any
length. The C++ reader reads the offset with `%d`: it takes -100 µs, reads
`.5` as the factor and `2 TE` as the hint, so the scanner computes a
different block duration; pypulseq rejects the file. The C++ reader also
keeps only the first 31 characters of a hint, so two hints that differ
after the 31st character are the same hint to it.

## What each source does

| Source | What it does |
|---|---|
| Specification | The soft delay extension is given by an example: `# id num offset factor hint`, the offset in `us`, rows such as `1 0 -7840 2 TE` (section 2.8.4, `spec:550-558`). The duration is `TE/2-7840 µs` for that row, that is the value of the user interface divided by the factor, plus the offset (`spec:562`). There is no table of types, and nothing on the length of the hint. The binary format stores the offset as `int64` picoseconds (section 3.1, `spec:723`; section 3.3, `spec:787`). |
| C++ reader | Holds the offset as `int` and the hint as `char[32]` (`cpp.h:194`, `cpp.h:198-200`). Reads the row with `"%d%d%d%f%n"` (`cpp:1330`): for `1 0 -100.5 2 TE`, `%d` reads `-100`, `%f` reads `.5` as the factor, and the rest, `2 TE`, is the hint. Copies at most 31 characters of the hint (`cpp:1334-1335`). The reader does not compute the duration; it gives the offset, the factor and the hint to the scanner's interpreter. |
| MATLAB Pulseq | `mr.makeSoftDelay` takes any offset and any hint without white space (`makeSoftDelay.m:24-25`, `:32-34`). Writes the offset in µs with `%g` and the hint with `%s` (`write.m:214-215`). Reads the offset with `str2num` (`read.m:173`). `applySoftDelay` sets the duration to `value/factor + offset`, rounded to the block raster (`Sequence.m:2567-2568`). |
| pypulseq | `make_soft_delay` takes any offset and any hint without white space (`make_soft_delay.py:101-105`). Writes the offset with `np.round` and `{:.0f}` (`write_seq.py:235`, `:239`): -100.5 µs is written `-100`. Reads the offset with `int()` (`read_seq.py:221`), so `-100.5` raises `ValueError`. Keeps the whole hint (`str`, `read_seq.py:221`). |

## Reproducer

In [`reproducers/DIS-0019/`](../reproducers/DIS-0019/):

- `matlab_soft_delay.seq`: written by MATLAB Pulseq under Octave 11.3.0:

  ```matlab
  seq = mr.Sequence();
  seq.addBlock(mr.makeDelay(1e-3), mr.makeSoftDelay(0, 'TE', -100.5e-6, 2));
  seq.addBlock(mr.makeDelay(1e-3), mr.makeSoftDelay(1, 'InversionTimeOfTheFirstContrast_A'));
  seq.addBlock(mr.makeDelay(1e-3), mr.makeSoftDelay(2, 'InversionTimeOfTheFirstContrast_B'));
  seq.write('matlab_soft_delay.seq');
  ```

  Its soft delay rows:

  ```
  extension DELAYS 1
  1 0 -100.5 2 TE
  2 1 0 1 InversionTimeOfTheFirstContrast_A
  3 2 0 1 InversionTimeOfTheFirstContrast_B
  ```

  The two long hints have 33 characters; their first 31 characters are the
  same.
- `pypulseq_soft_delay.seq`: the same three blocks written by pypulseq
  1.5.0.post1 (`make_soft_delay('TE', numID=0, offset=-100.5e-6, factor=2)`
  and the two long hints). Its first soft delay row is `1 0 -100 2 TE`.
  pypulseq master writes the same rows.

Commands as in DIS-0001, `pulseq-cpp-oracle --dump` for the values that the
C++ reader holds, and `seq.applySoftDelay('TE', 10e-3, ...)` in MATLAB Pulseq.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent on a fraction and on the length of the hint. With TE = 10 ms, the row `1 0 -100.5 2 TE` read as written gives 10000/2 - 100.5 = 4899.5 µs. | — |
| C++ reader | — | `matlab_soft_delay.seq`: read (exit 0; sanitized build exit 0). Block 1: `offset` -100 µs, `factor` 0.5, `hint` `2 TE`: with the rule of `spec:562`, TE = 10 ms gives 10000/0.5 - 100 = 19900 µs, and the hint is not `TE`. Blocks 2 and 3: both hints `InversionTimeOfTheFirstContrast`. `pypulseq_soft_delay.seq`: block 1 `offset` -100 µs, `factor` 2, `hint` `TE`; the long hints cut in the same way. 2026-10-14. |
| MATLAB Pulseq | — | `matlab_soft_delay.seq`: block 1 `offset` -100.5 µs, `factor` 2, `hint` `TE`; blocks 2 and 3: the whole hints. `applySoftDelay` with TE = 10 ms: block 1 lasts 4900 µs (4899.5 µs on the 10 µs block raster). `pypulseq_soft_delay.seq`: offset -100 µs, the whole hints. 2026-10-14. |
| pypulseq | — | 1.5.0.post1 and master: `matlab_soft_delay.seq`: `ValueError: invalid literal for int() with base 10: '-100.5'` (`read_seq.py:221`). `pypulseq_soft_delay.seq`: offset -100 µs, the whole hints. 2026-10-14. |

## Impact

A MATLAB Pulseq sequence with a soft delay whose offset is not a whole µs
(for example an offset computed from other timings) is played by the
scanner's interpreter with the wrong factor and offset, and with a hint
that does not match the hint of the other rows of the same delay; pypulseq
cannot read the file. A pypulseq sequence loses the fraction when it is
written. A hint longer than 31 characters is cut by the scanner's reader;
two soft delays whose hints share their first 31 characters get the same
hint there with two numeric IDs, which `applySoftDelay` of MATLAB Pulseq
treats as an error (one numeric ID for each hint, `Sequence.m:2551-2557`).

## Suggested resolution

The specification: give a table of types for the soft delay row (an integer
or a float offset, in µs), and a maximum length of the hint, or say that a
hint has no maximum length. Then the C++ reader reads the offset as that
type (a `%f` or a check that the token is an integer) and rejects, or
warns about, a longer hint; pypulseq reads the offset as that type.

## Report

Draft, to pulseq/pulseq:

> **The type of the soft delay offset, and the length of the hint**
>
> Section 2.8.4 of the specification gives the soft delay rows only by an
> example, with whole-µs offsets. MATLAB Pulseq writes the offset with `%g`
> (`write.m:214-215`), so `mr.makeSoftDelay(0, 'TE', -100.5e-6, 2)` gives the
> row `1 0 -100.5 2 TE`. `ExternalSequence::load` reads it with
> `"%d%d%d%f%n"` (`ExternalSequence.cpp:1330`): offset -100, factor 0.5,
> hint `2 TE`; for TE = 10 ms the duration is then 19900 µs in place of
> 4899.5 µs. The reader also keeps 31 characters of a hint
> (`SOFT_DELAY_HINT_LENGTH`, `ExternalSequence.h:194`; line 1334-1335 of the
> .cpp file), which the specification does not limit. Could the
> specification give the type of the offset and the maximum length of the
> hint, and the C++ reader follow them? Reproducer attached
> (`matlab_soft_delay.seq`, written by MATLAB Pulseq).

Draft, to pulseq/pypulseq:

> **`read` fails on a soft delay offset with a fraction**
>
> MATLAB Pulseq writes a soft delay offset with `%g`, so a file can have the
> row `1 0 -100.5 2 TE`. `Sequence.read` parses the offset with `int()`
> (`read_seq.py:221`) and raises `ValueError: invalid literal for int()
> with base 10: '-100.5'`; `write` rounds the offset to a whole µs
> (`write_seq.py:239`). Reproducer attached (`matlab_soft_delay.seq`).
> The specification does not give the type of the offset; this is reported
> to pulseq/pulseq as well.

## History

- 2026-10-09: found by pulseq-analysis (old ID D16, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources. The MATLAB file written
  and read under Octave 11.3.0, the pypulseq file written by 1.5.0.post1
  and master; both files run in the C++ reader (plain and sanitized), MATLAB
  Pulseq and pypulseq 1.5.0.post1 and master `c977214`. The two versions of
  pypulseq behave the same here, and their lines are the same.
