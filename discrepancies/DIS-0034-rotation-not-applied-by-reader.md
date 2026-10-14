---
id: DIS-0034
title: A block that plays a rotation, in the C++ reader's output
kind: implementation-vs-implementation
severity: playback
status: withdrawn
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "the block is rotated by its normalized quaternion"
  - key: cpp-reader
    behavior: "attaches the quaternion and leaves the gradients unrotated for the interpreter; turns a position offset by the conjugate, which is right"
  - key: matlab-pulseq
    behavior: "getBlock: unrotated gradients and the quaternion; waveforms_and_times: rotated gradients"
  - key: pypulseq
    behavior: "rejects the file (unknown section, DIS-0063)"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D6.2]
  commit: 5bd053a
found: 2026-10-12
checked: 2026-10-14
---

# DIS-0034: A block that plays a rotation, in the C++ reader's output

## Summary

Withdrawn: not a discrepancy. The C++ reader gives the gradients of a block
with a rotation unrotated, and attaches the block's quaternion: it leaves the
rotation to the scanner's interpreter, by design. MATLAB Pulseq does the same
in `getBlock`, and rotates only in `waveforms_and_times`, with the same
rotation as the specification. The reader's own use of the rotation, in the
functions that change the RF and ADC phase for a position offset, turns the
offset by the conjugate quaternion, and that is right: a run gives the same
ADC phase for the rotated block as for the same block rotated with
`mr.rotate3D`. No two sources disagree about the file. pypulseq rejects the
file, which is DIS-0063.

## What each source does

| Source | What it does |
|---|---|
| Specification | The rotation extension, from 1.5.1, specifies "a rotation operation that is applied to the entire block as a whole", as a normalized quaternion; `RotQuat0` is the cosine of half the angle and the other three are the axis times its sine; line 1 of the example is a rotation by 14.77° about the negative z axis (section 2.8.4, `spec:567-580`). It recommends to compare a sequence with the extension against the same sequence rotated with `mr.rotate()` or `mr.rotate3D()` (`spec:580`). |
| C++ reader | Reads each quaternion and divides it by its norm (`cpp:1281-1292`); `GetBlock` attaches it to the block (`SeqBlock::GetRotationEvent`, `cpp.h:719`). `gradientsAt` and `gradMomentsAt` do not read it (`cpp:3558-3698`, `cpp:3700-3834`): the gradients are those of the file. `rotate_vec3_by_quat` (`cpp:2666-2684`) computes v + 2w (u × v) + 2 u × (u × v), the rotation by q (w, u), and with `c = -1` (`cpp:2680`) the rotation by its conjugate. `applyRfPhaseModulation` and `updateAdcPhaseModulation` take a position offset "in the Pulseq logical coordinate frame" (`cpp.h:1046`, `cpp.h:1062`) and, in a block with a rotation, turn it by the conjugate, "because we update the offset, not the gradients" (`cpp:2770-2778`, `cpp:3021-3025`). The phase of a gradient R g at a position r is (R g) · r = g · (Rᵀ r), so the conjugate (Rᵀ) is right for the unrotated moments that the functions use (`cpp:3067`, `cpp:3075`). |
| MATLAB Pulseq | `read` divides each quaternion by its norm (`read.m:182-184`). `getBlock` gives the gradients of the file and `block.rotation` with the quaternion (`Sequence.m:1296-1306`). `waveforms_and_times` rotates the gradients of a block with a rotation with `mr.rotate3D` (`Sequence.m:1988-1999`), which uses the matrix of `mr.aux.quat.toRotMat`, the rotation by q (`rotate3D.m:51`, `toRotMat.m`). |
| pypulseq | `read` raises `ValueError: Unknown section code: extension ROTATIONS 1` (`read_seq.py:228`): it knows no rotation extension. That is DIS-0063 (an unknown extension). |

## Reproducer

In [`reproducers/DIS-0034/`](../reproducers/DIS-0034/), written by MATLAB
Pulseq under Octave 11.3.0 from `write_rotation.m`: one block of a triangle
gradient on x (0 to 1e5 Hz/m and back to 0 in 100 µs) and an ADC of 10
samples of 10 µs, rotated by 30° about z (`mr.makeRotation(pi/6)`):

- `rotation_extension.seq`: with the rotation extension,
  `1  0.965926 0 0 0.258819`, and `RequiredExtensions ROTATIONS`.
- `rotation_explicit.seq`: the same block rotated with `mr.rotate3D`: gx of
  86602.5 Hz/m and gy of 50000 Hz/m, no extension.

The C++ reader ran with `pulseq-cpp-oracle --dump` and
`pulseq-cpp-oracle-sanitized`, and with the driver
[`update_adc_phase.cpp`](../reproducers/DIS-0033/update_adc_phase.cpp) of
DIS-0033 (`update_adc_phase FILE 3 7 0`: `gradientsAt` and `gradMomentsAt` at
the ADC samples, then `updateAdcPhaseModulation` with the offset (3, 7, 0)
mm). MATLAB Pulseq and pypulseq as in DIS-0001. macOS arm64.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Both files play the same gradients: x 86602.5, y 50000 Hz/m at the peak. | — |
| C++ reader | — | Both read (exit 0; sanitized exit 0). `rotation_extension.seq`: rotation `0.9659258 0 0 0.2588190`, `gradientsAt` at 5 µs `10000 0 0` (unrotated); `rotation_explicit.seq`: `8660.25 5000 0`. `updateAdcPhaseModulation` with (3, 7, 0) mm gives the same new ADC phase shape for both files: `0.000152 0.001372 0.003811 0.007470 0.012349 0.018142 0.023020 0.026679 0.029118 0.030338` cycles. With q instead of its conjugate the offset would be x = −0.902 mm, and the first and last samples 0.999977 and 0.995513 (computed). 2026-10-14. |
| MATLAB Pulseq | — | `rotation_extension.seq`: `getBlock` gives gx `[0 100000 0]`, no gy, and the quaternion; `waveforms_and_times` gives x `[0 86602.5 0]` and y `[0 50000 0]` at 0, 50, 100 µs, as for `rotation_explicit.seq`. 2026-10-14. |
| pypulseq | — | `rotation_extension.seq`: `ValueError: Unknown section code: extension ROTATIONS 1`. `rotation_explicit.seq`: read. Both versions. 2026-10-14. |

## Impact

None between the sources: the C++ reader leaves the rotation to the
interpreter, as the extension intends, and its offset arithmetic matches the
rotation of the specification and of MATLAB Pulseq. The pypulseq rejection is
DIS-0063; the normalization of a quaternion is DIS-0067; an extension in a file
older than 1.5.1 is DIS-0069.

## Suggested resolution

Not applicable (withdrawn).

## Report

Not reported: withdrawn.

## History

- 2026-10-12: found by pulseq-analysis (old ID D49, commit `49a7e2c`, with
  the normalization that is DIS-0067; D6.2 in `5bd053a`); the inventory
  reserved this ID for the played rotation and asked whether `cpp:3024` turns
  the offsets by the conjugate.
- 2026-10-14: run in the C++ reader (oracle, plain and sanitized, and the
  driver of `updateAdcPhaseModulation`), MATLAB Pulseq under Octave 11.3.0,
  and pypulseq 1.5.0.post1 and master `c977214`. `cpp:3024` turns the
  position offset (not the RF or ADC frequency or phase offsets) by the
  conjugate, and that gives the phase of the rotated block. Withdrawn under
  the scope rule of the migration: no two sources disagree about the file.
  `applyRfPhaseModulation` has the same code (`cpp:2770-2778`); its numbers
  were not compared.
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, the two pins of `sources.yaml`;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
