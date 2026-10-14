---
id: DIS-0073
title: pypulseq's make_arbitrary_grad(oversampling=True) accepts a slew rate 4 times too high
kind: implementation-vs-implementation
severity: acceptance
status: withdrawn
format_versions: ["1.5.x"]
sources:
  - key: matlab-pulseq
    behavior: "makeArbitraryGrad rejects the gradient (slew rate violation, 350 %)"
  - key: pypulseq
    version: "1.5.0.post1"
    behavior: "make_arbitrary_grad accepts it (checks the slew over 2 rasters, not half a raster)"
  - key: pypulseq
    version: "master c977214"
    behavior: "make_arbitrary_grad rejects it (fixed by pulseq/pypulseq#422)"
report_to:
  - repo: pulseq/pypulseq
    component: pypulseq
    issue: null
found: 2026-09-24
checked: 2026-10-14
---

# DIS-0073: pypulseq's make_arbitrary_grad(oversampling=True) accepts a slew rate 4 times too high

## Summary

Withdrawn: not a discrepancy about a file. With `oversampling=True`,
`make_arbitrary_grad` of pypulseq 1.5.0.post1 divides the sample differences
by twice the gradient raster instead of half of it, so it accepts a gradient
up to 4 times the slew limit, which MATLAB Pulseq's `makeArbitraryGrad`
rejects. That is a check of a function's input against the limits of a
system, which are not part of the file: no reader and no part of the
specification checks a slew rate, so the file that pypulseq writes from such a
gradient is read the same by every source. It is fixed on master by
pulseq/pypulseq#422.

## What each source does

| Source | What it does |
|---|---|
| MATLAB Pulseq | `slew=[(first-g(1)); (g(2:end)-g(1:end-1)); (last-g(end))]./system.gradRasterTime*2` (`makeArbitraryGrad.m:71`): the differences over half a raster. |
| pypulseq 1.5.0.post1 | `edge_scale = system.grad_raster_time * 2` with oversampling (`make_arbitrary_grad.py:96`), and `slew_rate = … / edge_scale` (`make_arbitrary_grad.py:104`): the differences over two rasters, a quarter of the slew. |
| pypulseq master | `edge_scale = system.grad_raster_time / 2` (`make_arbitrary_grad.py:96`), since pulseq/pypulseq#422 (commit `892a12b`, 2026-10-09). |

## Reproducer

[`reproducers/DIS-0073/slew_check.py`](../reproducers/DIS-0073/slew_check.py),
from draft P01 of mdtisdall/pypulseq-issues: an oversampled triangle of 17
samples whose every segment is at 350 % of `max_slew` = 100 T/m/s. The MATLAB
call is the one of the draft, under Octave 11.3.0.

| Source | Expected | Observed (command, date) |
|---|---|---|
| MATLAB Pulseq | — | `error: Slew rate violation (350%)`. 2026-10-14. |
| pypulseq 1.5.0.post1 | — | `350 %: accepted`. 2026-10-14. |
| pypulseq master `c977214` | — | `350 %: Slew rate violation 349.99999999999994`. 2026-10-14. |

## Impact

None between the sources about a file. The defect let pypulseq 1.5.0.post1
users build gradients beyond the slew limit of their system; it is fixed on
master.

## Suggested resolution

Not applicable (withdrawn; fixed upstream by pulseq/pypulseq#422).

## Report

Not reported here: withdrawn. The fix, pulseq/pypulseq#422, came from draft
P01.

## History

- 2026-09-24: drafted as an issue in mdtisdall/pypulseq-issues (draft P01).
- 2026-10-09: fixed on pypulseq master by pulseq/pypulseq#422 (`892a12b`).
- 2026-10-14: run on pypulseq 1.5.0.post1 and master `c977214`, and on MATLAB
  Pulseq. Withdrawn under the scope rule of the migration: a record is a
  disagreement between sources about a file, and this is a check of the input
  of a function that makes an event, against the limits of a system that are
  not in the file.
