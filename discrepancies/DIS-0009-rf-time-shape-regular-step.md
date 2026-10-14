---
id: DIS-0009
title: An RF time shape of a regular step, (i + 0.5) d
kind: spec-vs-implementation
severity: crash
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "the time shape gives the time sampling points, in RF rasters"
  - key: cpp-reader
    behavior: "regular only if compressed in 3 or 4 values (first time not used); else resampled, and MATLAB's short pulse is read one sample past its end"
  - key: matlab-pulseq
    behavior: "the samples at the times of the shape; writes a pulse of 4 samples or fewer uncompressed"
  - key: pypulseq
    behavior: "the samples at the times of the shape; writes a regular pulse on the RF raster as time ID 0"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq, pypulseq]
  reason: "MATLAB makeArbitraryRf writes a pulse of 1-4 samples with an uncompressed time shape 0.5 1.5 ... The C++ reader resamples it and reads past the samples."
pulseq_analysis:
  ids: [D2.10]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-13
---

# DIS-0009: An RF time shape of a regular step, (i + 0.5) d

## Summary

An RF time shape whose times are `(i + 0.5) d` is a regularly sampled pulse.
The C++ reader takes a time shape as regular only when it is stored
compressed in 3 or 4 values, and then plays the samples from 0 with a dwell
of the second stored value, without using the first time; any other storage
is resampled. MATLAB Pulseq stores a pulse of 4 samples or fewer uncompressed,
so the C++ reader resamples MATLAB's short pulses, and for a dwell of one RF
raster the resampling reads one sample past the end: a crash, or undefined
behaviour, on a file that MATLAB Pulseq writes and reads.

## What each source does

| Source | What it does |
|---|---|
| Specification | The RF `<time_id>` is the "Shape ID for the time sampling points, specified in the units of `RadiofrequencyRasterTime`" (section 2.8.1, `spec:349`). How a shape is stored is only a matter of compression (section 2.9, `spec:602`). |
| C++ reader | A time shape stored in 3 or 4 values with fewer values than samples is regular: the dwell is the second stored value times the RF raster, and the shape is not decompressed (`cpp:2015-2021`); only the samples and the dwell are kept (`cpp:2063-2067`), so the samples play from the start of the event and the first time is not used. Any other time shape is resampled to the RF raster (`cpp:2022-2050`): `int(0.5 + t_last)` cells, and in cell `c` the index moves to the next sample when the time at the index is below `c + 1` (`cpp:2039-2043`). For the times 0.5, 1.5, 2.5 the index reaches 3, and the cell reads `waveform[3]` and `waveform_p[3]`, past the 3 samples (`cpp:2044-2045`). |
| MATLAB Pulseq | Reads the samples at the times of the shape (`Sequence.m:526-531`). Writes the time shape as time ID 0 only when it compresses to `0.5 1 1 N-3` (`Sequence.m:607-609`), and `compressShape` stores a shape of 4 samples or fewer uncompressed (`compressShape.m:20`): a regular pulse of 1 to 4 samples on the RF raster is written as an uncompressed time shape `0.5 1.5 …` (run). |
| pypulseq | Reads the samples at the times of the shape (`sequence.py:1238-1239`; `:1270-1271` on master). Writes time ID 0 for a pulse whose times are on the RF raster cells (`block.py:858-860`): the same 3-sample pulse has no time shape (run). |

## Reproducer

In [`reproducers/DIS-0009/`](../reproducers/DIS-0009/):

- `matlab_short_pulse.seq`: written by MATLAB Pulseq under Octave 11.3.0 from
  `mr.makeArbitraryRf([1 1 1], pi/20, 'dwell', 1e-6)` (RF raster 1 µs) and a
  delay of 200 µs. Its RF time shape:

  ```
  shape_id 3
  num_samples 3
  0.5
  1.5
  2.5
  ```

- `short_pulse.seq`: the same pulse, written by hand.
  The same pulse of 1, 2 or 4 samples (times `0.5`, `0.5 1.5`, `0.5 1.5 2.5
  3.5`) gives the same crash in the C++ reader (runs of 2026-10-13).
- `first_time_10.seq`: 20 samples on the time shape `10 1 1 17` (times 10, 11,
  …, 29 µs), stored in 4 values.

Commands as in DIS-0001, and `pulseq-cpp-oracle --dump` for the samples.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | `matlab_short_pulse.seq`: 3 samples at 0.5, 1.5 and 2.5 µs. `first_time_10.seq`: 20 samples at 10 to 29 µs. | — |
| C++ reader | — | `matlab_short_pulse.seq`, `short_pulse.seq`: crash (exit 70); sanitized: libc++ assertion (`vector::operator[]`) in `decodeBlock` (exit 3). `first_time_10.seq`: read, dwell 1 µs, `shape_dur` 20 µs: the samples play from 0 to 20 µs. 2026-10-13. |
| MATLAB Pulseq | — | All three read; `first_time_10.seq`: `rf.t` 10 to 29 µs. 2026-10-13. |
| pypulseq | — | All three read. The same pulse written by pypulseq has time ID 0. 2026-10-13. |

## Impact

Every MATLAB Pulseq sequence with an arbitrary RF pulse of 1 to 4 samples on
the RF raster (for example a short hard pulse made with `makeArbitraryRf`)
has such a time shape, and the scanner's reader reads past the end of the
pulse's samples when it decodes the block: the result depends on the build.
A time shape stored in 3 or 4 values whose first time is not half a step is
played early by the scanner's reader.

## Suggested resolution

The C++ reader: in the resampling loop (`cpp:2037-2046`), stop the index at
the last sample; and detect a regular time shape from its decompressed times,
not from the number of stored values, so that an uncompressed `0.5 1.5 2.5`
is regular too, and use its first time.

## Report

Draft, to pulseq/pulseq:

> **C++ reader: MATLAB's short RF pulses are read past their end**
>
> MATLAB Pulseq writes an arbitrary RF pulse of 4 samples or fewer with an
> uncompressed time shape (`compressShape.m:20`, `Sequence.m:607-613`), for
> example `0.5 1.5 2.5` for 3 samples on the RF raster. The C++ reader takes
> a time shape as regular only when it is stored in 3 or 4 values with fewer
> values than samples (`ExternalSequence.cpp:2015-2016`), so it resamples this
> one; in the last cell the index reaches 3, and lines 2044-2045 read
> `waveform[3]` and `waveform_p[3]`, past the 3 samples. A file written by
> `mr.makeArbitraryRf([1 1 1], pi/20, 'dwell', 1e-6)` is attached; with a
> hardened libc++ the read is an assertion, in a release build it is
> undefined. Also, the regular branch does not use the first time of the
> shape (a shape `10 1 1 17` plays from 0, not from 10 µs).

## History

- 2026-10-09: found by pulseq-analysis (old ID D35, commit `49a7e2c`; the
  crash on `valid_rf_time_shapes.seq` in D2.10, `5bd053a`).
- 2026-10-13: confirmed against the pinned sources; the MATLAB file written
  and read under Octave 11.3.0, and all files run in the C++ reader (plain
  and sanitized), MATLAB Pulseq and pypulseq (1.5.1 files).
- 2026-10-13: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, not at the fork that `sources.yaml` pins;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
