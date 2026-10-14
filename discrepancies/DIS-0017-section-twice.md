---
id: DIS-0017
title: A section that appears twice
kind: spec-gap
severity: playback
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "silent on how many times a section can appear"
  - key: cpp-reader
    behavior: "reads only the last section of each name"
  - key: matlab-pulseq
    behavior: "reads each copy in file order; [GRADIENTS] and [TRAP] add, other sections replace"
  - key: pypulseq
    behavior: "reads each copy in file order; event tables add, [DEFINITIONS], [BLOCKS], [SHAPES] replace"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
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
  level: low
  written_by: []
  reason: "No writer writes a section twice. The readers read a repeated section differently, and the C++ reader rejects one file with a message, but no reader crashes."
pulseq_analysis:
  ids: [D3.3]
  commit: 5bd053a
found: 2026-10-12
checked: 2026-10-14
---

# DIS-0017: A section that appears twice

## Summary

The specification does not say whether a section can appear more than once. The
C++ reader reads only the last section of each name; MATLAB Pulseq and pypulseq
read every copy in file order, and add or replace by section. With two
`[DEFINITIONS]` sections of different `BlockDurationRaster`, the C++ reader
plays each block twice as long as MATLAB Pulseq and pypulseq. With two `[TRAP]`
sections, the C++ reader rejects a file that both toolboxes play.

## What each source does

| Source | What it does |
|---|---|
| Specification | Silent. Section 2 names each section, and gives no rule on how many times it can appear. The IDs of the events of one class must be unique (section 2.2, `spec:183`). |
| C++ reader | Its index keeps one position for each header name, the last one (`m_fileIndex[line] = fileStream.tellg()`, `cpp:1768`), so each section is read from its last copy and the earlier copies are not read. The block durations are in units of the `BlockDurationRaster` of that last `[DEFINITIONS]` (`cpp:1495-1500`, `cpp:1540`, `cpp.h:705`). A block that uses a gradient of an earlier `[TRAP]` is "references to undefined events" (`cpp:1579-1583`, `cpp:2254-2256`). |
| MATLAB Pulseq | Reads the sections in file order (`read.m:49-195`). A second `[DEFINITIONS]` replaces the definitions, and sets each raster that it has (`read.m:56-77`). `[BLOCKS]` turns the durations into seconds with the `blockDurationRaster` that is set when `[BLOCKS]` is read (`read.m:117`, `read.m:512`). `[GRADIENTS]` and `[TRAP]` add to the gradients already read (the library is passed on, `read.m:130-137`); a second `[RF]`, `[ADC]`, `[SHAPES]` or `[BLOCKS]` replaces the first (`read.m:117-152`). |
| pypulseq | Reads the sections in file order. A second `[DEFINITIONS]` replaces the definitions and sets the rasters (`read_seq.py:73-92`). `[BLOCKS]` uses the `block_duration_raster` that is set when it is read (`read_seq.py:139-144`, `read_seq.py:546`). `[RF]`, `[GRADIENTS]`, `[TRAP]`, `[ADC]` and `extension TRIGGERS` add to the library already read (`read_seq.py:145-181`, `read_seq.py:194`); a second `[BLOCKS]` or `[SHAPES]` replaces the first (`read_seq.py:144`, `read_seq.py:187`). The lines are the same on master. |

## Reproducer

Two files in [`reproducers/DIS-0017/`](../reproducers/DIS-0017/), each of two
blocks of one trapezoid (400 µs, 100000 and 200000 Hz/m) and no shapes:

- `definitions_twice.seq`: `[DEFINITIONS]` (`BlockDurationRaster 1e-05`),
  `[BLOCKS]` (two blocks of duration 50), `[TRAP]`, and a second
  `[DEFINITIONS]` at the end, the same but with `BlockDurationRaster 2e-05`.
- `trap_twice.seq`: trapezoid 1 in a first `[TRAP]` and trapezoid 2 in a
  second `[TRAP]`.

The sections of `definitions_twice.seq` after `[VERSION]`:

```
[DEFINITIONS]
AdcRasterTime 1e-07
BlockDurationRaster 1e-05
GradientRasterTime 1e-05
RadiofrequencyRasterTime 1e-06

# NUM DUR RF GX GY GZ ADC EXT
[BLOCKS]
1 50 0 1 0 0 0 0
2 50 0 2 0 0 0 0

# id amplitude rise flat fall delay
[TRAP]
1 100000 100 200 100 0
2 200000 100 200 100 0

[DEFINITIONS]
AdcRasterTime 1e-07
BlockDurationRaster 2e-05
GradientRasterTime 1e-05
RadiofrequencyRasterTime 1e-06
```

Commands as in DIS-0001 (C++ reader plain and sanitized of pulseq-analysis
`65fc7e8`, with `--dump`; MATLAB Pulseq under Octave 11.3.0; pypulseq
1.5.0.post1 and master `c977214`).

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent. | — |
| C++ reader | — | `definitions_twice.seq`: read (exit 0), 2 blocks of `duration_ru` 50, with `BlockDurationRaster` 2e-05: 1000 µs each. `trap_twice.seq`: rejected (exit 1), "Block 1 contains references to undefined events ... GX:1". Same exit codes with the sanitized build. 2026-10-14. |
| MATLAB Pulseq | — | `definitions_twice.seq`: read, block durations 0.5 ms and 0.5 ms, while its definitions give `BlockDurationRaster` 2e-05. `trap_twice.seq`: read, 2 blocks of 0.4 ms, trapezoids of 100000 and 200000 Hz/m. 2026-10-14. |
| pypulseq | — | `definitions_twice.seq`: read, block durations 0.5 ms and 0.5 ms, definitions `BlockDurationRaster` 2e-05. `trap_twice.seq`: read, 2 blocks of 0.4 ms, trapezoids of 100000 and 200000 Hz/m. 1.5.0.post1 and master the same. 2026-10-14. |

## Impact

MATLAB Pulseq and pypulseq write each section once (`write.m:25-289`,
`write_seq.py:56-277`), so their files are not affected. A file that joins two
files, or is edited by hand, can repeat a section. Then the scanner's reader
plays only the last copy of each section, and the toolboxes play a mix of the
copies: different block durations, or a file that the scanner's reader rejects
and the toolboxes play.

## Suggested resolution

The specification: say that each section appears at most once (each
`extension` section once for each ID). The C++ reader, MATLAB Pulseq and
pypulseq: reject a file with a repeated section, in place of reading the last
copy, or a mix of the copies.

## Report

Draft, to pulseq/pulseq (specification, C++ reader, MATLAB toolbox):

> **A section that appears twice**
>
> The specification does not say whether a section can appear twice. The
> readers do different things: `ExternalSequence::load` reads only the last
> copy of each section (its index keeps the last header,
> `ExternalSequence.cpp:1768`); MATLAB `read.m` reads each copy in file order,
> adds a second `[TRAP]` or `[GRADIENTS]` to the first and replaces the other
> sections, and converts the block durations with the `BlockDurationRaster`
> that is known when `[BLOCKS]` is read. A file with a second
> `[DEFINITIONS]` (`BlockDurationRaster 2e-05`) after `[BLOCKS]` gives blocks
> of 1000 µs in the C++ reader and of 500 µs in MATLAB Pulseq; a file with two
> `[TRAP]` sections is rejected by the C++ reader and played by MATLAB Pulseq.
> Could the specification say that each section appears once, and the readers
> reject a repeated section? Reproducers attached.

Draft, to pulseq/pypulseq:

> **`read` merges a repeated section**
>
> `Sequence.read` reads each copy of a section in file order: it adds a second
> `[RF]`, `[GRADIENTS]`, `[TRAP]` or `[ADC]` to the first, replaces a second
> `[DEFINITIONS]`, `[BLOCKS]` or `[SHAPES]`, and computes the block durations
> with the raster that is set when `[BLOCKS]` is read. The C++ reader of
> pulseq/pulseq reads only the last copy, so the same file gives blocks of
> 500 µs in pypulseq and 1000 µs on the scanner. Could `read` reject a
> repeated section? Reproducers attached.

## History

- 2026-10-12: found by pulseq-analysis (old ID D10, commit `49a7e2c`; also its
  section 4, S4-9).
- 2026-10-14: confirmed against the pinned sources; reproducers written and run
  in the C++ reader (plain and sanitized), MATLAB Pulseq and pypulseq. The
  example of pulseq-analysis (`bad_section_duplicate.seq`) repeats `[TRAP]`
  with the same row (the same ID and values); the reproducers use different
  rows, so that the readers differ.
  The runs used 1.5.1 files; the code paths cited do not depend on the
  version.
- 2026-10-14: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq; the two behave the same here, and the cited
  lines are the same in both.
