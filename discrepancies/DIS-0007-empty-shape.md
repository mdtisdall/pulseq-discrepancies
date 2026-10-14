---
id: DIS-0007
title: An event that uses a shape with no sample
kind: spec-gap
severity: crash
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "silent on a shape of num_samples 0"
  - key: cpp-reader
    behavior: "copies from, and indexes, an empty vector"
  - key: matlab-pulseq
    behavior: "rejects the file (an error in readShapes)"
  - key: pypulseq
    behavior: "rejects the file (ValueError in read)"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D3.7, D5.6]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-13
---

# DIS-0007: An event that uses a shape with no sample

## Summary

The specification does not say whether a shape can have no sample. MATLAB
Pulseq and pypulseq reject a file with a shape of `num_samples 0` (both fail
while they read `[SHAPES]`); the C++ reader reads it, and when an event uses
the shape it copies from, and indexes, an empty vector: a crash, or undefined
behaviour.

## What each source does

| Source | What it does |
|---|---|
| Specification | Silent. A shape is a header and "a list of samples values (one per line)" (section 2.9, `spec:602`); `<num>` is the "Number of samples of the uncompressed shape" (`spec:619`), with no lower bound. |
| C++ reader | Reads a shape of no sample, uncompressed (`cpp:951-971`). An event that uses it: `decompressShape` copies from `&encoded.samples.front()` of the empty vector (`cpp:2203`) into `&waveform[0]` of an empty vector (`cpp:1994-1995` for RF). |
| MATLAB Pulseq | `readShapes` fails: "horizontal dimensions mismatch (0x2 vs 1x1)" (`read.m:654`). |
| pypulseq | `read` skips the empty line after `num_samples 0` (`read_seq.py:687`; `:689` on master) and reads the next `shape_id` line as a sample: `ValueError` (`read_seq.py:689`; `:691` on master). |

## Reproducer

[`reproducers/DIS-0007/shape_empty.seq`](../reproducers/DIS-0007/shape_empty.seq):
one RF block pulse whose magnitude is

```
shape_id 1
num_samples 0

```

Commands as in DIS-0001.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent. | — |
| C++ reader | — | Crash (exit 70); sanitized: libc++ assertion (`vector::operator[]`) in `decodeBlock` (exit 3). 2026-10-13. |
| MATLAB Pulseq | — | "horizontal dimensions mismatch (0x2 vs 1x1)" (`read.m:654`). 2026-10-13. |
| pypulseq | — | `ValueError: could not convert string to float: 'shape_id 2'` (`read_seq.py:689`; `:691` on master). 2026-10-13. |

## Impact

The writers do not write an event with no sample (pulseq-analysis D3.7: in
runs of 2026-10-13, both makers fail on an arbitrary RF or gradient of no
sample). A file from another tool with such a shape is rejected by both
toolboxes, with messages that do not name the cause, and crashes the
scanner's reader.

## Suggested resolution

The specification: state that a shape has at least one sample (or that an
event cannot use a shape of none). The C++ reader: reject a shape of no
sample, or an event that uses one, with a message.

## Report

Draft, to pulseq/pulseq:

> **A shape with no sample**
>
> The specification does not say whether `num_samples` can be 0. The C++
> reader reads such a shape, and an event that uses it makes `decompressShape`
> copy from `samples.front()` of an empty vector into `&waveform[0]` of an
> empty vector (`ExternalSequence.cpp:2203`, 1994-1995): a crash. MATLAB
> Pulseq and pypulseq reject the file while they read `[SHAPES]`. Could the
> specification require at least one sample, and the C++ reader reject such
> a shape? Reproducer attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D33, commit `49a7e2c`).
- 2026-10-13: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq (a 1.5.1 file).
- 2026-10-13: pypulseq checked at the release 1.5.0.post1 and at master
  `c977214` of pulseq/pypulseq, not at the fork that `sources.yaml` pins;
  the two behave the same here, and the citations give the lines of
  1.5.0.post1, with those of master where they differ.
