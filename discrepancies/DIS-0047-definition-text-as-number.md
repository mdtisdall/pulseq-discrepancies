---
id: DIS-0047
title: A definition whose text reads as a number
kind: spec-vs-implementation
severity: round-trip
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "<value> has the type any"
  - key: cpp-reader
    behavior: "keeps the text of each definition, and its numbers"
  - key: matlab-pulseq
    behavior: "holds a value that reads as a finite number as a double; writes it with %.9g"
  - key: pypulseq
    behavior: "holds a value that reads as a float as a float; writes it with {:0.9g}"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: MATLAB toolbox
    issue: null
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq, pypulseq]
  reason: "Both writers write a text definition such as ProtocolID 007. The C++ reader keeps the text; MATLAB Pulseq and pypulseq read it as the number 7 and write 7 back."
pulseq_analysis:
  ids: [D2.7, D7.1]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0047: A definition whose text reads as a number

## Summary

The value of a definition has the type "any". MATLAB Pulseq and pypulseq hold
a value that reads as a number as a number, and write it back with 9
significant digits, so a read and a write change the text of the file:
`ProtocolID 007` becomes `7`, `ToolVersion 1.10` becomes `1.1`, and
`SeriesUID 12345678901234567890` becomes `1.23456789e+19`. The C++ reader keeps
the text. Both toolboxes write the changed text, so the value that the
scanner's reader gets from the rewritten file is not the one of the original.

## What each source does

| Source | What it does |
|---|---|
| Specification | `<key> <value>`, where `<value>` has the type "any" (section 2.5, `spec:238`, `spec:247`); "The `<value>` field is separated by a single space or tab character from `<key>` and is terminated at the end of the line" (`spec:251`). |
| C++ reader | Keeps the text of each value (`cpp:1430-1432`), and the numbers that it reads from it (`cpp:1437-1445`). |
| MATLAB Pulseq | Reads the tokens of each value with `str2double`, and keeps the text only when one is not finite (`read.m:462-466`). Writes a value that is not text with `'%.9g '` (`write.m:46-50`). |
| pypulseq | Holds the value as floats when every token reads as one (`read_seq.py:464-472`). Writes a float with `'{:0.9g} '` (`write_seq.py:68-77`). |

## Reproducer

[`reproducers/DIS-0047/`](../reproducers/DIS-0047/):
`definitions_number.seq`, a 1.5.1 file whose `[DEFINITIONS]` has, after the
four rasters,

```
ProtocolID 007
SeriesUID 12345678901234567890
ToolVersion 1.10
```

and `roundtrip.py` and `roundtrip.m`, which read the file, write it again and
print the `[DEFINITIONS]` that were written. The scripts ran with pypulseq
1.5.0.post1 and master `c977214`, and with MATLAB Pulseq of `c7469123` under
GNU Octave 11.3.0; the file was read by the readers as in DIS-0001, and the C++
dump (`pulseq-cpp-oracle --dump`) gives the definitions that the reader holds.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | The value is the text, so a read and a write keep `007`, `12345678901234567890` and `1.10`. | — |
| C++ reader | — | Read (exit 0); the dump has the text `007`, `12345678901234567890` and `1.10`. 2026-10-14. |
| MATLAB Pulseq | — | `roundtrip.m`: `ProtocolID 7`, `SeriesUID 1.23456789e+19`, `ToolVersion 1.1`. 2026-10-14. |
| pypulseq | — | `roundtrip.py`: `ProtocolID 7`, `SeriesUID 1.23456789e+19`, `ToolVersion 1.1` (both versions). 2026-10-14. |

## Impact

A script that sets a definition as text (`setDefinition('ProtocolID',
'007')`) writes the text; the change happens when a file is read and written
again by a toolbox, for example to add blocks, to convert it, or to remove
duplicates. Identifiers, version strings and long numbers lose digits, and
the scanner's reader then sees the changed value. The rasters and the other
definitions that are numbers are not affected beyond the 9 digits.

## Suggested resolution

MATLAB Pulseq and pypulseq: keep the text of each definition as it was read
(as the C++ reader does), and give the numbers of the reserved definitions
(the rasters, `FOV`, `TotalDuration`) where they are used; or write a value
that was read as text from the text that was read.

## Report

Draft, to pulseq/pulseq (MATLAB Pulseq), and the same to pulseq/pypulseq:

> **A read and a write change the text of a definition that reads as a number**
>
> The specification gives the value of a definition the type "any". `read`
> holds a value that reads as a number as a `double` (`read.m:462-466`;
> `read_seq.py:464-472`), and `write` writes it with 9 significant digits
> (`write.m:49`; `write_seq.py:71`). So a read and a write change
> `ProtocolID 007` to `7`, `ToolVersion 1.10` to `1.1` and
> `SeriesUID 12345678901234567890` to `1.23456789e+19`. The C++ reader keeps
> the text. Could `read` keep the text of each definition? Reproducer
> attached.

## History

- 2026-10-09: found by pulseq-analysis (old ID D13, commit `49a7e2c`; D2.7 and
  D7.1 at `5bd053a`).
- 2026-10-14: confirmed against the pinned sources; the file and the scripts
  run in the C++ reader, MATLAB Pulseq and pypulseq 1.5.0.post1 and master
  `c977214`, which agree here. The inventory also gave this record the
  `[SIGNATURE]` hash that reads as a number (drafts 09a and 09b of
  `mdtisdall/pypulseq-issues`, and F-TODO-11). That case is left out: both
  toolboxes hold the hash as a number in memory (`read.m:86-91`,
  `read_seq.py:94-100`), but neither checks it against the file nor writes it
  back (`write` computes a new hash), so no file and no other source is
  affected: it is the state of an object in memory, which is not a record
  (`docs/record-format.md`, section 1). The title drops the hash.
