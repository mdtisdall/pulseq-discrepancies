---
id: DIS-0038
title: The number of fields of an [RF], [GRADIENTS] or [ADC] row (prose against tables and examples)
kind: spec-contradiction
severity: documentation
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "prose: 7, 4 and 6 numbers, and an [RF] line of 8 fields; tables and examples: 12, 7 and 9 fields"
  - key: cpp-reader
    behavior: "reads 12, 7 and 9 fields, in the order of the tables"
  - key: matlab-pulseq
    behavior: "reads and writes 12, 7 and 9 fields, in the order of the tables"
  - key: pypulseq
    behavior: "reads and writes 12, 7 and 9 fields, in the order of the tables"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
priority:
  level: low
  written_by: [matlab-pulseq, pypulseq]
  reason: "Only the spec's prose is wrong. Both writers write rows of 12, 7 and 9 fields as the tables give, and every reader reads them the same way."
pulseq_analysis:
  ids: [D1.2]
  commit: 5bd053a
found: 2026-10-08
checked: 2026-10-14
---

# DIS-0038: The number of fields of an [RF], [GRADIENTS] or [ADC] row (prose against tables and examples)

## Summary

Sections 2.8.1 to 2.8.3 of the specification give the layout of an event row
three ways: a sentence with a number of fields, a line with the names of the
fields, and a table; each section also has an example. For `[RF]`, the
sentence says 7 numbers, the line has 8 fields in another order, and the table
and the example have 12. For `[GRADIENTS]` and `[ADC]`, the sentence says 4 and
6, while the line, the table and the example have 7 and 9. The C++ reader and
both toolboxes follow the tables and the examples, so only the prose is wrong;
but a reader written from the `[RF]` line would read the RF center as the
delay.

## What each source does

| Source | What it does |
|---|---|
| Specification | `[RF]` (section 2.8.1): "a single line containing seven numbers" (`spec:334`), and the line `<id> <amp> <mag_id> <phase_id> <time_id> <delay> <freq> <phase>`, of 8 fields (`spec:336`). The table has 12 fields, with `<center>` before `<delay>`, and `<freq_ppm>`, `<phase_ppm>` and `<use>`; it names the offsets `<freq_off>` and `<phase_off>` (`spec:341-359`). The example rows have 12 fields (`spec:367-368`), and the text under them reads the first row by the table: center 1000 µs, delay 100 µs (`spec:372`). `[GRADIENTS]` (section 2.8.2): "specified by four numbers" (`spec:375`); the line, the table and the example have 7 fields (`spec:377`, `spec:386-401`, `spec:410-413`). `[ADC]` (section 2.8.3): "specified by six numbers" (`spec:424`); the line, the table and the example have 9 fields (`spec:426`, `spec:431-445`, `spec:453`). `[TRAP]` ("six numbers", `spec:379-381`) and `[EXTENSIONS]` ("four numbers", `spec:462-464`) agree with their lines. |
| C++ reader | In a 1.5 file, reads 12 values of an `[RF]` row, with the center before the delay (`cpp:1042-1048`), 7 of a `[GRADIENTS]` row (`cpp:1073`) and 9 of an `[ADC]` row (`cpp:1148-1149`). |
| MATLAB Pulseq | Reads 12, 7 and 9 values in a 1.5 file (`read.m:120`, `read.m:130`, `read.m:140`), and writes 12, 7 and 9 fields (`write.m:86`, `write.m:102-104`, `write.m:131`). |
| pypulseq | Reads 12, 7 and 9 values in a 1.5 file (`read_seq.py:147-151`, `read_seq.py:163`, `read_seq.py:172-177`), and writes 12, 7 and 9 fields (`write_seq.py:111`, `write_seq.py:134`, `write_seq.py:169`). |

## Reproducer

[`reproducers/DIS-0038/rows_of_the_tables.seq`](../reproducers/DIS-0038/rows_of_the_tables.seq):
a 1.5.1 file with one row of each section, as the tables give them:

```
[RF]
1 1000 1 2 0 50 0 0 0 0 0 e

[GRADIENTS]
2 100000 0 0 3 0 0

[ADC]
1 8 25000 100 0 0 0 0 0
```

Commands as in DIS-0001 (C++ reader plain and sanitized of pulseq-analysis
`65fc7e8`; MATLAB Pulseq under Octave 11.3.0; pypulseq 1.5.0.post1 and master
`c977214`).

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | By the tables and the examples: valid. By the prose: rows of 7 (or 8), 4 and 6 numbers, so not valid. | — |
| C++ reader | — | Read, each block decoded (exit 0), plain and sanitized. 2026-10-14. |
| MATLAB Pulseq | — | Read; `getBlock` and `waveforms_and_times` succeed. 2026-10-14. |
| pypulseq | — | Read; `get_block` and `waveforms_and_times` succeed, in both versions. 2026-10-14. |

## Impact

No file changes meaning between the implementations: they agree with the
tables and the examples. The prose misleads a person who writes a reader or a
writer from the specification. The `[RF]` line is the one with an effect on
values: read by it, the example row `1 550 1 2 0 1000 100 …` has a delay of
1000 µs and a frequency offset of 100 Hz, where the table gives a center at
1000 µs and a delay of 100 µs.

## Suggested resolution

In sections 2.8.1 to 2.8.3, give the number of fields of the line (12, 7 and
9), or remove the number and refer to the line; make the `[RF]` line the 12
fields of the table, in its order; and use one name for the offsets in the line
and the table.

## Report

Draft, to pulseq/pulseq. It is draft 13 of `mdtisdall/pypulseq-issues`, which
also has DIS-0039 (item 4) and a slip of the text that changes no file (item
5). The five items go in one issue.

> **Specification: the prose of five sections disagrees with their tables and examples**
>
> The specification (`doc/specification.tex` at `c7469123`, version 1.5.3,
> draft) gives the layout of each event section as a sentence with the number
> of fields, a line with the names of the fields, and a table, with an example.
> In five places the prose disagrees with the table and the example. The tables
> and the examples agree with each other and with the files that MATLAB Pulseq
> writes, so only the prose is wrong.
>
> 1. RF (section 2.8.1): "a single line containing seven numbers", and the line
>    `<id> <amp> <mag_id> <phase_id> <time_id> <delay> <freq> <phase>` (8
>    fields). The table has 12 fields, with `<center>` before `<delay>`, and
>    `<freq_ppm>`, `<phase_ppm>` and `<use>`; the example has 12. Read with the
>    line, the example row `1 550 1 2 0 1000 100 …` has a delay of 1000 µs; the
>    text under it gives a center at 1000 µs and a delay of 100 µs.
> 2. Gradients (section 2.8.2): "specified by four numbers"; the line, the
>    table and the example have 7 fields.
> 3. ADC (section 2.8.3): "specified by six numbers"; the line, the table and
>    the example have 9 fields.
> 4. The extension header (section 2.8.4): the table gives the type of
>    `<STRING_ID>` as "integer"; the description calls it a text ID, and every
>    example has a word (`extension TRIGGERS 1`). The type is text.
> 5. Soft delay extension (section 2.8.4): the second paragraph starts "Label
>    extension can be used in conjunction with pure delay blocks"; it is about
>    the soft delay extension.
>
> Suggested change: the correct count in items 1 to 3 (or no count, and a
> reference to the line); the 12 fields of the table in the line of item 1;
> "text" as the type of `<STRING_ID>`; "Soft delay extension" in item 5.

## History

- 2026-10-08: found (draft 13 of `mdtisdall/pypulseq-issues`, commit
  `1de4a1d`); the same finding is D01a, D01b and D01c of pulseq-analysis
  (commit `49a7e2c`), D1.2 at `5bd053a`.
- 2026-10-14: confirmed against the pinned sources (`spec:334-453`, the
  readers and the writers); reproducer run in the C++ reader (plain and
  sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and master `c977214`,
  which agree here. The slip of item 5 (`spec:545`) is in the report but is
  not a condition of a file, so it is not a record of its own.
