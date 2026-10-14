---
id: DIS-0065
title: An extension that a reader does not know, and that the file requires
kind: spec-vs-implementation
severity: acceptance
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "from 1.5.1: the interpreter must generate an error and must not execute the sequence"
  - key: cpp-reader
    behavior: "rejects the file"
  - key: matlab-pulseq
    behavior: "does not read RequiredExtensions: reads and plays the file"
  - key: pypulseq
    behavior: "does not read RequiredExtensions: reads the file when it has no section of the extension"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
pulseq_analysis:
  ids: [D47]
  commit: 49a7e2c
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0065: An extension that a reader does not know, and that the file requires

## Summary

From format 1.5.1 a file can list the extensions that it needs in the
definition `RequiredExtensions`; an interpreter that does not know one of them
must generate an error and must not execute the sequence. The C++ reader does
so. MATLAB Pulseq and pypulseq do not read `RequiredExtensions`: MATLAB
Pulseq reads and plays such a file, ignoring the extension, and pypulseq reads
it when the file has no section of that extension.

## What each source does

| Source | What it does |
|---|---|
| Specification | "Since the format revision v1.5.1 there is a concept of required extensions … All extensions listed under the definition `RequiredExtensions` must be supported by the interpreter. If any of the declared required extensions are unknown to the interpreter, it MUST generate an error and MUST not attempt executing the sequence." (section 2.8.4, `spec:460`) |
| C++ reader | From 1.5.1, checks each name in `RequiredExtensions` against the extensions that it knows, and rejects the file: "The extension 'FOO' is unknown to this interpreter but is defined as REQUIRED in the sequence file" (`cpp:1505-1538`). |
| MATLAB Pulseq | `read.m` does not read `RequiredExtensions`; only `write.m` (`write.m:31-36`) and `writeBinary.m` use it. It warns and skips the unknown extension (`read.m:186-189`). |
| pypulseq | No code of `read` uses `RequiredExtensions`. An unknown `extension` section is rejected for its own sake (DIS-0063), so a file with a section of the required extension is rejected, and one without it is read. |

## Reproducer

Two 1.5.1 files in [`reproducers/DIS-0065/`](../reproducers/DIS-0065/), each
of one trapezoid block, with `RequiredExtensions FOO`:

- `required_unknown.seq`: the block refers to an extension `FOO`, defined in
  `extension FOO 1`;
- `required_unknown_unused.seq`: no extension section and no reference;
  only the definition.

```
[DEFINITIONS]
AdcRasterTime 1e-07
BlockDurationRaster 1e-05
GradientRasterTime 1e-05
RadiofrequencyRasterTime 1e-06
RequiredExtensions FOO
```

Commands as in DIS-0057.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | An error for both files. | — |
| C++ reader | — | Both: "ERROR: The extension 'FOO' is unknown to this interpreter but is defined as REQUIRED in the sequence file", `load` returned false (exit 1; sanitized exit 1). 2026-10-14. |
| MATLAB Pulseq | — | Both read and played; `required_unknown.seq` with "Ignoring unknown extension, input string: FOO 1". 2026-10-14. |
| pypulseq | — | `required_unknown.seq`: `ValueError: Unknown section code: extension FOO 1` (`read_seq.py:228`). `required_unknown_unused.seq`: read. 2026-10-14. |

## Impact

`RequiredExtensions` marks the extensions without which the sequence is not
what its author meant. MATLAB Pulseq and pypulseq play such a file without
the extension and without an error, so a user who checks the sequence in a
toolbox sees a sequence that the scanner refuses, and that differs from what
the author meant.

## Suggested resolution

MATLAB Pulseq and pypulseq: read `RequiredExtensions` from 1.5.1, and reject
(or at least warn about) a file that requires an extension that they do not
implement, as the C++ reader does.

## Report

Draft, to pulseq/pulseq (MATLAB Pulseq) and pulseq/pypulseq:

> **`RequiredExtensions` is not checked by `read`**
>
> Section 2.8.4 says that, from 1.5.1, an interpreter that does not know a
> required extension "MUST generate an error and MUST not attempt executing
> the sequence", and `ExternalSequence` rejects such a file. MATLAB's
> `read.m` does not read `RequiredExtensions` (only `write.m` uses it), and
> plays a file with `RequiredExtensions FOO`, ignoring `FOO`. pypulseq's
> `read` does not read it either. Could `read` reject a file that requires
> an extension that the toolbox does not implement? Reproducers attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D47, commit `49a7e2c`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq, and pypulseq 1.5.0.post1 and
  master `c977214` of pulseq/pypulseq (the two behave the same here). The
  second file, with no section of the extension, is new: it separates
  pypulseq's missing check of `RequiredExtensions` from its rejection of an
  unknown section (DIS-0063).
