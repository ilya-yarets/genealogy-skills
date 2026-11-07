# Release notes

## 0.3.4 — Reference validation and reproducible synthetic evaluations (candidate)

- Explicit person/source reference checks for documented immediate `claim.value`
  fields; documented binary kinship predicates require a second person.
- Clarified omitted relationship participants, with an explicit-possessive positive
  control. Unresolved mentions remain usable leads; no participant is invented.
- Removed the Cyrillic heuristic. Original spellings and quotations are preserved;
  privacy-pattern, file-set, checksum, symlink and link gates remain independent.
- Eight paired synthetic inputs, separate rubrics, first-response copies with declared path-only redactions and
  run metadata, plus the review's original known-failure output and provenance.
- Public reference/evidence regression tests and CI; editorial examples and prior
  evaluation outputs remain unchanged.

The schema stays `genealogy-handoff-1`. Invalid typed references and missing binary
participants previously tolerated by the validator now fail. Unknown predicates,
free text and arbitrary nested extension objects retain their existing semantics.
Do not invent a relative to make an old handoff pass. This is a prepared candidate,
not a published release or proof of general accuracy or host compatibility.

## 0.3.3 — Public source and hosted CI

- Public source at `ilya-yarets/genealogy-skills`, integrated through reviewed
  PR #1. No tagged release was issued as part of that integration.
- A clean source export with pinned, read-only GitHub Actions checks for Linux,
  macOS and Windows; no publishing, installation or merge automation.
- Repository checks stage a temporary consumer package. The release ZIP keeps
  its exact manifest and excludes Git metadata and repository-only CI files.
- Regression coverage for source/export boundaries and self-contained checks.

All runtime instructions, contracts, six authored JSON examples and original
evaluation responses are unchanged. Previous archives are preserved. Local
verification is separate from hosted checks. PR #1 and its main commit passed
all three configured platforms; those checks establish package structure, not
agent installation or genealogical accuracy.

## 0.3.2 — Genealogy Skills family candidate

- A family README with task selection, common principles and explicit handoffs
  between the three independently usable skills.
- A complete synthetic interview -> research -> evidence-review walkthrough,
  with three cumulative JSON examples retaining IDs, original evidence, search
  provenance, unresolved identity and the owner's accepted value.
- Development and contribution rules covering new-skill proposals, shared
  contracts, preserved evaluations, versioning and release boundaries.
- Export and integrity checks include the new documentation and all six JSON
  examples. The previous 0.3.1 archive and all historical responses are preserved.

Runtime instructions, skill names, licenses, shared contracts and the handoff
validator are unchanged from 0.3.1. The schema remains `genealogy-handoff-1`.
The new workflow is authored teaching material, not a new model benchmark or
evidence of automatic orchestration. This is a local prepared candidate.

## 0.3.1 — English distribution candidate

- English entrypoints, shared references and Codex UI descriptions for all three
  skills. The existing task, access, provenance and proposal boundaries are retained.
- A collection README with installation, first-use prompts, requirements,
  troubleshooting and explicit compatibility limits.
- Three small English worked examples and an optional offline handoff validator.
- Corrected interview demonstrations: notebook compiler remains unknown, and the
  acquaintances' viewing medium is unspecified. Original test responses are unchanged.
- A deterministic, allowlisted ZIP with source revision and file checksums.
- Explicit coverage-target guidance matching the unchanged validator: search
  attempt IDs are not valid `coverage.target_ids`.
- MIT licensing with the owner-confirmed name Illia Yarats.

The optional JSON schema remains `genealogy-handoff-1`; the validator's previous
notes/reason and accessed_at fixes are retained. This edition follows the local
0.3 integration and subsequent contract corrections. It is a prepared candidate;
no public release, installation or main-branch merge is implied.
