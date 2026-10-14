---
id: DIS-0043
title: A section that the format does not have
kind: spec-gap
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "lists its sections; no rule for another"
  - key: cpp-reader
    behavior: "reads only the sections that it knows; ignores another"
  - key: matlab-pulseq
    behavior: "rejects: Unknown section code"
  - key: pypulseq
    behavior: "rejects: ValueError Unknown section code"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
pulseq_analysis:
  ids: [D2.4]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0043: A section that the format does not have

## Summary

The specification lists the sections of a file and has no rule for a section
of another name, for example `[FOO]`. The C++ reader seeks to each section that
it knows by name, so it ignores another; MATLAB Pulseq and pypulseq read the
sections in order and reject the file at the unknown header. For extensions,
the specification has a rule (detect, and may ignore), but not for sections.

## What each source does

| Source | What it does |
|---|---|
| Specification | Gives the sections `[VERSION]`, `[SIGNATURE]`, `[DEFINITIONS]`, `[BLOCKS]`, the event sections and `[SHAPES]` (sections 2.3 to 2.9, `spec:189-626`). No rule for another section. For an unknown extension: "The interpreter MUST detect unknown extensions and MAY chose to ignore them" (`spec:460`). |
| C++ reader | Indexes every line that starts with `[` (`cpp:1762-1769`), then seeks to the sections that it knows by name (for example `cpp:873`, `cpp:998`, `cpp:1546`): a section of another name is never read. |
| MATLAB Pulseq | Reads the headers in file order (`read.m:50-55`); a header that is not a section that it knows, nor `extension …`, gives "Unknown section code" (`read.m:192`). |
| pypulseq | The same: `ValueError("Unknown section code: …")` (`read_seq.py:228`). |

## Reproducer

[`reproducers/DIS-0043/section_unknown.seq`](../reproducers/DIS-0043/section_unknown.seq):
a 1.5.1 file of one RF block pulse and one block of a trapezoid and an ADC,
with this section after `[ADC]`:

```
[FOO]
1 2 3
```

Commands as in DIS-0001.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent. | — |
| C++ reader | — | Read, each block decoded (exit 0), plain and sanitized. 2026-10-14. |
| MATLAB Pulseq | — | Error "Unknown section code: [FOO]" (`read.m:192`). 2026-10-14. |
| pypulseq | — | `ValueError: Unknown section code: [FOO]` (`read_seq.py:228`). Both versions. 2026-10-14. |

## Impact

Neither writer writes another section. A file from another tool with a section
of its own (for example metadata) is played by the scanner's reader and
rejected by both toolboxes, so it cannot be checked or plotted with them.

## Suggested resolution

The specification: say whether a reader rejects or ignores a section that it
does not know, as it does for extensions in section 2.8.4.

## Report

Draft, to pulseq/pulseq:

> **Specification: a section that the format does not have**
>
> The specification has a rule for an unknown extension (section 2.8.4: detect
> it, and it may be ignored) but not for an unknown section, such as `[FOO]`.
> The C++ reader ignores it (it reads only the sections that it knows, by
> name); MATLAB Pulseq stops with "Unknown section code" (`read.m:192`), and
> so does pypulseq. Could the specification say which is meant?

## History

- 2026-10-09: found by pulseq-analysis (old ID D08, commit `49a7e2c`; D2.4 at
  `5bd053a`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and
  master `c977214`, which agree here. `report_to` is the specification only
  (the inventory also had MATLAB Pulseq and pypulseq): until it decides, there
  is no rule for the toolboxes to follow.
