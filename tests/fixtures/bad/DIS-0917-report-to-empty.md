---
# expect: report_to is not a non-empty list
id: DIS-0917
title: The number of fields of an [RF] row
kind: spec-contradiction
severity: playback
status: confirmed
format_versions: ["1.5.x"]
sources:
  - key: spec
    behavior: "prose: 7 numbers; tables: 12"
report_to: []
pulseq_analysis:
  ids: [D1.2]
  commit: 5bd053a
found: 2026-10-09
checked: 2026-10-13
---

# DIS-0917: The number of fields of an [RF] row
