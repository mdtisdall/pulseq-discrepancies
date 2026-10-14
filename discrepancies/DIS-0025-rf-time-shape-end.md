---
id: DIS-0025
title: An RF time shape whose last time is before the end of the last sample's dwell
kind: spec-gap
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "silent on where a pulse with a time shape ends"
  - key: cpp-reader
    behavior: "a time shape of a regular step d: the pulse lasts N d"
  - key: matlab-pulseq
    behavior: "makes the pulse N d long; reads it back as ending at its last time, rounded up to the RF raster"
  - key: pypulseq
    behavior: "as MATLAB Pulseq"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
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
  reason: "Both writers write an arbitrary, sinc or Gauss pulse with a dwell longer than the RF raster as a time shape. The spec is silent on its end; the C++ reader ends it at N*d, and the toolboxes end it half a dwell earlier."
pulseq_analysis:
  ids: [D2.12]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0025: An RF time shape whose last time is before the end of the last sample's dwell

## Summary

An arbitrary RF pulse with a dwell `d` longer than the RF raster has its
samples at `(i + 0.5) d`, and both toolboxes make it `N d` long. They write it
with a time shape, and when they read it back, they end it at its last time,
`(N - 0.5) d`, rounded up to the RF raster. The C++ reader holds each sample
for one dwell and ends the pulse at `N d`. The specification does not say
where a pulse with a time shape ends, so the scanner plays the last half dwell
after the end that the toolboxes give the pulse, and the toolboxes' checks
accept a block that the pulse overruns on the scanner.

## What each source does

| Source | What it does |
|---|---|
| Specification | The RF `<time_id>` is the "Shape ID for the time sampling points, specified in the units of `RadiofrequencyRasterTime`" (section 2.8.1, `spec:349`). It does not say how long a sample lasts, or where the pulse ends. The slide set says that the sampling points of a regularly sampled pulse "are aligned to the centers of the dwell time periods" (slide 9), which puts the end of such a pulse at `N d`, but it does not say how a reader finds the end from a time shape. |
| C++ reader | A time shape stored in 3 or 4 values, with fewer values than samples, is a regular step: the dwell is the second stored value times the RF raster (`cpp:2015-2021`), and `shape_dur` is the dwell times the number of samples (`cpp:2063`). Any other time shape is resampled to the RF raster, to `int(0.5 + t_last)` cells (`cpp:2031`), see DIS-0010. |
| MATLAB Pulseq | `makeArbitraryRf` puts the samples at `((1:N)-0.5)*dwell` and sets `shape_dur` to `N*dwell` (`makeArbitraryRf.m:68-75`); `makeSincPulse` and `makeGaussPulse` do the same (`makeSincPulse.m:75`, `:85`; `makeGaussPulse.m:75`, `:85`). The writer stores the times as a time shape unless they compress to `0.5 1 1 N-3` (`Sequence.m:607-613`). The reader sets `shape_dur` to the last time rounded up to the RF raster (`Sequence.m:530-531`). |
| pypulseq | `make_arbitrary_rf` sets the times to `(i + 0.5) dwell` and `shape_dur` to `n_samples * dwell` (`make_arbitrary_rf.py:113-120`); `make_sinc_pulse` and `make_gauss_pulse` do the same (`make_sinc_pulse.py:113`, `:124`, and `make_gauss_pulse.py:115`, `:126`; on master `:115`, `:126` and `:118`, `:129`). The writer stores a time shape unless the times are on the cells of the RF raster (`block.py:858-866`). The reader sets `shape_dur` as MATLAB Pulseq (`sequence.py:1238-1239`; `:1270-1271` on master). |

## Reproducer

In [`reproducers/DIS-0025/`](../reproducers/DIS-0025/), one RF event of 20
samples with a dwell of 2 µs (RF raster 1 µs), in a block of 40 µs:

- `matlab_dwell_2us.seq`: written by MATLAB Pulseq under Octave 11.3.0 from
  `mr.makeArbitraryRf(ones(1,20), pi/20, 'dwell', 2e-6)`. Its time shape is
  `1 2 2 17` (the times 1, 3, …, 39 µs).
- `pypulseq_dwell_2us.seq`: written by pypulseq (1.5.0.post1 and master write
  the same file) from `make_arbitrary_rf(np.ones(20), np.pi/20, dwell=2e-6)`;
  the same time shape.
- `delay_1us.seq`: `matlab_dwell_2us.seq` with the RF delay set to 1 µs by
  hand.

Commands as in DIS-0001, and `pulseq-cpp-oracle --dump` for the samples;
`seq.checkTiming()` in MATLAB Pulseq and `check_timing()` in pypulseq after
the read.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | 20 samples at 1, 3, …, 39 µs; silent on the end of the pulse. | — |
| C++ reader | — | All three read (exit 0; sanitized exit 0). 20 samples, dwell 2 µs, `shape_dur` 40 µs. `delay_1us.seq`: the pulse ends at 41 µs, in a block of 40 µs, with no message. 2026-10-14. |
| MATLAB Pulseq | — | `makeArbitraryRf`: `shape_dur` 40 µs. After the read, all three: `rf.t` 1 to 39 µs, `shape_dur` 39 µs, `calcDuration(rf)` 39 µs. `checkTiming` passes `delay_1us.seq` (the pulse ends at 40 µs). 2026-10-14. |
| pypulseq | — | 1.5.0.post1 and master: `make_arbitrary_rf`: `shape_dur` 40 µs. After the read, all three: `rf.t` 1 to 39 µs, `shape_dur` 39 µs; `check_timing` passes `delay_1us.seq`. 2026-10-14. |

## Impact

Every arbitrary, sinc or Gaussian pulse made by MATLAB Pulseq or pypulseq
with a dwell longer than the RF raster, and stored compressed, is played by
the scanner for `N d`, while each toolbox, once it has read the file, gives
the pulse an end half a dwell earlier: the end that its timing checks, its
RF power (`calcRfPower` uses `shape_dur`) and the end of the RF event in a
read-back sequence use. A file whose block ends between the two ends passes
the toolboxes' checks, and the scanner plays the pulse past the end of the
block. A pulse that the toolboxes made themselves has a block of at least
`N d`, so it is not affected in that way.

## Suggested resolution

The specification: state where a pulse with a time shape ends; for samples at
`(i + 0.5) d` (the toolboxes' own pulses), `N d`, as the C++ reader and the
make functions of both toolboxes give. The toolboxes' readers: set
`shape_dur` to `N d` for such a time shape, so that a pulse reads back with
the duration that it was made with.

## Report

Draft, to pulseq/pulseq (specification and MATLAB toolbox), and the same for
pulseq/pypulseq:

> **The end of an RF pulse with a time shape changes on read-back**
>
> `mr.makeArbitraryRf(ones(1,20), pi/20, 'dwell', 2e-6)` (RF raster 1 µs)
> makes a pulse of 40 µs (`shape_dur`, `makeArbitraryRf.m:68-75`) with its
> samples at 1, 3, …, 39 µs. The file stores the time shape `1 2 2 17`. When
> the file is read, `Sequence.m:531` sets `shape_dur` to the last time rounded
> up to the raster: 39 µs, so `calcDuration` and `checkTiming` use 39 µs. The
> C++ reader plays the pulse for 20 dwells of 2 µs, 40 µs
> (`ExternalSequence.cpp:2020`, `2063`). With an RF delay of 1 µs in a block
> of 40 µs (attached), `checkTiming` passes, and the scanner's reader plays
> the pulse to 41 µs. pypulseq does the same (`sequence.py:1239`). Could the
> specification say where such a pulse ends, and the readers give it `N d`,
> the duration it was made with?

## History

- 2026-10-09: found by pulseq-analysis (old ID D37, commit `49a7e2c`; the
  time shape `1 2 2 17` of its figure).
- 2026-10-14: confirmed against the pinned sources; the MATLAB file written
  under Octave 11.3.0 and the pypulseq file by 1.5.0.post1 and master
  `c977214`, and all files run in the C++ reader (plain and sanitized),
  MATLAB Pulseq and pypulseq (1.5.1 files; the code paths cited do not
  depend on the version). The inventory's first reading reported to the
  specification and the C++ reader; the C++ reader's end agrees with the make
  functions of both toolboxes, so the report goes to the specification and
  the toolboxes' readers.
