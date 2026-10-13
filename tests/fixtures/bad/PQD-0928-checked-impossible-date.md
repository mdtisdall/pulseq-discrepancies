---
# expect: checked '2026-02-30' is not a date
id: PQD-0928
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
found: 2026-10-09
checked: "2026-02-30"
---

# PQD-0928: The number of fields of an [RF] row
