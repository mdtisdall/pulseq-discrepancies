---
id: DIS-0037
title: A 1.3 file read with a system of dead times or other rasters
kind: implementation-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.3.x"]
sources:
  - key: cpp-reader
    behavior: "1.3 block durations from the events alone, on fixed rasters of 10 µs, 1 µs and 100 ns"
  - key: matlab-pulseq
    behavior: "1.3 block durations add the RF ringdown and ADC dead time of its system, on the rasters of its system"
  - key: pypulseq
    behavior: "as MATLAB Pulseq"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
pulseq_analysis:
  ids: [D52]
  commit: 49a7e2c
found: 2026-10-12
checked: 2026-10-14
---

# DIS-0037: A 1.3 file read with a system of dead times or other rasters

## Summary

A file holds no dead time, ringdown time or other value of a scanner, and
MATLAB Pulseq and pypulseq attach the values of their `system` to the events
that they read. For a 1.4 or 1.5 file this changes only the objects in
memory and the timing checks against that system: the block durations, the
waveforms and a re-written file stay the same. A 1.3 file has no block
durations and no rasters: the readers compute the durations from the events.
The C++ reader uses the events alone and fixed rasters; MATLAB Pulseq and
pypulseq add the RF ringdown time and the ADC dead time of their system and
use its rasters. Read with a system that has dead times or another gradient
raster, the same 1.3 file has other block durations and other gradient times
than on the scanner's reader.

## What each source does

| Source | What it does |
|---|---|
| Specification | Has no dead time or ringdown time; the rasters are required definitions from 1.4.0 (section 2.5, `spec:273-276`), and the block duration is explicit from 1.4.0 (revision history, `spec:113-114`). It does not say how a 1.3 file is read. |
| C++ reader | For a file before 1.4.0, sets the rasters to 10 µs (gradient and block duration), 1 µs (RF) and 0.1 µs (ADC), whatever the file defines (`cpp:1466-1472`). Computes each block duration as the longest of the delay, `rf.delay` plus the number of RF samples (1 µs each), each gradient, `adc.delay` plus the samples times the dwell, and the trigger, then rounds up to the block raster (`cpp:1656-1708`): no dead time or ringdown time. |
| MATLAB Pulseq | Takes its rasters from its system (`Sequence.m:117`), and from `[DEFINITIONS]` when they are there (`read.m:57-77`); for a file before 1.4.0 it writes the system's rasters into the definitions (`read.m:213-225`). `getBlock` gives each RF event the system's `rfDeadTime` and `rfRingdownTime` (`Sequence.m:545-546`) and each ADC the system's `adcDeadTime` (`Sequence.m:1446`). For a file before 1.4.0 the block durations are `mr.calcDuration` of each block (`read.m:285-294`), which adds `ringdownTime` after the RF and `deadTime` after the ADC (`calcDuration.m:107`, `calcDuration.m:120-121`). |
| pypulseq | The same: rasters from `Opts` (`read_seq.py:57-60`, `:247-259`); the ADC's `dead_time` (`read_seq.py:176`, `:180`; `block.py:483`) and the RF's `dead_time` and `ringdown_time` (`sequence.py:1251-1252`; `:1283-1284` on master) from `Opts`; for a file before 1.4.0 the durations are `calc_duration` of each block (`read_seq.py:308-318`), which adds them (`calc_duration.py:42`, `:48`; `:55`, `:61` on master). |

## Reproducer

In [`reproducers/DIS-0037/`](../reproducers/DIS-0037/):

- `v131_rf_adc_grad.seq` (hand-written, version 1.3.1, no `[DEFINITIONS]`):
  block 1, an RF block pulse of 100 samples with a delay of 100 µs; block 2,
  an ADC of 100 samples of 1 µs with a delay of 10 µs; block 3, an arbitrary
  gradient of 10 samples.
- `v151_rf_adc_grad.seq`: the same events in a 1.5.1 file, with the block
  durations 200, 110 and 100 µs (the control).
- `read_with_system.m` and `read_with_system.py`: read both files with three
  systems (the default; `rfDeadTime` 100 µs, `rfRingdownTime` 20 µs and
  `adcDeadTime` 10 µs; a gradient raster of 5 µs) and print the block
  durations, `waveforms_and_times` and the timing check.

Commands as in DIS-0001 (`pulseq-cpp-oracle --dump` for the C++ block
durations), and the two scripts, run in the folder of the files
(`octave-pulseq read_with_system.m`, `python read_with_system.py`).

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent on a 1.3 file. | — |
| C++ reader | — | `v131_rf_adc_grad.seq`: read (exit 0; sanitized exit 0); `duration_ru` 20, 11, 10: blocks of 200, 110, 100 µs. 2026-10-14. |
| MATLAB Pulseq | — | `v131_rf_adc_grad.seq`: default system: 200, 110, 100 µs. Dead times: 220, 120, 100 µs; the ADC samples at 230.5 to 329.5 µs, where they are at 210.5 to 309.5 µs with the default. Gradient raster 5 µs: 200, 110, 50 µs; the gradient points every 5 µs. `v151_rf_adc_grad.seq`: 200, 110, 100 µs and the same `waveforms_and_times` with each system; `checkTiming` reports the ringdown and dead time with the second system only; the files that `write` gives after the read are the same byte for byte with each system. 2026-10-14. |
| pypulseq | — | 1.5.0.post1 and master: the same block durations and times as MATLAB Pulseq with each system; `check_timing` on the 1.5.1 file: `RF_RINGDOWN_TIME`, `POST_ADC_DEAD_TIME` and `BLOCK_DURATION_MISMATCH` with the second system only; the re-written 1.5.1 files are the same with each system. `write` after reading the 1.3.1 file fails (`KeyError: 1` in `write_seq.py:118`) with every system. 2026-10-14. |

## Impact

Only files before 1.4.0, read by MATLAB Pulseq or pypulseq with a system
whose dead times or rasters differ from the defaults (0, and 10 µs, 1 µs,
100 ns). A user who reads an old file with the system of a scanner (dead
times are usual there) sees, in plots, simulations, k-space calculations and
the total duration, blocks that are longer than the ones the scanner's reader
plays. With a gradient raster other than 10 µs, the arbitrary gradients have
another length. For files of 1.4.0 and later, the values of the system change
only the timing checks, which compare the file with that system on purpose,
and the objects in memory: no record.

## Suggested resolution

MATLAB Pulseq and pypulseq: compute the block durations of a file before
1.4.0 from the events without the system's dead time and ringdown time, and
with the rasters that the interpreter uses for such files (10 µs, 1 µs,
100 ns), as the C++ reader does; or warn that the durations depend on the
system.

## Report

Draft, to pulseq/pulseq (MATLAB) and pulseq/pypulseq:

> **Reading a 1.3 file: the block durations depend on the system**
>
> A file before 1.4.0 has no block durations. `read` computes them with
> `mr.calcDuration` (`read.m:285-294`; `read_seq.py:308-318`), which adds the
> `rfRingdownTime` and `adcDeadTime` of the `Sequence`'s system, and it takes
> the rasters from that system. The C++ reader of the interpreter uses the
> events alone and rasters of 10 µs, 1 µs and 100 ns
> (`ExternalSequence.cpp:1466-1472`, `:1656-1708`). The attached 1.3.1 file
> gives blocks of 200, 110 and 100 µs in the C++ reader and with the default
> system, but 220, 120 and 100 µs with `rfRingdownTime` 20 µs and
> `adcDeadTime` 10 µs, and 200, 110 and 50 µs with `gradRasterTime` 5 µs.
> Could the durations of an old file be computed without the system's values?

## History

- 2026-10-12: found by pulseq-analysis (old ID D52, commit `49a7e2c`; not
  in the regrouped record of `5bd053a`). The entry is about any file.
- 2026-10-14: checked whether the values of the system change what is
  played or written. For a 1.5.1 file they do not: the block durations,
  `waveforms_and_times` and the re-written file are the same with each
  system in MATLAB Pulseq and pypulseq; only the timing checks differ, which
  is their purpose. For a 1.3.1 file they change the block durations and the
  gradient times. The record is narrowed to files before 1.4.0 (title and
  `format_versions` changed); kind and severity as in the inventory. A
  missing raster in a 1.4 or later file is DIS-0046. Confirmed against the
  pinned sources; the files run in the C++ reader (plain and sanitized),
  MATLAB Pulseq (Octave 11.3.0) and pypulseq. Only version 1.3.1 was run; the
  code paths cited are those of every version before 1.4.0.
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, the two pins of `sources.yaml`;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
