# Worked examples

These are small, authored English teaching examples, not unedited model outputs
or evidence of a new benchmark run. People and records are fictional. Each
focused example below contains the input, an editorial Markdown result and a structurally
validated JSON proposal. The JSON files are data, not executable tree imports.

For a complete sequence, start with the [family workflow](workflow/README.md):
one fictional case moves from interview to supplied-record research to evidence
review. It shows exactly which result and source inputs to pass onward, how IDs
and original claims survive, and why an answered review does not change a tree.
Its three cumulative JSON files are new editorial examples, not repaired test
outputs or a new agent execution. The focused examples below remain unchanged.

| Task | Input | Worked result | JSON |
|---|---|---|---|
| Plan the next search without inventing access | [Research](research/input.md) | [Report](research/result.md) | [Handoff](research/result.json) |
| Preserve an interview's meaning and limits | [Interview excerpt](interview/input.md) | [Report](interview/result.md) | [Handoff](interview/result.json) |
| Review a conflict without overwriting acceptance | [Evidence review](evidence-review/input.md) | [Report](evidence-review/result.md) | [Handoff](evidence-review/result.json) |

The interview example corrects two observations from an earlier synthetic run:
`FAM-C150` now records notebook possession/provenance without inventing its
compiler; `FAM-C199` no longer claims that acquaintances saw the children in
photographs. Its selected utterance and claim IDs retain their historical
mapping. It is a focused adaptation, not a repaired or complete replay of the
long interview. [Provenance](provenance.json) identifies the unchanged originals
by repository-relative path and SHA-256. Those original responses remain in the
source project's evaluation archive and are deliberately not part of this
English runtime distribution.

To try a case, give your agent only its input and the selected skill. Read the
worked result afterward. Wording can differ; compare source attribution,
uncertainty, coverage, search provenance and permission boundaries. A schema
PASS establishes structure, not genealogical truth or complete extraction.
