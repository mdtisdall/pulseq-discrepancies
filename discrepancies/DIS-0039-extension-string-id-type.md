---
id: DIS-0039
title: An extension header whose STRING_ID is a word (table against examples)
kind: spec-contradiction
severity: documentation
status: confirmed
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: spec
    behavior: "the table gives the type of <STRING_ID> as integer; the description and every example give a word"
  - key: cpp-reader
    behavior: "reads STRING_ID as text"
  - key: matlab-pulseq
    behavior: "reads and writes STRING_ID as text"
  - key: pypulseq
    behavior: "reads and writes STRING_ID as text"
    version: "1.5.0.post1 and master c977214"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
pulseq_analysis:
  ids: [D1.4]
  commit: 5bd053a
found: 2026-10-08
checked: 2026-10-14
---

# DIS-0039: An extension header whose STRING_ID is a word (table against examples)

## Summary

The header of an extension section is `extension <STRING_ID> <type>`. The
table of section 2.8.4 gives the type of `<STRING_ID>` as "integer", but its
own description calls it a text ID, the interpreter must recognize an extension
only by it, and every example has a word (`extension TRIGGERS 1`). The C++
reader and both toolboxes read and write a word. Only the table is wrong.

## What each source does

| Source | What it does |
|---|---|
| Specification | The header is `extension <STRING_ID> <type>` (section 2.8.4, `spec:483`). The table gives `<STRING_ID>` the type "integer", with the description "text ID of the present extension used by the interpreter to recognize the extension" (`spec:493`). "The interpreters MUST only use the `STRING_ID` to recognize the extensions" (`spec:498`). Each example has a word: `extension TRIGGERS 1` (`spec:507`), `extension DELAYS 2` (`spec:553`), `extension ROTATIONS 1` (`spec:574`), `extension RF_SHIMS 4` (`spec:591`); `RequiredExtensions` lists them by these words (`spec:460`). |
| C++ reader | Reads the header with `sscanf("extension %s %d")` and compares the text with the names that it knows (`cpp:1228-1244`). |
| MATLAB Pulseq | Compares the text after `extension ` with the names that it knows (`read.m:156-189`); writes a word (`write.m:166`, `write.m:183`, `write.m:195`, `write.m:210`, `write.m:223`, `write.m:237`). |
| pypulseq | Compares the text of the header with the names that it knows (`read_seq.py:191-228`); writes a word (`write_seq.py:191`, `write_seq.py:204`, `write_seq.py:219`, `write_seq.py:234`). |

## Reproducer

[`reproducers/DIS-0039/extension_word.seq`](../reproducers/DIS-0039/extension_word.seq):
one RF block pulse with a trigger, in a `TRIGGERS` section:

```
[EXTENSIONS]
1 1 1 0

extension TRIGGERS 1
1 1 2 0 10
```

Commands as in DIS-0001.

| Source | Expected | Observed (command, date) |
|---|---|---|
| Specification | By the description and the examples: valid. By the table: `TRIGGERS` is not an integer. | — |
| C++ reader | — | Read, each block decoded (exit 0), plain and sanitized. 2026-10-14. |
| MATLAB Pulseq | — | Read; `getBlock` and `waveforms_and_times` succeed. 2026-10-14. |
| pypulseq | — | Read; `get_block` and `waveforms_and_times` succeed, in both versions. 2026-10-14. |

## Impact

None between the implementations, which agree. The table misleads a person
who writes a reader from the specification.

## Suggested resolution

Give the type of `<STRING_ID>` as "text" in the table of section 2.8.4.

## Report

Item 4 of the issue of DIS-0038 (draft 13 of `mdtisdall/pypulseq-issues`),
which reports both records together.

## History

- 2026-10-08: found (item 4 of draft 13 of `mdtisdall/pypulseq-issues`,
  commit `1de4a1d`); also D55 of pulseq-analysis (commit `49a7e2c`), D1.4 at
  `5bd053a`.
- 2026-10-14: confirmed against the pinned sources; reproducer run in the C++
  reader (plain and sanitized), MATLAB Pulseq and pypulseq 1.5.0.post1 and
  master `c977214`, which agree here.
