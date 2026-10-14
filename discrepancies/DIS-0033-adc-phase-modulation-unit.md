---
id: DIS-0033
title: The unit of an ADC phase modulation shape
kind: spec-gap
severity: playback
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "the ADC phase shape has no unit; the scalar ADC phase offset is in rad"
  - key: cpp-reader
    behavior: "the header says rad; updateAdcPhaseModulation adds the shape to a phase in cycles and writes it back wrapped to [0, 1)"
  - key: matlab-pulseq
    behavior: "rad: writes the vector as given, adds it to the ADC phase in rad, and writes 2π × cycles itself"
  - key: pypulseq
    behavior: "rad: writes the vector as given, and adds it to the ADC phase in rad in its plot"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D2.15, D3.8, D7.6]
  commit: 5bd053a
found: 2026-10-12
checked: 2026-10-14
---

# DIS-0033: The unit of an ADC phase modulation shape

## Summary

The specification gives the samples of an ADC phase modulation shape no unit.
MATLAB Pulseq and pypulseq use the samples as radians, and so does the comment
in the C++ reader's header. The code of the C++ reader that changes the ADC
phase for a position offset, `updateAdcPhaseModulation`, uses them as cycles:
it adds them to a phase in cycles and wraps the sum to [0, 1). So a sample of
π/2 (a quarter cycle to MATLAB) leaves the reader as 0.5708 cycles (3.586 rad),
and the same file has a different ADC phase on the scanner when the position
offset is not zero. The 2π factor that is commented out (`cpp:3059-3060`)
does not change this: the code runs without it.

## What each source does

| Source | What it does |
|---|---|
| Specification | `<phase_shape_id>` is the "Shape ID of the phase modulation, 0 for no modulation", unit "--" (section 2.8.3, `spec:443`); the scalar `<phase>` of the ADC is in rad (`spec:442`). The table of revisions says that 1.5.0 ADC objects "optionally declare phase offset per sample as a vector" (`spec:120`). The shape samples have no unit (section 2.9, `spec:620`). |
| C++ reader | Reads the shape ID (`cpp:1149`) into `ADCEvent::phaseModulationShapeID`, whose comment is "Phase modulation shape of receiver (rad)" (`cpp.h:146`). `decodeBlock` does not decode the ADC phase shape; the reader's only use of it is `updateAdcPhaseModulation` (`cpp:2938-3111`), which the interpreter calls with a position offset (`cpp.h:1051-1065`). With an offset of zero it returns at once and the shape is unchanged (`cpp:2950-2959`). Else, for each ADC in a block whose gradients are not constant during the ADC (`cpp:3008`), it decompresses the shape (`cpp:3050-3058`); the multiplication by 2π is commented out (`cpp:3059-3060`). It adds each sample to the position phase, which it computes in cycles (`cpp:3028-3033`, `cpp:3062-3083`), wraps the sum to [0, 1) (`cpp:3085-3087`), and stores the result as a new shape, "already normalised ([0,1) cycles)" (`cpp:3091-3098`). So a sample is used as cycles. The RF phase shape is in cycles in the file, and the reader multiplies it by 2π to have rad (`cpp:2004-2005`); the commented-out line at `cpp:3059-3060` is the same line. |
| MATLAB Pulseq | `mr.makeAdc` takes `phaseModulation` as a vector of one value per sample, with no unit (`makeAdc.m:36-37`), next to `phaseOffset` in radians (`makeAdc.m:32`). The writer stores the vector as given (`Sequence.m:713-720`); the RF phase, in contrast, is divided by 2π (`Sequence.m:587-589`). `getBlock` gives the decompressed shape (`Sequence.m:1431-1453`). `waveforms_and_times` adds it to the phase offset in rad (`Sequence.m:2087-2097`) and returns it as `pm_adc`. `TransformFOV` stores its own position phase as `2*pi*` the phase in cycles (`TransformFOV.m:389-393`), and the plot adds the vector to the phase in rad (`SeqPlot.m:232-237`). So the unit is rad. |
| pypulseq | `make_adc` takes `phase_modulation` with no unit (`make_adc.py:48-50`). The writer stores it as given (`block.py:584-591`), and `get_block` gives the decompressed shape (`block.py:464-482`). The plot adds it to `phase_offset`, in rad (`seq_plot.py:482-489`; `:505-514` on master). `waveforms_and_times` gives one phase per ADC, without the modulation (`sequence.py:156`). So the unit is rad. |

## Reproducer

In [`reproducers/DIS-0033/`](../reproducers/DIS-0033/):

- `adc_phase_modulation.seq`: written by MATLAB Pulseq under Octave 11.3.0
  from `write_adc_phase_modulation.m`. One block: a triangle gradient on x (0
  to 1e5 Hz/m and back to 0 in 100 µs) and an ADC of 10 samples of 10 µs with
  `'phaseModulation', (0:9)*pi/4`. MATLAB writes the samples in rad:

  ```
  [ADC]
  1 10 10000 0 0 0 0 0 3

  shape_id 3
  num_samples 10
  0
  0.785398163
  1.57079633
  ...
  7.06858347
  ```

- `update_adc_phase.cpp`: a driver that loads a file with the C++ reader,
  prints the ADC phase shape of block 0, calls
  `updateAdcPhaseModulation(offset, {1, 1, 1})`, and prints the new shape.
  The `pulseq-cpp-oracle` of pulseq-analysis gives only the shape ID, so this
  driver is needed. Its header has the build command (Apple clang 21, `-std=c++11
  -fsigned-char -ffp-contract=off`, `src/` of `c7469123`).

The C++ reader also ran as `pulseq-cpp-oracle --dump` and
`pulseq-cpp-oracle-sanitized`, and MATLAB and pypulseq as in DIS-0001, with
a script for `pm_adc` and `fp_adc`. macOS arm64.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | The unit is not given. | — |
| C++ reader | — | Reads (exit 0; sanitized exit 0); ADC phase shape ID 3, not decoded. `update_adc_phase adc_phase_modulation.seq 1e-9 0 0` (an offset whose own phase is below 5e-12 cycles): the new shape is `0 0.785398 0.570796 0.356194 0.141593 0.926991 0.712389 0.497787 0.283185 0.068583`, the fraction of each sample: the samples are cycles. With `1 0 0` (1 mm): `0.000025 0.785623 0.571421 …`, where 0.000025 cycles is 1 mm × 25000 Hz·µs/m, the moment at the first sample. With `0 0 0`: returns 0, the shape stays `0 0.785398 1.570796 …`. 2026-10-14. |
| MATLAB Pulseq | — | `getBlock(1).adc.phaseModulation` is `0 0.785398 1.570796 … 7.068583`; `waveforms_and_times` gives the same values as `pm_adc`, at `t_adc` 5, 15, …, 95 µs. 2026-10-14. |
| pypulseq | — | `get_block(1).adc.phase_modulation` is `0 0.785398 1.570796 … 7.068583`; `waveforms_and_times` gives `fp_adc` `[[0, 0]]` (no modulation). `make_adc(…, phase_modulation=(0:9)·π/4)` is written as the same shape. Both versions. 2026-10-14. |

So the third sample, 1.5708, is π/2 rad (0.25 cycle) to MATLAB Pulseq and
pypulseq, and becomes 0.5708 cycles (3.586 rad) in the C++ reader when a
position offset is set.

## Impact

Every file with an ADC phase modulation shape, a 1.5 feature. MATLAB's own
`TransformFOV` writes one (2π × cycles, `TransformFOV.m:389-393`), and so do
the MATLAB demos `demoSeq/writeEpiRS_label.m:85` and
`demoSeq/writeEpiRS_label_softdelay.m:87`
(`0.1*rand`). On a scanner whose interpreter uses
`updateAdcPhaseModulation`, a shape written in rad is played as cycles when
the slice or FOV is shifted, and with no shift it is left in the file's unit.
The interpreter on the scanner is not public, so how it plays the shape after
the call is not known; but the call's result can be right only if the file
holds cycles, and the writers write rad.

## Suggested resolution

The specification: give the unit of the samples of an ADC phase modulation
shape in section 2.8.3 (`spec:443`), rad as the scalar `<phase>`, or cycles
as the RF phase shape. The C++ reader: use that unit in
`updateAdcPhaseModulation` (for rad, divide each sample by 2π before line
3085 and multiply the result by 2π before line 3094), remove the commented-out
lines 3059-3060, and make the comment of `cpp.h:146` agree. If the
specification chooses cycles, MATLAB Pulseq and pypulseq must change instead.

## Report

Draft, to pulseq/pulseq:

> **The unit of an ADC phase modulation shape: rad in MATLAB, cycles in
> `updateAdcPhaseModulation`**
>
> The specification gives `<phase_shape_id>` of an `[ADC]` row no unit
> (section 2.8.3). MATLAB Pulseq writes `adc.phaseModulation` as given and
> adds it to the ADC phase in rad (`Sequence.m:2097`); `TransformFOV` stores
> `2*pi*phase_cycle_vector` in it. `ExternalSequence.h:146` says rad too. But
> `ExternalSequence::updateAdcPhaseModulation` adds the decompressed shape to
> a phase in cycles and wraps the sum to [0, 1) (`ExternalSequence.cpp:3085-3087`);
> the 2π factor at lines 3059-3060 is commented out (and would go the wrong
> way for rad). A file written by `mr.makeAdc(10, 'Dwell', 10e-6,
> 'phaseModulation', (0:9)*pi/4)` is attached: with a position offset of 1e-9
> mm, the shape `0 0.785 1.571 2.356 …` becomes `0 0.785 0.571 0.356 …`; with
> an offset of 0 it is not changed. Which unit is meant? Please state it in
> the specification and make the reader and the header agree.

## History

- 2026-10-12: found by pulseq-analysis (old ID D44, commit `49a7e2c`; D2.15,
  D3.8 and D7.6 in `5bd053a`). pulseq-analysis said that the reader uses the
  shape as radians; at the pin the code uses it as cycles (above).
- 2026-10-14: confirmed against the pinned sources. The file written by
  MATLAB Pulseq under Octave 11.3.0 and run in the C++ reader (oracle, plain
  and sanitized, and the driver of `updateAdcPhaseModulation`), MATLAB Pulseq,
  and pypulseq 1.5.0.post1 and master `c977214`. The part of D3.8 on a shape
  whose length is not the number of samples is not in this record.
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, the two pins of `sources.yaml`;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
