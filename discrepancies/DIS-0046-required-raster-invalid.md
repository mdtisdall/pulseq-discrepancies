---
id: DIS-0046
title: A required raster that is missing, zero, negative or not finite
kind: spec-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "the four rasters are required from 1.4.0; no range for their values"
  - key: cpp-reader
    behavior: "rejects a missing raster and NaN; reads 0 and a negative value; rejects an arbitrary gradient on a gradient raster other than 10 us"
  - key: matlab-pulseq
    behavior: "rejects a missing raster only when [DEFINITIONS] comes after [VERSION]; reads 0, a negative value and NaN"
  - key: pypulseq
    behavior: "takes the raster of its Opts for a missing one; reads 0, a negative value and NaN"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
  - repo: pulseq/pulseq
    component: specification
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq, pypulseq]
  reason: "Both writers write a raster of NaN or 0 through setDefinition/set_definition. The C++ reader rejects NaN as missing, and both toolboxes read it."
pulseq_analysis:
  ids: [D11]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0046: A required raster that is missing, zero, negative or not finite

## Summary

From 1.4.0, the four rasters `GradientRasterTime`, `RadiofrequencyRasterTime`,
`AdcRasterTime` and `BlockDurationRaster` are required definitions. The C++
reader rejects a file without one. pypulseq reads it, with the raster of its
own `Opts` in place of the missing one, and MATLAB Pulseq reads it when
`[DEFINITIONS]` comes before `[VERSION]`. The specification gives no range for
the values: the C++ reader rejects `nan`, which both toolboxes read; all three
read 0 and a negative value.

## What each source does

| Source | What it does |
|---|---|
| Specification | "Starting from the Pulseq format revision 1.4.0, the following definitions are reserved … the definitions labeled as **required** are compulsory": the four rasters, "specified in seconds" (section 2.5, `spec:267-276`). No range for the values. |
| C++ reader | From 1.4.0, a raster that is not defined gives "Required: definition … is not present in the file" and `load` fails (`cpp:1476-1500`). A value is read with `operator>>` into a list of doubles (`cpp:1437-1445`); `nan` does not read as a number, so the list is empty and the raster counts as missing. 0 and -1e-06 are read. An arbitrary gradient on a gradient raster other than 10 µs fails in `decodeBlock` (`cpp:2115-2121`), so `GradientRasterTime 0` is rejected when a block has one. |
| MATLAB Pulseq | Checks the four rasters when it reads `[DEFINITIONS]`, and only if the version is already 1.4.0 or later (`read.m:80-83`); with `[DEFINITIONS]` before `[VERSION]`, the version is still 0 (`read.m:45`), there is no check, and the raster of `mr.opts` stays. A value is read with `str2double`, and kept as text when it is not finite (`read.m:463-466`); 0, -1e-06 and `nan` are read. |
| pypulseq | Starts from the rasters of its `Opts` (`read_seq.py:57-60`) and replaces each one that the file defines (`read_seq.py:77-90`); only a missing `BlockDurationRaster` gives a warning (`read_seq.py:91-92`). No check of a value. |

## Reproducer

Changes of the `[DEFINITIONS]` of a 1.5.1 file of one RF block pulse and one
block of a trapezoid and an ADC, in
[`reproducers/DIS-0046/`](../reproducers/DIS-0046/):

| File | Change |
|---|---|
| `raster_missing.seq` | No `AdcRasterTime`. |
| `raster_missing_definitions_first.seq` | No `AdcRasterTime`, and `[DEFINITIONS]` before `[VERSION]`. |
| `adc_raster_zero.seq` | `AdcRasterTime 0`. |
| `rf_raster_negative.seq` | `RadiofrequencyRasterTime -1e-06`. |
| `grad_raster_nan.seq` | `GradientRasterTime nan`. |
| `grad_raster_zero.seq` | `GradientRasterTime 0`, and a third block with an arbitrary gradient. |

Commands as in DIS-0001.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | The two files without `AdcRasterTime` do not have a required definition. The others: silent. | — |
| C++ reader | — | Both `raster_missing` files: "Required: definition AdcRasterTime is not present in the file" (exit 1). `grad_raster_nan.seq`: "Required: definition GradientRasterTime is not present in the file" (exit 1). `grad_raster_zero.seq`: `decodeBlock` fails for the block of the arbitrary gradient (exit 1). `adc_raster_zero.seq`, `rf_raster_negative.seq`: read (exit 0). Plain and sanitized. 2026-10-14. |
| MATLAB Pulseq | — | `raster_missing.seq`: error "Required definitions AdcRasterTime are missing in the file" (`read.m:83`). `raster_missing_definitions_first.seq`: read. The other four: read. 2026-10-14. |
| pypulseq | — | Both `raster_missing` files: read. `adc_raster_zero.seq`, `rf_raster_negative.seq`, `grad_raster_nan.seq`: read. `grad_raster_zero.seq`: `read` and `get_block` succeed; `waveforms_and_times` raises `Warning: Time vector elements are not monotonically increasing` (`sequence.py:1695`; `:1758` on master). Both versions. 2026-10-14. |

## Impact

Both writers write the four rasters from their system limits, so their files
are not affected. A file from another tool, or edited by hand, without a
raster is refused by the scanner's reader, while pypulseq checks, plots and
simulates it with a raster that is not in the file (its default), and MATLAB
Pulseq does the same when the sections are in that order. A raster of 0, below
0 or not a number has no meaning, and the readers accept it in different
cases.

## Suggested resolution

pypulseq: reject a file of 1.4.0 or later without one of the four rasters, as
the C++ reader and MATLAB Pulseq do. MATLAB Pulseq: check the rasters after
the whole file is read, not when `[DEFINITIONS]` is read, so the order of the
sections does not matter. The specification: say that each raster is a
finite number above 0.

## Report

Draft, to pulseq/pypulseq:

> **`read` accepts a file without a required raster**
>
> From 1.4.0, `GradientRasterTime`, `RadiofrequencyRasterTime`,
> `AdcRasterTime` and `BlockDurationRaster` are required definitions
> (specification, section 2.5). `read` starts from the rasters of the
> `Opts` (`read_seq.py:57-60`) and keeps them for a raster that the file does
> not define, with a warning only for `BlockDurationRaster`. The C++ reader
> and MATLAB Pulseq reject such a file. Could `read` raise an error for a
> missing raster in a file of 1.4.0 or later? Reproducer attached
> (`raster_missing.seq`).

Draft, to pulseq/pulseq (MATLAB Pulseq and the specification):

> **The required rasters: the order of the sections, and their values**
>
> `read` checks the required rasters when it reads `[DEFINITIONS]`, and only
> when the version is already known to be 1.4.0 or later (`read.m:80-83`). A
> file with `[DEFINITIONS]` before `[VERSION]` and no `AdcRasterTime` is read
> with the raster of `mr.opts`; the C++ reader rejects it. Could the check run
> after the whole file is read?
>
> Also, the specification does not give a range for the rasters: the C++
> reader rejects `GradientRasterTime nan` (it reads no number), MATLAB Pulseq
> and pypulseq read it; all three read `AdcRasterTime 0` and
> `RadiofrequencyRasterTime -1e-06`. Could section 2.5 say that each raster is
> a finite number above 0? Reproducers attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D11, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducers run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and
  master `c977214`, which agree here. New: MATLAB Pulseq reads a file without
  a raster when `[DEFINITIONS]` comes before `[VERSION]`. The C++ reader's
  rejection of an arbitrary gradient on a raster other than 10 µs is its own
  condition (D28 of pulseq-analysis), not part of this record. `report_to`: the C++ reader is
  not in it (the inventory had it): it rejects the cases that the
  specification decides.
