---
id: DIS-0059
title: A time that is not a multiple of its raster
kind: spec-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "gradient times and the ADC dwell must be multiples of their rasters"
  - key: cpp-reader
    behavior: "reads the times as written, with no error or warning"
  - key: matlab-pulseq
    behavior: "read accepts them; checkTiming reports them"
  - key: pypulseq
    behavior: "read accepts them; check_timing reports them"
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
priority:
  level: high
  written_by: [matlab-pulseq, pypulseq]
  reason: "Both writers write an ADC dwell off the ADC raster, such as 25050 ns. The spec forbids it, and every reader accepts it with no message."
pulseq_analysis:
  ids: [D26]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0059: A time that is not a multiple of its raster

## Summary

The specification says that gradient events start and end on the gradient
raster, that the ramps and flat top of a trapezoid are multiples of it, and
that the ADC dwell time must be a multiple of the ADC raster. A trapezoid with
a ramp or a delay off the gradient raster, or an ADC dwell off the ADC raster,
is read with no error or warning by the C++ reader, MATLAB Pulseq's `read`
and pypulseq's `read`. The timing checks of the two toolboxes report it, when
the user calls them.

## What each source does

| Source | What it does |
|---|---|
| Specification | "Gradient events may only start and end at time points which are multiple of `GradientRasterTime` …; for trapezoid events, ramp times and plateau duration may also only be equal to multiples of `GradientRasterTime`" (section 2.6, `spec:290`). `AdcRasterTime`: "ADC dwell time must be integer multiple of the specified AdcRasterTime" (section 2.5, `spec:275`). |
| C++ reader | Does not compare the times with the rasters (run: exit 0, no message). |
| MATLAB Pulseq | `read` does not check (run). `checkTiming` (`Sequence.m:211`, through `mr.checkTiming`) reports each: "adc: dwell time is not an integer multiple of sys.adcRasterTime" (`Sequence.m:282-283`), and the trapezoid with its times for the other two. |
| pypulseq | `read` does not check (run). `check_timing` (`check_timing.py:23`) reports each as `RASTER` (`dwell`, `delay`, `rise_time`). |

## Reproducer

Three 1.5.1 files in [`reproducers/DIS-0059/`](../reproducers/DIS-0059/),
each of one block that holds its event:

| File | Event | Off the raster |
|---|---|---|
| `trap_ramp_off_raster.seq` | `[TRAP]` `1 100000 95 200 100 0` | rise time 95 µs on a gradient raster of 10 µs |
| `trap_delay_off_raster.seq` | `[TRAP]` `1 100000 100 200 100 5` | delay 5 µs |
| `adc_dwell_off_raster.seq` | `[ADC]` `1 8 25050 0 0 0 0 0 0` | dwell 25050 ns on an ADC raster of 100 ns |

Commands as in DIS-0057.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Not valid: each time breaks a "must" or "may only". | — |
| C++ reader | — | All three read, no message (exit 0; sanitized exit 0). 2026-10-14. |
| MATLAB Pulseq | — | All three read. `checkTiming`: false for each, with the messages above. 2026-10-14. |
| pypulseq | — | All three read. `check_timing`: false for each (`RASTER` on `rise_time`, `delay`, `dwell`). 2026-10-14. |

## Impact

The scanner's reader plays the times as written. A gradient that starts or
ends between two edges of the gradient raster, or an ADC with a dwell that
the hardware cannot make, is not what the specification describes, and the
reader does not tell the user. MATLAB Pulseq and pypulseq tell the user only if
the timing check is called after `read`.

## Suggested resolution

The C++ reader: reject (or at least warn about) a time that is not a
multiple of its raster, as sections 2.5 and 2.6 require. The `read` of
MATLAB Pulseq and pypulseq could warn too.

## Report

Draft, to pulseq/pulseq (C++ reader, MATLAB Pulseq) and pulseq/pypulseq:

> **Times off their raster are accepted**
>
> Sections 2.5 and 2.6 require the ADC dwell to be a multiple of
> `AdcRasterTime`, and gradient start and end times, ramps and flat tops to be
> multiples of `GradientRasterTime`. `ExternalSequence` reads a trapezoid
> with a rise time of 95 µs or a delay of 5 µs on a 10 µs raster, and an ADC
> with a dwell of 25050 ns on a 100 ns raster, with no message; so do MATLAB's
> and pypulseq's `read`. Only `checkTiming` / `check_timing` report them.
> Could the readers reject such times? Reproducers attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D26, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here; the
  citations give the lines of 1.5.0.post1).
