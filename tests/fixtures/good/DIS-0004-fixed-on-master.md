---
id: DIS-0004
title: The number of fields of an [RF] row
kind: spec-contradiction
severity: playback
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "prose: 7 numbers; tables: 12"
report_to:
  - repo: pulseq/pulseq
    component: specification
    issue: null
pulseq_analysis:
  ids: [D1.2]
  commit: 5bd053a
priority:
  level: high
  written_by: []
  reason: "pypulseq 1.5.0.post1 writes the condition; master no longer does"
  fixed:
    by: https://github.com/pulseq/pypulseq/pull/1
    last_release: "pypulseq 1.5.0.post1"
found: 2026-10-09
checked: 2026-10-13
---

# DIS-0004: The number of fields of an [RF] row
