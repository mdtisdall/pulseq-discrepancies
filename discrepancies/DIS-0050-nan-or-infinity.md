---
id: DIS-0050
title: NaN or infinity in a float column
kind: spec-gap
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "types the columns as floats; silent on NaN and infinity"
  - key: cpp-reader
    behavior: "reads nan and inf with sscanf"
  - key: matlab-pulseq
    behavior: "reads nan and inf with sscanf"
  - key: pypulseq
    behavior: "rejects: ValueError or OverflowError when read removes duplicate events"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq]
  reason: "MATLAB Pulseq writes NaN in [TRAP] and [RF] with no message. The C++ reader and MATLAB read it, and pypulseq's read fails with ValueError in round_data."
pulseq_analysis:
  ids: [D3.5]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0050: NaN or infinity in a float column

## Summary

The specification types the amplitudes, offsets and other columns as floats,
and does not say whether NaN and infinity are floats of the file. The C++
reader and MATLAB Pulseq read `nan` and `inf` as such (both with `sscanf`), and
pypulseq rejects them: `read` removes duplicate events, which rounds each value
to a number of significant digits, and the logarithm of NaN or infinity cannot
be made an integer.

## What each source does

| Source | What it does |
|---|---|
| Specification | The tables of section 2.8 type `<amp>` and the offsets as "float" (for example `spec:346`, `spec:391`); "**floating-point** numbers are in the 64-bit IEEE 754 floating-point format" (`spec:176`). It does not say whether the text of a float can be NaN or infinity. |
| C++ reader | Reads the floats with `sscanf("%f")` (`cpp:1042`, `cpp:1117`), which reads `nan` and `inf`. |
| MATLAB Pulseq | Reads a row with `sscanf('%f')` (`read.m:565`), which reads `nan` and `inf` (`NaN`, `Inf`). |
| pypulseq | Reads the row; then `read` calls `remove_duplicates` (`read_seq.py:443-444`, by default), whose `round_data` rounds each value to a number of significant digits with `math.ceil(math.log10(abs(d) + 1e-12))` (`event_lib.py:275-284`): `math.ceil` of NaN raises `ValueError: cannot convert float NaN to integer`, and of infinity `OverflowError` (`event_lib.py:282`). `write` removes duplicates too (`write_seq.py:49-50`). |

## Reproducer

Changes of a 1.5.1 file of one RF block pulse and one block of a trapezoid and
an ADC, in [`reproducers/DIS-0050/`](../reproducers/DIS-0050/):
`rf_amp_nan.seq` (the RF amplitude is `nan`), `trap_amp_nan.seq` (the
trapezoid amplitude is `nan`) and `trap_amp_inf.seq` (`inf`). The scripts
`write_nan.m` and `write_nan.py` make a trapezoid of amplitude NaN and a block
pulse of frequency offset NaN, and write them.

Commands as in DIS-0001; the scripts ran with MATLAB Pulseq of `c7469123`
under GNU Octave 11.3.0 and with pypulseq 1.5.0.post1 and master `c977214`.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent. | — |
| C++ reader | — | All three: read, each block decoded (exit 0), plain and sanitized. 2026-10-14. |
| MATLAB Pulseq | — | All three: read; `getBlock` and `waveforms_and_times` succeed. `write_nan.m` writes `1          250 1 2 3 500 0 0 0 NaN 0 e` in `[RF]` and ` 1          NaN 100  200 100   0` in `[TRAP]`. 2026-10-14. |
| pypulseq | — | `rf_amp_nan.seq`, `trap_amp_nan.seq`: `ValueError: cannot convert float NaN to integer` (`event_lib.py:282`). `trap_amp_inf.seq`: `OverflowError: cannot convert float infinity to integer` (`event_lib.py:282`). `write_nan.py`: `add_block` accepts both events, and `write` fails with `ValueError: cannot convert float NaN to integer` (`event_lib.py:282`). Both versions. 2026-10-14. |

## Impact

MATLAB Pulseq writes `NaN` in `[TRAP]` for a trapezoid of amplitude NaN, and
in `[RF]` for a frequency offset NaN, with no message, while pypulseq fails to
write them. So a script error in MATLAB Pulseq gives a file that the scanner's
reader plays with a NaN value, and that pypulseq cannot read.

## Suggested resolution

The specification: say that each float is finite (no NaN or infinity). The
readers can then reject such a value with a message, and MATLAB Pulseq can
refuse to write it.

## Report

Draft, to pulseq/pulseq:

> **Specification: NaN and infinity in a float column**
>
> The specification types the amplitudes and offsets as floats but does not
> say whether `nan` or `inf` is one. The C++ reader and MATLAB Pulseq read
> them (`sscanf`), and pypulseq rejects them. A trapezoid of amplitude `nan`
> is read by the scanner's reader without a message. Could the specification
> say that each float of the file is finite? Reproducers attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D14, commit `49a7e2c`; D3.5 at
  `5bd053a`, with the runs of the writers of 2026-10-13).
- 2026-10-14: confirmed against the pinned sources; reproducers run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and
  master `c977214`, which agree here. `report_to` is the specification only
  (the inventory also had MATLAB Pulseq and pypulseq): the specification
  decides first.
