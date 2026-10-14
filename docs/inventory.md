# The inventory of the findings of pulseq-analysis

This document sorts every finding of pulseq-analysis into the records of this
repository. For each record it reserves a DIS ID and gives its kind, severity,
the maintainers to report to, and the batch of the migration that adds it. It
is the plan of the migration: when the last batch is merged, this document
stays as the map from the IDs of pulseq-analysis to the DIS IDs.

## 1. The sources of the findings

| Source | Version | Cited as |
|---|---|---|
| `docs/discrepancies.md` of [pulseq-analysis](https://github.com/mdtisdall/pulseq-analysis), the record before the regrouping, with four sources (specification, C++ reader, MATLAB Pulseq, pypulseq) and section 4 | commit `49a7e2c` (the richest of the 13 versions; `858ef25`, the first, and `f501393` were compared with it) | old IDs `D01a` to `D56`; `S4-n` for a finding of section 4 that no entry has |
| `docs/discrepancies.md` and `packages/pulseq-cpp-siemens/docs/specification.md` of pulseq-analysis, the records by kind of decision | commit `5bd053a` | IDs `D1.1` to `D7.6`; `D59` and `D60` are old IDs that only the second file has |
| `docs/findings-for-pulseq-checks.md` and `TODO.md` of pulseq-analysis | commit `5bd053a` | `F-281` (lines 281-289 of the first), `F-TODO-10`, `F-TODO-11` (lines of the second) |
| [mdtisdall/pypulseq-issues](https://github.com/mdtisdall/pypulseq-issues), draft issue reports for pypulseq and notes for MATLAB Pulseq | commit `1de4a1d`; draft 14 on the branch `docs/14-crlf-signature` (`14b320c`) | `P01` to `P14` |

The IDs of pulseq-analysis name decisions of its interpreters, and they were
renumbered on 2026-10-13. A record of this repository names a condition in a
file, so one record can take several IDs of pulseq-analysis, and one ID can
give several records (for example `D14`).

## 2. How the findings were sorted

A finding is a record when two sources of the format, documents or
implementations, disagree about a file: what it means, whether it is valid,
what is written for the same input, or what is played; or when the
specification contradicts itself (`docs/record-format.md`, section 1). A
defect of one implementation is a record only when it makes that
implementation disagree with another source; a crash of the C++ reader on a
file that the specification allows, or that a writer writes, is such a
record. A choice of pulseq-analysis's own interpreters is not a record.

The kinds and the severities are first readings, from the findings. Each
record confirms them when it is written, against the sources at the pins of
`sources.yaml`, and can change them. "Report to" names the source to change:
"spec" is the specification, "C++" the C++ reader, "MATLAB" MATLAB Pulseq
(all three `pulseq/pulseq`), and "pypulseq" `pulseq/pypulseq`.

## 3. The batches

Each batch is one branch and one PR, and adds its records with `status: draft`
or `status: confirmed`. The batches add different records, so they can be
written at the same time.

| Batch | Records | Contents |
|---|---|---|
| 1 | DIS-0001 to DIS-0014 | An implementation crashes, hangs, or reads memory that it does not own. |
| 2 | DIS-0015 to DIS-0037 | The sources play the same file differently. |
| 3 | DIS-0038 to DIS-0055 | The text of the specification, and the syntax of a file: what is accepted, rejected, or changed when it is read back. |
| 4 | DIS-0056 to DIS-0073 | The meaning of the events, the extensions and the signature: what is accepted, rejected, or changed when it is read back. |

## 4. The records

| DIS | Batch | Condition in the file | Kind | Severity | Report to | pulseq-analysis, old IDs (`49a7e2c`) | pulseq-analysis, IDs (`5bd053a`) | Other sources |
|---|---|---|---|---|---|---|---|---|
| DIS-0001 | 1 | `[VERSION]` after `[BLOCKS]`, or as the last section | `spec-gap` | `crash` | spec, C++ | D05 | D2.1, D5.1 | — |
| DIS-0002 | 1 | A shape with no blank line after its last sample | `spec-vs-implementation` | `crash` | C++ | D07 | D3.11, D5.1 | S4-8 |
| DIS-0003 | 1 | A reference to an event, shape or extension that does not exist; a `[GRADIENTS]` row of shape ID 0 | `spec-vs-implementation` | `crash` | C++, pypulseq | D21 | D5.1, D5.2 | — |
| DIS-0004 | 1 | An RF event with time ID -1 | `spec-vs-implementation` | `crash` | C++, MATLAB | D22 | D5.3 | — |
| DIS-0005 | 1 | A cycle in an extension list | `spec-vs-implementation` | `crash` | C++, MATLAB, pypulseq | D23 | D5.4 | S4-4 |
| DIS-0006 | 1 | A shape that decompresses to more or fewer samples than it declares | `spec-vs-implementation` | `crash` | C++, MATLAB, pypulseq | D29 | D5.5 | S4-3 |
| DIS-0007 | 1 | An event that uses a shape with no sample | `spec-gap` | `crash` | spec, C++ | D33 | D3.7, D5.6 | — |
| DIS-0008 | 1 | The shapes of one event (RF or gradient) with different numbers of samples | `spec-gap` | `crash` | spec, C++, pypulseq | D34 | D3.8, D5.7 | S4-4, S4-10 |
| DIS-0009 | 1 | An RF time shape of a regular step, stored in 3 or 4 values | `spec-vs-implementation` | `crash` | C++ | D35 | D2.10 | — |
| DIS-0010 | 1 | Any other RF time shape (resampled by the C++ reader); a time shape of one sample or times that do not increase | `spec-vs-implementation` | `crash` | C++ | D36 | D2.11, D3.9, D5.8 | — |
| DIS-0011 | 1 | An RF time shape whose last time does not fit an `int` | `spec-gap` | `crash` | C++ | — | D5.9 | — |
| DIS-0012 | 1 | An extended trapezoid of one point at a time above 0 | `spec-gap` | `crash` | C++ | D59 | D5.10 | — |
| DIS-0013 | 1 | An extended trapezoid time that does not fit a `long` | `spec-gap` | `crash` | C++ | D60 | D5.11 | — |
| DIS-0014 | 1 | `[SHAPES]` as the last section (a file with no `[SIGNATURE]`): pypulseq 1.5.0.post1 hangs (pulseq/pypulseq#358; fixed by #359 on 2026-02-03, not yet in a release) | `spec-vs-implementation` | `crash` | pypulseq | — | — | F-TODO-10 |
| DIS-0015 | 2 | A blank or `#` line inside a section | `spec-vs-implementation` | `playback` | C++, MATLAB, pypulseq | D06 | D2.5 | S4-8 |
| DIS-0016 | 2 | The last section with no blank line after it | `spec-gap` | `playback` | spec, C++, pypulseq | D56 | D2.2 | — |
| DIS-0017 | 2 | A section that appears twice | `spec-gap` | `playback` | spec, C++, MATLAB, pypulseq | D10 | D3.3 | S4-9 |
| DIS-0018 | 2 | A number with a fraction in an integer column (for example an RF delay of `100.5`) | `spec-vs-implementation` | `playback` | C++, MATLAB | D14 | — | — |
| DIS-0019 | 2 | A soft delay offset with a fraction, or a hint longer than 31 characters | `spec-gap` | `playback` | spec, C++, pypulseq | D16 | D2.16 | — |
| DIS-0020 | 2 | A value with more digits than a 32-bit float holds | `spec-vs-implementation` | `playback` | C++ | D18 | D7.2 | — |
| DIS-0021 | 2 | Block IDs that are not in increasing order | `spec-vs-implementation` | `playback` | MATLAB | D20 | D7.3 | — |
| DIS-0022 | 2 | An amplitude shape with a sample outside [-1, 1] | `spec-vs-implementation` | `playback` | C++, MATLAB, pypulseq | D30 | — | — |
| DIS-0023 | 2 | An RF magnitude shape with a sample below 0 | `spec-vs-implementation` | `playback` | C++ | D31 | D2.8 | — |
| DIS-0024 | 2 | An RF phase shape with a sample outside [0, 1) | `spec-gap` | `playback` | spec, C++ | D32 | D2.9 | — |
| DIS-0025 | 2 | An RF time shape whose last time is before the end of the last sample's dwell | `spec-gap` | `playback` | spec, C++ | D37 | D2.12 | — |
| DIS-0026 | 2 | A 1.4 arbitrary gradient on the default raster (no `first` and `last`) | `spec-gap` | `playback` | spec, C++, MATLAB, pypulseq | D39 | D4.4 | — |
| DIS-0027 | 2 | A 1.4 arbitrary gradient with a time shape (no `first`) | `spec-gap` | `playback` | spec, C++ | D40 | D4.5 | — |
| DIS-0028 | 2 | A 1.5 arbitrary gradient with a time shape: the C++ reader does not use `first` and `last` | `spec-vs-implementation` | `playback` | C++ | — | — | F-281 |
| DIS-0029 | 2 | An arbitrary gradient on the default raster (time ID 0), between its samples | `spec-vs-implementation` | `playback` | MATLAB | D41 | D2.13 | — |
| DIS-0030 | 2 | A gap between two gradient events on one axis | `spec-gap` | `playback` | spec, MATLAB, pypulseq | D42 | D2.14, D7.4 | P12 |
| DIS-0031 | 2 | An oversampled arbitrary gradient (time ID -1) | `spec-vs-implementation` | `playback` | C++, pypulseq | D43 | D6.1 | S4-6, P03, P04 |
| DIS-0032 | 2 | The area of an oversampled arbitrary gradient: MATLAB Pulseq counts only the raster-centre samples, not the waveform that the specification defines | `spec-vs-implementation` | `playback` | MATLAB | — | — | P05 |
| DIS-0033 | 2 | An ADC phase modulation shape: its unit (and the 2π factor commented out at `cpp:3059-3060`) | `spec-gap` | `playback` | spec, C++ | D44 | D2.15, D3.8, D7.6 | — |
| DIS-0034 | 2 | A block that plays a rotation: the C++ reader's output is not rotated, and it turns position offsets by the conjugate (`cpp:3024`, to check) | `implementation-vs-implementation` | `playback` | C++ | D49 | D6.2 | — |
| DIS-0035 | 2 | A vertex of a gradient time shape off the gradient raster (slide 6 against slide 4) | `spec-contradiction` | `playback` | spec | D26 | D1.3 | — |
| DIS-0036 | 2 | The C++ reader rounds the times of an extended trapezoid to whole µs (`cpp:2182`, not yet run) | `spec-vs-implementation` | `playback` | C++ | — | — | S4-1 |
| DIS-0037 | 2 | A file read with no dead time, ringdown time or default raster: MATLAB and pypulseq add the values of a system | `implementation-vs-implementation` | `playback` | MATLAB, pypulseq | D52 | — | — |
| DIS-0038 | 3 | The number of fields of an `[RF]`, `[GRADIENTS]` or `[ADC]` row, and two other sections (prose against tables and examples) | `spec-contradiction` | `documentation` | spec | D01a, D01b, D01c | D1.2 | P13 |
| DIS-0039 | 3 | An extension header whose `STRING_ID` is a word (table against examples) | `spec-contradiction` | `documentation` | spec | D55 | D1.4 | — |
| DIS-0040 | 3 | The label flag `NOSLC` of the specification, which every implementation spells `NOSCL` | `spec-vs-implementation` | `acceptance` | spec | D50 | D2.19 | — |
| DIS-0041 | 3 | A `[VERSION]` value such as `5.0`, an unknown key, or a revision of two digits | `spec-vs-implementation` | `acceptance` | C++, MATLAB, pypulseq | D04 | — | — |
| DIS-0042 | 3 | A `[VERSION]` section with no `revision` line: the C++ reader takes 0 | `spec-gap` | `acceptance` | spec, C++ | — | — | S4-2 |
| DIS-0043 | 3 | A section that the format does not have | `spec-gap` | `acceptance` | spec, MATLAB, pypulseq | D08 | D2.4 | — |
| DIS-0044 | 3 | A `[DELAYS]` section in a file of 1.4.0 or later | `spec-vs-implementation` | `acceptance` | MATLAB, pypulseq | D09 | — | — |
| DIS-0045 | 3 | A data line before the first section | `spec-gap` | `acceptance` | spec | D06 | D3.2 | — |
| DIS-0046 | 3 | A required raster that is missing, zero, negative or not finite | `spec-vs-implementation` | `acceptance` | C++, MATLAB, pypulseq | D11 | — | — |
| DIS-0047 | 3 | A definition or a `[SIGNATURE]` hash whose text reads as a number | `spec-vs-implementation` | `round-trip` | MATLAB, pypulseq | D13 | D2.7, D7.1 | P09a, P09b, F-TODO-11 |
| DIS-0048 | 3 | A row with too few or too many values (for example a `[BLOCKS]` row of 7 values) | `spec-vs-implementation` | `acceptance` | C++, MATLAB | D14 | — | — |
| DIS-0049 | 3 | A byte that is not UTF-8 | `spec-gap` | `acceptance` | spec, C++, MATLAB | D14 | D3.1 | — |
| DIS-0050 | 3 | NaN or infinity in a float column | `spec-gap` | `acceptance` | spec, MATLAB, pypulseq | D14 | D3.5 | — |
| DIS-0051 | 3 | A negative time or count (written by both writers) | `spec-vs-implementation` | `acceptance` | MATLAB, pypulseq | D14 | D3.6 | — |
| DIS-0052 | 3 | An ADC dwell time with a decimal point, such as `2500.0` | `spec-vs-implementation` | `acceptance` | C++ | D15 | — | — |
| DIS-0053 | 3 | An RF `use` letter that is not one of `e r i s p o u` | `spec-vs-implementation` | `acceptance` | C++, MATLAB, pypulseq | D17 | — | — |
| DIS-0054 | 3 | pypulseq's `add_block` writes an RF event of `use='other'` as undefined | `implementation-vs-implementation` | `round-trip` | pypulseq | — | — | P08 |
| DIS-0055 | 3 | IDs of shapes, events or blocks that are not positive or not unique | `spec-vs-implementation` | `acceptance` | C++, MATLAB, pypulseq | D19 | D3.4 | — |
| DIS-0056 | 4 | Time ID -1 in a 1.4 file | `spec-vs-implementation` | `acceptance` | C++, MATLAB | D22 | D4.3 | — |
| DIS-0057 | 4 | A file with no block | `spec-vs-implementation` | `acceptance` | C++, MATLAB, pypulseq | D24 | — | — |
| DIS-0058 | 4 | An event that lasts longer than its block | `spec-vs-implementation` | `acceptance` | C++, MATLAB, pypulseq | D25 | D7.4 | — |
| DIS-0059 | 4 | A time that is not a multiple of its raster | `spec-vs-implementation` | `acceptance` | C++, MATLAB, pypulseq | D26 | — | — |
| DIS-0060 | 4 | A gradient that is not 0 at a start after a delay, or at an end before the end of its block | `spec-vs-implementation` | `acceptance` | C++, MATLAB, pypulseq | D27 | — | — |
| DIS-0061 | 4 | An arbitrary gradient on a gradient raster other than 10 µs | `spec-vs-implementation` | `acceptance` | C++ | D28 | — | — |
| DIS-0062 | 4 | The rows of a 1.4 file, and the RF `center` that it does not have | `spec-gap` | `round-trip` | spec, C++ | D01a, D01b, D01c, D38 | D4.2, D7.5 | S4-7 |
| DIS-0063 | 4 | An unknown extension that the file does not require | `spec-vs-implementation` | `acceptance` | pypulseq | D45 | D2.17 | — |
| DIS-0064 | 4 | `[EXTENSIONS]` as the last section | `spec-gap` | `acceptance` | spec, C++ | D46 | D2.3 | — |
| DIS-0065 | 4 | An unknown extension that the file requires | `spec-vs-implementation` | `acceptance` | MATLAB, pypulseq | D47 | — | — |
| DIS-0066 | 4 | Two ROTATIONS or RF_SHIMS objects in one block | `spec-vs-implementation` | `acceptance` | C++ | D48 | — | — |
| DIS-0067 | 4 | A rotation quaternion that is not normalized, or of norm 0 | `spec-gap` | `acceptance` | spec, C++ | D49 | D2.18, D3.10 | — |
| DIS-0068 | 4 | A `LABELSET` or `LABELINC` row with a label name that a reader does not know | `spec-gap` | `acceptance` | spec, C++, MATLAB, pypulseq | D50 | D2.19 | — |
| DIS-0069 | 4 | An extension, or a label flag, in a file older than the revision that introduced it | `spec-vs-implementation` | `acceptance` | C++ | D45, D49, D50 | D4.6, D4.7 | — |
| DIS-0070 | 4 | A `[SIGNATURE]` hash of a file with CRLF line ends, or a hash that does not match | `spec-vs-implementation` | `acceptance` | spec, C++ | D53 | — | P14 |
| DIS-0071 | 4 | A `[SIGNATURE]` section without `Type` or `Hash` | `spec-vs-implementation` | `acceptance` | C++, MATLAB, pypulseq | D54 | — | — |
| DIS-0072 | 4 | Two event rows with equal values and different IDs (pypulseq merges them) | `implementation-vs-implementation` | `round-trip` | pypulseq | D51 | — | — |
| DIS-0073 | 4 | pypulseq's `make_arbitrary_grad(oversampling=True)` accepts a slew rate 4 times too high | `implementation-vs-implementation` | `acceptance` | pypulseq | — | — | P01 |

## 5. Findings that are not records

| Source IDs | Reason |
|---|---|
| D02 / D1.1 | No disagreement: every implementation rejects a file with no `[VERSION]`, as the specification recommends. (pypulseq fails with an unhandled exception, not a message: a defect, not a discrepancy.) |
| D03 / D4.1, S4-11 | No disagreement among the sources: the specification is silent on other versions, and the readers broadly agree. The version gate is a choice of pulseq-analysis. |
| D12 / D2.6 | No disagreement: each source keeps the last definition. |
| D7.1 to D7.6 | Choices of pulseq-analysis's interpreter `cpp-siemens` about how to present what the C++ reader reads. Each upstream condition is in the record of its old ID. |
| S4-5 | The C++ reader drops the labels PMC and TRID on purpose: the scanner's interpreter handles them (the user, 2026-10-13). Out of scope. |
| S4-12 | A note on pulseq-analysis's own document (section 4 was stale). |
| P02 | pypulseq's `get_block` returns a wrong `shape_dur` for an oversampled gradient: the return value of an API. Upstream issue #423, PR #424. |
| P06, P07 | pypulseq's `calculate_pns` time and memory: performance. |
| P10a, P10b | `signatureFile` / `signature_file` is `'Text'` after `read` and `'text'` after `write`: the state of an object in memory. Upstream pulseq/pulseq#295, #296 and pulseq/pypulseq#427, #428. |
| P11a, P11b | A `Sequence` keeps the `[SIGNATURE]` hash after `add_block` and after `read` of an unsigned file: the state of an object in memory. |
