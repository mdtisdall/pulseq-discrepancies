---
id: DIS-0002
title: A gap that is reported
kind: spec-gap
severity: acceptance
status: reported
format_versions: ["1.4.x", "1.5.x"]
sources:
  - key: cpp-reader
    behavior: "rejects the file"
  - key: fixture-only
    behavior: "accepts the file"
    version: "1.2.3"
report_to:
  - repo: pulseq/pulseq
    component: C++ reader
    issue: https://github.com/pulseq/pulseq/issues/1
  - repo: imr-framework/pypulseq
    component: pypulseq
    issue: null
priority:
  level: high
  written_by: [matlab-pulseq, pypulseq]
  reason: "both writers write the condition, and the C++ reader rejects it"
  fixed:
    by: https://github.com/pulseq/pulseq/pull/1
    last_release: "MATLAB Pulseq v1.5.1"
found: "2026-10-09"
checked: "2026-10-13"
---
