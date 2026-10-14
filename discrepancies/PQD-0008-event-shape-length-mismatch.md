---
id: PQD-0008
title: The shapes of one event with different numbers of samples
kind: spec-gap
severity: crash
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "pairs RF magnitude, phase and time by sample; silent on other lengths"
  - key: cpp-reader
    behavior: "RF phase shorter than magnitude: reads past the phase; longer: plays the magnitude's length; ADC phase: accepts"
  - key: matlab-pulseq
    behavior: "rejects an RF event of unequal shapes; accepts an ADC phase shape of another length"
  - key: pypulseq
    behavior: "rejects an RF event of unequal shapes in get_block; accepts an ADC phase shape of another length"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D3.8, D5.7]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-13
---

# PQD-0008: The shapes of one event with different numbers of samples

## Summary

The specification pairs the magnitude, phase and time shapes of an RF event
sample by sample, but does not say what a reader does when their lengths
differ. MATLAB Pulseq and pypulseq reject an RF event whose magnitude and
phase differ in length. The C++ reader reads past the phase when it is
shorter than the magnitude (a crash, or undefined behaviour), and plays the
magnitude's length when the phase is longer. An ADC phase shape whose length
is not the number of ADC samples is read by all three.

## What each source does

| Source | What it does |
|---|---|
| Specification | The RF `<time_id>` gives "the time sampling points" of the samples (section 2.8.1, `spec:349`); the ADC `<phase_shape_id>` is the "Shape ID of the phase modulation" (section 2.8.3, `spec:443`). Nothing on shapes of different lengths. |
| C++ reader | RF: decompresses magnitude and phase to their own lengths (`cpp:1993-2003`), and `checkRF` reads `rfPhase[i]` for each index of the magnitude (`cpp:2284-2290`): past the phase when it is shorter. A longer phase is kept; the event plays the magnitude's length (`cpp:2063`). An extended trapezoid whose time shape and waveform differ in length is rejected (`cpp:2190-2192`). An ADC phase shape of another length is accepted (run). |
| MATLAB Pulseq | RF: `rf.signal = amplitude*mag.*exp(1j*2*pi*phase)` fails on unequal lengths ("nonconformant arguments", `Sequence.m:524`). Extended trapezoid: asserts equal lengths (`Sequence.m:1401`). ADC phase shape of another length: read (run). |
| pypulseq | RF: `get_block` fails with `ValueError` on unequal lengths (`sequence.py:1232`; `:1264` on master). Extended trapezoid: `ValueError` "Mismatch between time shape length" (`block.py:435-437`). ADC phase shape of another length: read (run). |

## Reproducer

In [`reproducers/PQD-0008/`](../reproducers/PQD-0008/), each one block:

- `rf_phase_shorter.seq`: an RF magnitude of 100 samples, phase `0 0 6` of 8;
- `rf_phase_longer.seq`: the same magnitude, phase of 110 samples;
- `adc_phase_length.seq`: an ADC of 8 samples with a phase shape of 4;
- `ext_trap_lengths.seq`: an extended trapezoid of 3 amplitudes and 4 times.

Commands as in PQD-0001, and `pulseq-cpp-oracle --dump` for the samples.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent. | — |
| C++ reader | — | `rf_phase_shorter.seq`: crash (exit 70); sanitized: libc++ assertion (`vector::operator[]`) in `checkRF` (exit 3). `rf_phase_longer.seq`: read, magnitude and phase of 100 samples. `adc_phase_length.seq`: read. `ext_trap_lengths.seq`: rejected, "uncompressed extended trapezoid time and wave shape lengths do not match". 2026-10-13. |
| MATLAB Pulseq | — | Both RF files: "product: nonconformant arguments" (`Sequence.m:524`). `adc_phase_length.seq`: read, a phase modulation of 4 values. `ext_trap_lengths.seq`: assertion failed (`Sequence.m:1401`). 2026-10-13. |
| pypulseq | — | Both RF files: `ValueError: operands could not be broadcast together` in `get_block` (`sequence.py:1232`; `:1264` on master). `adc_phase_length.seq`: read. `ext_trap_lengths.seq`: `ValueError` (`block.py:436`). 2026-10-13. |

## Impact

Both writers take the magnitude and phase of an RF event from one signal
(pulseq-analysis D3.8), so their files are not affected. A file from another
tool with an RF phase shorter than its magnitude crashes the scanner's reader;
one with a longer phase is played by the scanner and rejected by both
toolboxes. An ADC phase shape of the wrong length is accepted everywhere,
with a meaning that no source defines.

## Suggested resolution

The specification: state that the magnitude, phase and time shapes of an RF
event have the same number of samples, and that an ADC phase shape has one
value per ADC sample. The C++ reader: reject an RF event whose shapes differ
in length, as it does for an extended trapezoid.

## Report

Draft, to pulseq/pulseq:

> **The shapes of one RF event with different numbers of samples**
>
> The specification does not say that the magnitude, phase and time shapes of
> an RF event (or the phase shape of an ADC) have the same length. MATLAB
> Pulseq and pypulseq reject an RF event whose magnitude and phase differ. The
> C++ reader's `checkRF` reads `rfPhase[i]` for each index of the magnitude
> (`ExternalSequence.cpp:2284-2290`), past the end of a shorter phase: a
> crash. A longer phase is played with the magnitude's length. Could the
> specification require equal lengths, and the C++ reader reject unequal ones,
> as it does for an extended trapezoid (line 2190)? Reproducers attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D34, commit `49a7e2c`).
- 2026-10-13: confirmed against the pinned sources; reproducers run in the
  C++ reader (plain and sanitized), MATLAB Pulseq and pypulseq (1.5.1 files).
  pypulseq rejects the RF case in `get_block` (pulseq-analysis recorded it
  as read, from `read` alone), so pypulseq is not a maintainer to report to.
- 2026-10-13: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, not at the fork that `sources.yaml` pins;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
