---
# expect: checked 'YYYY-MM-DD' is not a date
id: DIS-0927
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
  level: low
  written_by: []
  reason: "no writer writes the condition"
found: 2026-10-09
checked: YYYY-MM-DD
---

# DIS-0927: The number of fields of an [RF] row
