# pulseq-discrepancies

A centralized record of the discrepancies between the definitions, readers,
and writers of the [Pulseq](https://pulseq.github.io/) format: the
specification, the C++ reader of the scanner's interpreter, MATLAB Pulseq, and
pypulseq. The discrepancies were found by
[pulseq-analysis](https://github.com/mdtisdall/pulseq-analysis). Each record is
written so that it can be reported to the maintainers of the affected source.

- [`discrepancies/`](discrepancies/): one file for each discrepancy,
  `DIS-NNNN-<slug>.md`.
- [`docs/record-format.md`](docs/record-format.md): the format of a record, its
  fields, severities, and statuses.
- [`docs/inventory.md`](docs/inventory.md): every finding of pulseq-analysis,
  sorted into records, and the batches that add them.
- [`sources.yaml`](sources.yaml): the sources, each at a pinned version.
- [`templates/discrepancy.md`](templates/discrepancy.md): the template for a
  new record.

## Checks

`scripts/validate_records.py` checks the front matter of each record against
[`docs/record-format.md`](docs/record-format.md). Run all the checks, as CI
does, with:

```
nix develop --command scripts/check
```
