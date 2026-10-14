---
id: DIS-0049
title: A byte that is not UTF-8
kind: spec-gap
severity: acceptance
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "gives no encoding of the file"
  - key: cpp-reader
    behavior: "does not check the encoding; reads the file"
  - key: matlab-pulseq
    behavior: "reads the file (under Octave)"
  - key: pypulseq
    behavior: "opens the file in the encoding of the locale; under UTF-8, UnicodeDecodeError"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq, pypulseq]
  reason: "Both writers write definition text in the system encoding, so a Latin-1/cp1252 system writes a non-UTF-8 byte. pypulseq's read under UTF-8 fails with UnicodeDecodeError."
pulseq_analysis:
  ids: [D3.1]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-14
---

# DIS-0049: A byte that is not UTF-8

## Summary

The specification gives no encoding of a `.seq` file. A file with a byte that
is not valid UTF-8, for example the micro sign 0xB5 of Latin-1 in a comment,
is read by the C++ reader and by MATLAB Pulseq under Octave. pypulseq opens the
file in the encoding of the locale (UTF-8 in Python's UTF-8 mode), so under
UTF-8 it fails with `UnicodeDecodeError`, and under an encoding such as Latin-1
or Windows-1252 it would read the file.

## What each source does

| Source | What it does |
|---|---|
| Specification | Silent: no encoding. The text that it describes is ASCII: keys, numbers, and the text of a definition (`spec:238-251`). |
| C++ reader | Reads bytes, and compares only ASCII characters (for example `cpp:1762`, `cpp:1219`); it does not check the encoding. |
| MATLAB Pulseq | Opens the file with `fopen(filename)` and no encoding (`read.m:23`), so the bytes are read in the default encoding of MATLAB or Octave. |
| pypulseq | Opens the file with `open(path, 'r')` and no encoding (`read_seq.py:43`), the encoding of the locale; a byte that does not decode raises `UnicodeDecodeError` when the line is read (`read_seq.py:754`; `:762` on master). |

## Reproducer

[`reproducers/DIS-0049/non_utf8_comment.seq`](../reproducers/DIS-0049/non_utf8_comment.seq):
a 1.5.1 file of one RF block pulse and one block of a trapezoid and an ADC,
whose comment line above `[TRAP]` ends with `(µs)`, the µ as the byte 0xB5
(Latin-1). The signature is the MD5 of the bytes.

Commands as in DIS-0001; pypulseq under Python 3.14.7, which ran in its UTF-8
mode (the C locale, with `LANG` unset), so `open` decoded UTF-8.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | Silent. | — |
| C++ reader | — | Read, each block decoded, signature verified (exit 0). Plain and sanitized. 2026-10-14. |
| MATLAB Pulseq | — | Read; `getBlock` and `waveforms_and_times` succeed (GNU Octave 11.3.0). 2026-10-14. |
| pypulseq | — | `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb5 in position 396` (`read_seq.py:754`; `:762` on master). Both versions. 2026-10-14. |

## Impact

The fixed text of both writers is ASCII. The text of a definition, and the
hint of a soft delay, are the script's, and are written as they are: pypulseq
opens the file for writing in the encoding of the locale (`write_seq.py:52`, with `newline='\n'` on master),
and MATLAB Pulseq with no encoding (`write.m:17`). So a definition with a
non-ASCII character, written on a system whose encoding is not UTF-8, gives a
file that pypulseq cannot read under a UTF-8 locale, while the scanner's reader
reads it. Whether the same file is read by pypulseq depends on the machine.

## Suggested resolution

The specification: give the encoding of a file (ASCII, or UTF-8), and say
whether the signature hashes the bytes of the file. The readers and the writers
can then open the file in that encoding, not in the one of the system.

## Report

Draft, to pulseq/pulseq:

> **Specification: the encoding of a `.seq` file**
>
> The specification gives no encoding. A file with a byte that is not UTF-8
> (for example µ as 0xB5 in a comment or a definition) is read by the C++
> reader and by MATLAB Pulseq, and by pypulseq only when the locale is not
> UTF-8: `read` opens the file in the encoding of the locale and raises
> `UnicodeDecodeError` under a UTF-8 locale. The writers also write the text of
> a definition in the encoding of the system. Could the specification give the
> encoding (ASCII or UTF-8)?

## History

- 2026-10-09: found by pulseq-analysis (old ID D14, commit `49a7e2c`; D3.1 at
  `5bd053a`).
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and
  master `c977214`, which agree here. Correction: pulseq-analysis gave a
  failure of MATLAB Pulseq "in `regexp`". That failure comes from the dump
  of its oracle (`strsplit` of the file in `dump.m`, after `read`), not from
  MATLAB Pulseq: `read`, `getBlock` and `waveforms_and_times` of MATLAB Pulseq
  succeed on the file. MATLAB itself (not Octave), and pypulseq under a locale
  that is not UTF-8, were not run. `report_to` is the specification only (the
  inventory also had the C++ reader and MATLAB Pulseq, which read the file).
