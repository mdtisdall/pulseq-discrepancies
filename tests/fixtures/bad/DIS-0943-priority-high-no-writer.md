---
# expect: priority.level is high, but priority.written_by is empty
id: DIS-0943
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
  reason: "no writer writes the condition"
found: 2026-10-09
checked: 2026-10-13
---

# DIS-0943: The number of fields of an [RF] row
