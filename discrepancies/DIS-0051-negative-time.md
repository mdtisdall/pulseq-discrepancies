---
id: DIS-0051
title: A negative delay (written by both writers)
kind: spec-vs-implementation
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "a delay is an integer, stored unsigned; an event delay is after the start of its block"
  - key: cpp-reader
    behavior: "reads -10; inside the block, the gradient starts at 10% of its amplitude"
  - key: matlab-pulseq
    behavior: "writes and reads -10; its waveform starts the ramp 10 us before the block, in the previous block"
  - key: pypulseq
    behavior: "writes and reads -10; its waveform starts the ramp 10 us before the block, in the previous block"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
  - repo: pulseq/pulseq
    component: specification
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq, pypulseq]
  reason: "Both writers write a trapezoid delay of -10, which the spec types unsigned. The C++ reader starts the gradient at 10% inside the block; the toolboxes start the ramp in the previous block."
pulseq_analysis:
  ids: [D3.6]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0051: A negative delay (written by both writers)

## Summary

The specification types a delay as an integer, stores integers as unsigned,
and describes a delay as the time "before starting" an event in its block.
Both writers write a negative delay when a script gives one, for example a
trapezoid of delay -10 µs. The readers all read -10, but they do not play the
same gradient: the waveforms of MATLAB Pulseq and pypulseq start the ramp
10 µs before the block, inside the previous block, while the C++ reader holds
the events of one block, and its gradient starts at 10% of the amplitude at
the start of the block.

## What each source does

| Source | What it does |
|---|---|
| Specification | "**integer** types are stored as 64-bit unsigned integers" (section 2.1, `spec:176`). `<delay>` of a gradient is an "integer", "Delay before starting the gradient event" (`spec:399`); of an RF event, "Delay before starting the RF pulse" (`spec:351`); of an ADC event, "Delay between start of block and first sample" (`spec:438`). "All blocks and events are aligned to the corresponding edges of the time raster" (`spec:290`). The specification does define negative values elsewhere: the time ID -1 (`spec:395`) and the offset of a soft delay (`spec:554`). |
| C++ reader | Reads the delay of a trapezoid with `%d` (`cpp:1117-1118`) into an `int` (`cpp.h:116`). `gradientsAt` of block 2 gives 10000 Hz/m at 0 µs, 60000 at 50 µs and 100000 at 90 µs (run): the ramp is placed from -10 µs, and the part before the block is not in the block. |
| MATLAB Pulseq | `makeTrapezoid` keeps a delay of -10 µs, and `write` writes it (`write.m:117-118`). `read` reads -10 (`read.m:137`); `waveforms_and_times` gives the gradient at 190, 290, 490 and 590 µs of the sequence: the ramp starts at 190 µs, 10 µs before block 2 starts (run). |
| pypulseq | `make_trapezoid` keeps the delay, and `write` writes -10 (run). `read` reads -10; `waveforms_and_times` gives the same points as MATLAB Pulseq (run). |

## Reproducer

[`reproducers/DIS-0051/`](../reproducers/DIS-0051/):
`write_negative_delay.py` and `write_negative_delay.m` make a trapezoid of
delay -10 µs and print the `[TRAP]` section that they write;
`trap_delay_negative.seq` is a 1.5.1 file of one RF block pulse of 200 µs and
one block of a trapezoid and an ADC, whose trapezoid has the delay -10:

```
[TRAP]
1 100000 100 200 100 -10
```

The scripts ran with pypulseq 1.5.0.post1 and master `c977214`, and with
MATLAB Pulseq of `c7469123` under GNU Octave 11.3.0; the file was read as in
DIS-0001, and the gradient of the C++ reader was sampled with
`pulseq-cpp-oracle --sample` (lines `block_index time_us`).

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | A delay is not negative: not a file that the specification describes. | — |
| C++ reader | — | Read (exit 0). `--sample` of block 2 (index 1) at 0, 5, 50, 90 and 100 µs: 10000, 15000, 60000, 100000, 100000 Hz/m. 2026-10-14. |
| MATLAB Pulseq | — | `write_negative_delay.m` writes ` 1       100000 100  200 100 -10`. The file: read; the x gradient of `waveforms_and_times` has the points (190, 0), (290, 100000), (490, 100000), (590, 0) (µs, Hz/m). 2026-10-14. |
| pypulseq | — | `write_negative_delay.py` writes ` 1       100000 100  200 100 -10` (both versions). The file: read; the same four points. 2026-10-14. |

## Impact

A script that gives an event a negative delay, by mistake or to start a ramp
in the previous block, gets a file from either toolbox, with no message. The
toolboxes plot, check and simulate a gradient that starts in the previous
block, while the scanner's reader holds the block on its own and its gradient
jumps to 10% of the amplitude at the start of the block. The same holds for
the other delays that both writers write as integers.

## Suggested resolution

MATLAB Pulseq and pypulseq: refuse a negative delay when an event is made or
added to a block, so that no file has one. The specification: say that a
delay is not negative (and that the unsigned type of `spec:176` does not apply
to the values that it defines as signed, such as the time ID -1).

## Report

Draft, to pulseq/pulseq (MATLAB Pulseq), and the same to pulseq/pypulseq:

> **A negative event delay is written to the file**
>
> `makeTrapezoid(…, 'delay', -10e-6)` and `addBlock` accept a delay of
> -10 µs, and `write` writes it in `[TRAP]` (`1 100000 100 200 100 -10`). The
> specification types a delay as an unsigned integer, "before starting" the
> event. The toolbox's waveform then starts the ramp 10 µs before the block,
> in the previous block; the C++ reader, which plays each block on its own,
> starts the gradient at 10% of its amplitude at the start of the block. Could
> the toolbox refuse a negative delay? Reproducer attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D14, commit `49a7e2c`; D3.6 at
  `5bd053a`, with the runs of the writers of 2026-10-13).
- 2026-10-14: confirmed against the pinned sources; the writers and the file
  run in the C++ reader, MATLAB Pulseq and pypulseq 1.5.0.post1 and master
  `c977214`, which agree here. Severity changed from `acceptance` to
  `playback`: all three readers accept the file, and the C++ reader's gradient
  differs from the toolboxes' waveforms. The title is limited to the delay,
  the case that was run.
