---
id: DIS-0064
title: "[EXTENSIONS] as the last section"
kind: spec-gap
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "silent on the order of the sections"
  - key: cpp-reader
    behavior: "rejects the file: 'failed find the end of the section while reading EXTENSIONS'"
  - key: matlab-pulseq
    behavior: "reads the file"
  - key: pypulseq
    behavior: "reads the file"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
  - repo: pulseq/pulseq
    component: C++ reader
    issue: null
pulseq_analysis:
  ids: [D2.3]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0064: [EXTENSIONS] as the last section

## Summary

The specification does not set an order of the sections. A file whose last
section header is `[EXTENSIONS]` (it has no `[SHAPES]` and no `[SIGNATURE]`
after it, only its `extension` sections) is read by MATLAB Pulseq and
pypulseq, and rejected by the C++ reader: the reader finds the end of
`[EXTENSIONS]` at the next section header, and there is none.

## What each source does

| Source | What it does |
|---|---|
| Specification | Silent on the order of the sections. `[SIGNATURE]` is optional (section 2.4), and a file with no arbitrary shape needs no `[SHAPES]`. |
| C++ reader | Reads `[EXTENSIONS]` up to the next section header of its index, and rejects the file when there is none: "failed find the end of the section while reading EXTENSIONS" (`cpp:1203-1210`). The index has only the lines that start with `[` (`cpp:1762-1769`), so the `extension …` sections after `[EXTENSIONS]` do not end it. |
| MATLAB Pulseq | Reads the file (run). |
| pypulseq | Reads the file (run). |

## Reproducer

Two 1.5.1 files in [`reproducers/DIS-0064/`](../reproducers/DIS-0064/), each
of one trapezoid block with a trigger:

- `extensions_last.seq`: no `[SHAPES]` and no `[SIGNATURE]`; the file ends
  with the extension sections and a blank line:

  ```
  [EXTENSIONS]
  1 1 1 0

  extension TRIGGERS 1
  1 1 2 0 10

  ```

- `extensions_then_signature.seq`: the same with a `[SIGNATURE]` section at
  the end (the control).

Commands as in DIS-0057.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent; nothing makes the file invalid. | — |
| C++ reader | — | `extensions_last.seq`: "ERROR: failed find the end of the section while reading EXTENSIONS", `load` returned false (exit 1; sanitized exit 1). Control: read (exit 0). 2026-10-14. |
| MATLAB Pulseq | — | Both read. 2026-10-14. |
| pypulseq | — | Both read. 2026-10-14. |

Without the blank line at the end of `extensions_last.seq`, pypulseq fails too
(`AttributeError: 'int' object has no attribute 'strip'`, `read_seq.py:813`;
`:821` on master): that is DIS-0016, the last section with no blank line after
it.

## Impact

Both writers write `[EXTENSIONS]` before `[SHAPES]` and `[SIGNATURE]`; they
write `[SHAPES]` only when there is a shape, and `[SIGNATURE]` unless the
caller turns it off (`write.m:153`, `write.m:248-250`, `write.m:263`;
`write_seq.py:181`, `write_seq.py:243-245`, `write_seq.py:256`). So their
files end with `[EXTENSIONS]` when they have extensions, no shape, and no
signature. Such a file loads in both toolboxes and is
refused by the scanner's reader, for a reason that is not a rule of the
format.

## Suggested resolution

The C++ reader: take the end of the file as the end of `[EXTENSIONS]` when no
section header follows it. Or the specification sets an order of the sections
(for example that `[EXTENSIONS]` is not last), and the toolboxes check it.

## Report

Draft, to pulseq/pulseq:

> **`[EXTENSIONS]` as the last section is rejected**
>
> A file with no `[SHAPES]` and no `[SIGNATURE]`, whose last section header is
> `[EXTENSIONS]`, is rejected by `ExternalSequence::load`: "failed find the
> end of the section while reading EXTENSIONS" (`ExternalSequence.cpp:1203-1210`).
> The reader looks for the next `[` header, and the `extension …` sections do
> not count. The specification sets no order of the sections, and MATLAB
> Pulseq and pypulseq read the file. Could the reader take the end of the
> file as the end of the section, or the specification set an order?
> Reproducer attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D46, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here). The
  reproducer ends with a blank line, so that pypulseq's failure on a last
  section with no blank line (DIS-0016) does not hide its result.
