# The discrepancy record format

This document defines how this repository records a discrepancy. Each record
is one Markdown file with YAML front matter. The front matter holds the fields
that tools and summaries use. The body holds the explanation, the evidence, and
the text of the report.

## 1. What a record is

A record describes one disagreement between two sources of the Pulseq format,
documents or implementations, that a maintainer can act on: the sources
disagree on what a file means, whether a file is valid, what is written for
the same input, or what is played. A record is one of these kinds (`kind`):

| `kind` | Meaning |
|---|---|
| `spec-contradiction` | The specification (or its slide set) contradicts itself, for example its prose against its tables. |
| `spec-gap` | The specification is silent or only recommends, and the implementations do different things. |
| `spec-vs-implementation` | The specification states a rule, and an implementation does not follow it. |
| `implementation-vs-implementation` | Two implementations disagree where the specification does not decide, and the record does not ask the specification to decide. |

A defect of one implementation is a record only when it makes that
implementation disagree with another source about a file. For example, a crash
of the C++ reader on a file that the specification allows, or that a writer
writes, is `spec-vs-implementation` or `implementation-vs-implementation`, with
`severity: crash`. A defect with no such disagreement (performance, the state
of an object in memory, the return value of an API) is not a record.

One record names one condition in a file, for example "an `[RF]` row of 12
fields". When a condition gives a separate issue to each of two maintainers,
it is still one record, with one entry in `report_to` for each maintainer.

A choice of pulseq-analysis's own interpreter `spec` is not a discrepancy of
this repository. A record can use pulseq-analysis as evidence, but it states
what the upstream sources do.

## 2. Layout

| Path | Contents |
|---|---|
| `discrepancies/PQD-NNNN-<slug>.md` | One record. |
| `reproducers/PQD-NNNN/` | Optional. Files of a reproducer that are too long to put in the record. |
| `sources.yaml` | The sources that records compare, each at a pinned version. |
| `templates/discrepancy.md` | The template for a new record. |

The ID is `PQD-` and four digits, given in order. An ID is never reused or
renumbered. A record that turns out to be wrong or a duplicate stays, with
`status: withdrawn` or `status: duplicate`. The slug is short kebab-case and
can change. Links use the ID.

Add each new record on its own branch, in its own PR. The exception is the
migration of the findings of pulseq-analysis (`docs/inventory.md`): there, one
branch and one PR add one batch of records, with the IDs that the inventory
reserved.

## 3. The sources

`sources.yaml` lists each source with a key, its repository, the pinned
commit or version, and how a record cites it. A record refers to a source by
its key. When a record was checked at a different version, its entry in
`sources` gives `version`.

A citation gives the file and the line at the pinned version:

| Source key | Cited as |
|---|---|
| `spec` | `spec:N`, line N of `doc/specification.tex`, with the section number of the PDF |
| `spec-slides` | "slide N" of `doc/pulseq_shapes_and_times.pdf` |
| `cpp-reader` | `cpp:N` (`src/ExternalSequence.cpp`), `cpp.h:N` (`src/ExternalSequence.h`) |
| `matlab-pulseq` | `<file>.m:N`, for example `write.m:86` |
| `pypulseq` | `<file>.py:N`, for example `write_seq.py:111` |

## 4. The front matter

```yaml
id: PQD-0001
title: The number of fields of an [RF], [GRADIENTS] or [ADC] row
kind: spec-contradiction
severity: playback
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "prose: 7, 4 and 6 numbers; tables and examples: 12, 7 and 9"
  - key: cpp-reader
    behavior: "reads 12, 7 and 9"
  - key: matlab-pulseq
    behavior: "writes 12, 7 and 9"
  - key: pypulseq
    behavior: "writes 12, 7 and 9"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
pulseq_analysis:
  ids: [D1.2]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-13
```

| Field | Required | Contents |
|---|---|---|
| `id` | yes | `PQD-NNNN`. Equal to the file name's prefix. |
| `title` | yes | The condition in the file, in a few words. |
| `kind` | yes | One value of section 1. |
| `severity` | yes | One value of section 5. |
| `status` | yes | One value of section 6. |
| `format_versions` | yes | The Pulseq format versions that the condition applies to, for example `["1.4.x", "1.5.x"]`. |
| `sources` | yes | Each source that the record compares: `key` (from `sources.yaml`), `behavior` (one short line), and optional `version` when the source was checked at a version other than the pin. At least two entries, or one for `spec-contradiction`. |
| `report_to` | yes | Each maintainer to report to: `repo` (`owner/name`), `component` (for example `specification`, `C++ reader`, `MATLAB toolbox`), and `issue` (the URL of the upstream issue or PR, or `null`). |
| `pulseq_analysis` | no | `ids`: the IDs of `docs/discrepancies.md` of pulseq-analysis, and `commit`: the commit of pulseq-analysis that has those IDs. pulseq-analysis renumbers its IDs, so the commit is required with the IDs. |
| `found` | yes | The date that the discrepancy was found. |
| `checked` | yes | The date that the statements of the record were last checked against the sources. |
| `duplicate_of` | with `status: duplicate` | The ID of the record that this one duplicates. |

## 5. Severity

The highest value that applies:

| `severity` | Meaning |
|---|---|
| `crash` | An implementation crashes, hangs, or reads memory that it does not own. |
| `playback` | The same file gives different waveforms or timing in different implementations, or different from the specification. |
| `acceptance` | One implementation accepts a file that another rejects, and both play the same waveforms when they read it. |
| `round-trip` | A file written by one tool does not read back the same in another tool, or in the same tool. |
| `documentation` | Only the text of the specification or the documentation is affected. |

## 6. Status

```
draft -> confirmed -> reported -> acknowledged -> resolved
                                              \-> wontfix
any -> duplicate | withdrawn
```

| `status` | Meaning |
|---|---|
| `draft` | The record is being written, or its evidence is not complete. |
| `confirmed` | Each statement of the record is checked against the pinned sources, and the reproducer runs. Ready to report. |
| `reported` | An issue or PR exists upstream. Each `report_to` entry that is reported has its `issue` URL. |
| `acknowledged` | A maintainer has accepted that it is a problem. |
| `resolved` | Fixed upstream. The body gives the fixing commit or release. |
| `wontfix` | A maintainer declined it. The body gives the reason. |
| `duplicate` | Another record covers it (`duplicate_of`). |
| `withdrawn` | It is not a discrepancy. The body gives the reason. |

## 7. The body

Use these sections, in this order. `templates/discrepancy.md` has them.

1. **Summary.** Two or three sentences: the condition, and how the sources
   disagree.
2. **What each source does.** A table with one row for each source in
   `sources`: what it does, with citations (section 3).
3. **Reproducer.** The smallest file or script that shows the discrepancy,
   inline in a code block or in `reproducers/PQD-NNNN/`. For each source: what
   the specification says should happen, and what was observed, with the
   command that ran it and the date.
4. **Impact.** Who is affected, and how: which files, which scanners, which
   tools.
5. **Suggested resolution.** Optional. What would remove the discrepancy, for
   example the text to change in the specification.
6. **Report.** The draft text of the upstream issue, or the links to the
   issues once they exist.
7. **History.** Dated lines: found, confirmed, reported, maintainer replies,
   resolved.
