---
id: DIS-0006
title: A shape that decompresses to more or fewer samples than it declares
kind: spec-vs-implementation
severity: crash
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "the decompressed samples must equal num_samples"
  - key: cpp-reader
    behavior: "no check: more samples write past the buffer; a final repeat with no count reads past; fewer repeat the last value"
  - key: matlab-pulseq
    behavior: "no check: decodes the samples it finds (more, or fewer with the last value repeated)"
  - key: pypulseq
    behavior: "no check in read: fewer are read; more, or a repeat with no count, fail in get_block"
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
pulseq_analysis:
  ids: [D5.5]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-13
---

# DIS-0006: A shape that decompresses to more or fewer samples than it declares

## Summary

The specification says that a shape "must" decompress to the number of
samples that it declares. No implementation checks this. For a shape that
decompresses to more samples than it declares, the C++ reader writes past the
end of its buffer, MATLAB Pulseq reads all the samples, and pypulseq fails in
`get_block`; for a shape that declares more samples than it holds, all three
read it, with the last value repeated. A shape that ends in a repeat with no
count makes the C++ reader read past the stored values.

## What each source does

| Source | What it does |
|---|---|
| Specification | "The number of points after decompressing all samples defined in a shape **must** be equal the number declared in `<num_samples>`." (section 2.9, `spec:626`) |
| C++ reader | `decodeBlock` sizes the buffer to `num_samples` (`cpp:1994`) and `decompressShape` writes each run with no bound (`cpp:2230-2231`): a shape that decompresses to more samples writes past the buffer. A shape that ends in a repeated value with no count reads `packed[countPack+1]` past the stored values (`cpp:2222`). A shape that decompresses to fewer samples leaves the rest of the buffer as it was, and the cumulative sum (`cpp:2242-2244`) adds those values to the last one: zeros of a new buffer repeat the last value; the buffer of the arbitrary gradients is reused across the axes (`cpp:2099`, `cpp:2109`). |
| MATLAB Pulseq | `decompressShape` preallocates `num_samples` (`decompressShape.m:26`) and assigns each run, which grows the array for more samples (`decompressShape.m:52`); the cumulative sum (`decompressShape.m:64`) repeats the last value for fewer. A final repeat with no count fails ("out of bound", `decompressShape.m:51`). |
| pypulseq | `read` does not check. `get_block` decodes the declared number for a shape with more samples and then fails with `ValueError` when it multiplies magnitude and phase (`sequence.py:1232`; `:1264` on master); a final repeat with no count fails with `IndexError` (`decompress_shape.py:58`); fewer samples are read. |

## Reproducer

In [`reproducers/DIS-0006/`](../reproducers/DIS-0006/), each one RF block
pulse:

- `shape_longer.seq`: the magnitude `1 0 0 97` (100 samples) declared with
  `num_samples 99`;
- `shape_count_missing.seq`: the magnitude `1 0 0` (a repeat with no count)
  declared with `num_samples 100`;
- `shape_shorter.seq`: magnitude and phase of 100 samples declared with
  `num_samples 101`.

Commands as in DIS-0001, and `pulseq-cpp-oracle --dump` for the samples.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Not a file that the specification describes ("must"). | — |
| C++ reader | — | `shape_longer.seq` and `shape_count_missing.seq`: read by the plain build (exit 0); sanitized: AddressSanitizer heap-buffer-overflow in `decompressShape` (exit 3). `shape_shorter.seq`: read, 101 samples of 1. 2026-10-13. |
| MATLAB Pulseq | — | `shape_longer.seq`: read, 100 samples. `shape_count_missing.seq`: "dataPack(4): out of bound 3" (`decompressShape.m:51`). `shape_shorter.seq`: read, 101 samples. 2026-10-13. |
| pypulseq | — | `shape_longer.seq`: `ValueError: operands could not be broadcast together with shapes (99,) (100,)` in `get_block` (`sequence.py:1232`; `:1264` on master). `shape_count_missing.seq`: `IndexError` (`decompress_shape.py:58`). `shape_shorter.seq`: read. 2026-10-13. |

## Impact

The writers compress shapes correctly, so their files are not affected. A
damaged or hand-edited shape is accepted by MATLAB Pulseq, so it looks valid
in the toolbox, and makes the scanner's reader write past a heap buffer, with
results that depend on the build. The three implementations decode the same
bad shape to different numbers of samples.

## Suggested resolution

All three implementations: after decompression, check that the number of
samples is `num_samples`, as section 2.9 requires, and reject the file
otherwise. The C++ reader: bound the writes of `decompressShape` by
`numUncompressedSamples`, and check that a repeat has its count.

## Report

Draft, to pulseq/pulseq (C++ reader and MATLAB toolbox) and pulseq/pypulseq:

> **A shape that does not decompress to `num_samples`**
>
> Section 2.9 of the specification: the decompressed samples "must" equal
> `num_samples`. None of the readers checks it. The C++ reader's
> `decompressShape` writes past its buffer of `num_samples` floats when the
> shape decompresses to more (`ExternalSequence.cpp:2230-2231`), and reads
> past the stored values when the shape ends in a repeat with no count (line
> 2222). MATLAB Pulseq reads such a shape with the number of samples that it
> finds (`decompressShape.m:52`); pypulseq fails later in `get_block`.
> Could each reader reject a shape whose length is not `num_samples`?
> Reproducers attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D29, commit `49a7e2c`); the
  overflow in the C++ reader on 2026-10-12 (D5.5).
- 2026-10-13: confirmed against the pinned sources; reproducers run in the
  C++ reader (plain and sanitized), MATLAB Pulseq and pypulseq (1.5.1 files).
- 2026-10-13: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, not at the fork that `sources.yaml` pins;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
