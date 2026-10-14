---
id: DIS-0052
title: An ADC dwell time with a decimal point, such as 25000.0
kind: spec-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "<dwell> is a float, in ns"
  - key: cpp-reader
    behavior: "reads the dwell time with %d into an int; rejects 25000.0"
  - key: matlab-pulseq
    behavior: "reads a float"
  - key: pypulseq
    behavior: "reads a float"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D15]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0052: An ADC dwell time with a decimal point, such as 25000.0

## Summary

The specification types the ADC dwell time as a float, in ns. The C++ reader
holds it as an `int` and reads it with `%d`, which stops at the decimal point;
the next `%d` cannot read `.0`, so `sscanf` stops after 3 of the 9 values. So a dwell
time written as `25000.0` makes the reader reject the file, where MATLAB
Pulseq and pypulseq read 25 µs.

## What each source does

| Source | What it does |
|---|---|
| Specification | `<dwell>` is a "float", "The ADC dwell time", in ns (section 2.8.3, `spec:437`). |
| C++ reader | `dwellTime` is an `int` (`cpp.h:140`), read with `%d` among nine values (`cpp:1148-1149`). `%d` stops at the `.` of `25000.0`, the next `%d` fails on `.0`, and `sscanf` returns 3 of the 9 values: "failed to decode ADC event" (`cpp:1150-1151`). |
| MATLAB Pulseq | Reads the row with `sscanf('%f')` and scales the dwell time by 1e-9 (`read.m:140`, `read.m:565`). Writes it with `%.0f` (`write.m:131`). |
| pypulseq | Reads it as a float, scaled by 1e-9 (`read_seq.py:172-177`). Writes it with `{:.0f}` (`write_seq.py:169`). |

## Reproducer

[`reproducers/DIS-0052/adc_dwell_decimal.seq`](../reproducers/DIS-0052/adc_dwell_decimal.seq):
a 1.5.1 file of one RF block pulse and one block of a trapezoid and an ADC of 8
samples, with `AdcRasterTime 1e-07` and the ADC row

```
[ADC]
1 8 25000.0 100 0 0 0 0 0
```

Commands as in DIS-0001.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | A dwell time of 25000 ns, a multiple of the ADC raster of 100 ns: valid. | — |
| C++ reader | — | "*** ERROR: failed to decode ADC event" (exit 1), plain and sanitized. 2026-10-14. |
| MATLAB Pulseq | — | Read; the ADC has a dwell time of 25000 ns. 2026-10-14. |
| pypulseq | — | Read; the ADC has a dwell time of 25000 ns. Both versions. 2026-10-14. |

## Impact

Both writers write the dwell time as an integer of ns, so their files are not
affected. A file from another tool that writes the float of the specification
with a decimal point is rejected by the scanner's reader. A dwell time that is
not a whole number of ns cannot be read at all, although the specification
allows it; with an ADC raster of 100 ns it is not on the raster.

## Suggested resolution

The C++ reader: read the dwell time as a float (`%f`) and round it to the
integer of ns, or of the ADC raster, that it holds. Or the specification: type
the dwell time as an integer of ns, as the binary format stores it in ps
(`spec:771`).

## Report

Draft, to pulseq/pulseq:

> **C++ reader: an ADC dwell time with a decimal point is rejected**
>
> The specification types `<dwell>` as a float in ns (section 2.8.3). The
> reader holds it as an `int` and reads it with `%d`
> (`ExternalSequence.cpp:1148`), so `%d` stops at the `.` of `25000.0`,
> `sscanf` reads only 3 of the 9 values, and `load` fails ("failed to decode
> ADC event"). MATLAB Pulseq and pypulseq read it as 25 µs. Could the reader
> read the dwell time as a float? Reproducer attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D15, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and
  master `c977214`, which agree here.
