---
# expect: sources[0] has unknown field 'commit'
id: DIS-0914
title: The number of fields of an [RF] row
kind: spec-contradiction
severity: playback
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "prose: 7 numbers; tables: 12"
    commit: abc1234
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
checked: 2026-10-13
---

# DIS-0914: The number of fields of an [RF] row
