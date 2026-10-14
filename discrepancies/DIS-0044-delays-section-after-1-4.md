---
id: DIS-0044
title: "A [DELAYS] section in a file of 1.4.0 or later"
kind: spec-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "removed in 1.4.0; the binary format says that current readers ignore it"
  - key: cpp-reader
    behavior: "reads it, and uses it only for a file before 1.4.0"
  - key: matlab-pulseq
    behavior: "rejects: MUST NOT contain the [DELAYS] section"
  - key: pypulseq
    behavior: "rejects: RuntimeError MUST NOT contain [DELAYS] section"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
priority:
  level: low
  written_by: []
  reason: "No writer writes [DELAYS] in a 1.4+ file. Both toolboxes reject such a file with a deliberate 'MUST NOT contain [DELAYS]' message, and the C++ reader ignores the section."
pulseq_analysis:
  ids: [D09]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0044: A [DELAYS] section in a file of 1.4.0 or later

## Summary

Version 1.4.0 removed the `[DELAYS]` section. The specification says that
"Current readers ignore this section for compatibility with old files", and
the C++ reader does: it reads the section and uses it only for a file before
1.4.0. MATLAB Pulseq and pypulseq reject a file of 1.4.0 or later that has the
section.

## What each source does

| Source | What it does |
|---|---|
| Specification | The table of revisions gives, for 1.4.0, "removed [DELAYS]" (`spec:114`). The binary format lists `[DELAYS]` as "legacy, deprecated" (`spec:743`), and its payload as "Current readers ignore this section for compatibility with old files" (`spec:772`). The text format has no section for it. |
| C++ reader | Reads the rows of `[DELAYS]` (`cpp:1172-1192`) and uses them only to convert the blocks of a file before 1.4.0 (`cpp:1656-1711`): in a later file the section is ignored. |
| MATLAB Pulseq | "Pulseq file revision 1.4.0 and above MUST NOT contain the [DELAYS] section" (`read.m:146-149`). |
| pypulseq | `RuntimeError("Pulseq file revision 1.4.0 and above MUST NOT contain [DELAYS] section")` (`read_seq.py:182-184`). |

## Reproducer

[`reproducers/DIS-0044/delays_section.seq`](../reproducers/DIS-0044/delays_section.seq):
the 1.5.1 file of DIS-0043, with this section after `[ADC]`:

```
# id delay
[DELAYS]
1 100
```

Commands as in DIS-0001.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | The section is ignored (`spec:772`). | — |
| C++ reader | — | Read, each block decoded (exit 0), plain and sanitized. 2026-10-14. |
| MATLAB Pulseq | — | Error "Pulseq file revision 1.4.0 and above MUST NOT contain the [DELAYS] section" (`read.m:148`). 2026-10-14. |
| pypulseq | — | `RuntimeError: Pulseq file revision 1.4.0 and above MUST NOT contain [DELAYS] section` (`read_seq.py:184`). Both versions. 2026-10-14. |

## Impact

Neither writer writes `[DELAYS]` from 1.4.0. A file converted from an old
version that keeps the section, with its version changed, is played by the
scanner's reader and rejected by both toolboxes.

## Suggested resolution

Make the readers agree with the specification, or the specification with the
readers. Either MATLAB Pulseq and pypulseq ignore `[DELAYS]` from 1.4.0 (with
a warning), as `spec:772` says and the C++ reader does; or the specification
says, in the text format, that a file of 1.4.0 or later must not have it, and
the sentence of `spec:772` is limited to files before 1.4.0. The statement of
`spec:772` is in the description of the binary format, so the choice is the
maintainers'.

## Report

Draft, to pulseq/pulseq (MATLAB Pulseq), and the same to pulseq/pypulseq:

> **`read` rejects a `[DELAYS]` section that the specification says readers ignore**
>
> The specification says of `[DELAYS]` (legacy, removed in 1.4.0): "Current
> readers ignore this section for compatibility with old files"
> (`specification.tex:772`), and the C++ reader does. `read` rejects a file of
> 1.4.0 or later with the section ("MUST NOT contain the [DELAYS] section",
> `read.m:146-149`; `read_seq.py:182-184`). Should it ignore it, with a
> warning, or should the specification say that such a file is invalid?
> Reproducer attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D09, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and
  master `c977214`, which agree here.
