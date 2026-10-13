# pulseq-discrepancies

A centralized record of the discrepancies between the definitions, readers,
and writers of the [Pulseq](https://pulseq.github.io/) format: the
specification, the C++ reader of the scanner's interpreter, MATLAB Pulseq, and
pypulseq. The discrepancies were found by
[pulseq-analysis](https://github.com/mdtisdall/pulseq-analysis). Each record is
written so that it can be reported to the maintainers of the affected source.

- [`discrepancies/`](discrepancies/): one file for each discrepancy,
  `PQD-NNNN-<slug>.md`.
- [`docs/record-format.md`](docs/record-format.md): the format of a record, its
  fields, severities, and statuses.
- [`sources.yaml`](sources.yaml): the sources, each at a pinned version.
- [`templates/discrepancy.md`](templates/discrepancy.md): the template for a
  new record.
