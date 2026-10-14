---
id: DIS-NNNN
title: <the condition in the file>
kind: <spec-contradiction | spec-gap | spec-vs-implementation | implementation-vs-implementation>
severity: <crash | playback | acceptance | round-trip | documentation>
status: draft
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "<one short line>"
  - key: cpp-reader
    behavior: "<one short line>"
report_to:
  - repo: pulseq/pulseq
    component: <specification | C++ reader | MATLAB toolbox>
    issue: null
pulseq_analysis:
  ids: []
  commit: <commit>
found: YYYY-MM-DD
checked: YYYY-MM-DD
---

# DIS-NNNN: <title>

## Summary

<The condition, and how the sources disagree, in two or three sentences.>

## What each source does

| Source | What it does |
|---|---|
| Specification | <with `spec:N` citations> |
| C++ reader | <with `cpp:N` citations> |

## Reproducer

```
<the smallest .seq file or script; or a link to reproducers/DIS-NNNN/>
```

| Source | Expected | Observed (command, date) |
|---|---|---|
| | | |

## Impact

<Who is affected, and how.>

## Suggested resolution

<Optional.>

## Report

<The draft text of the upstream issue, or the links to the issues.>

## History

- YYYY-MM-DD: found.
