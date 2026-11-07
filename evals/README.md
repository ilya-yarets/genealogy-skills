# Reproducible synthetic evaluations

This directory contains eight small interview cases and two first-output copy
sets with declared path-only redactions, alongside separate assessor rubrics and run identities. Every person and
record is invented. These files are distinct from the six editorial JSON examples.

## Repeat an execution

1. Choose one input in `cases/` and one standalone skill folder. Read its `SKILL.md`
   and the references it requests. Give the executor the case input only; keep
   `rubrics/`, previous outputs and assessments out of its context.
2. Use supplied material only, with no network, real tree, contacts or other case
   files. Save the first JSON response unchanged. Do not validate and repair it
   before preserving the original delivery.
3. After execution, use the handoff validator for structure and assess the source
   against the separate rubric. Record actual client/model/tools, input/runtime
   hashes, output hash and deviations. A new result gets a new run identity;
   do not replace the saved first response.

`RUNS.json` pins all eight input/output/rubric triples per variant. Original first
deliveries remain private and unchanged because executors included local absolute
input paths. Public copies remove only that local release-root prefix. Each run
records original/public hashes, the transform and occurrence count; no semantic
repair was made. Blind assessors reviewed the unchanged private deliveries. Baseline runtime
bytes match the public 0.3.3 source at
[1efd6839](https://github.com/ilya-yarets/genealogy-skills/tree/1efd6839e07076660799df3f8168a82b3f2cb8eb/skills/family-interview-to-tree).
Candidate runtime hashes match this package's standalone interview skill. The
baseline can be obtained at that pinned revision; its hashes remain in the index.
The optional handoff contract stays v1; these run IDs describe experiments, not a
new required case-store schema.

## What the offline checker establishes

```sh
python3 -B tools/check_genealogy_evals.py
```

Run from the package/source root. The checker verifies case/variant inventories,
exact bytes, runtime identity for the candidate, preserved structural outcomes and
the binding of each recorded assessment to its input, output and rubric. It does
not grade source interpretation, infer completeness from a nonempty ledger or
establish that a model was executed merely because metadata claims it.
The package manifest additionally covers every shipped evaluation file.

`ASSESSMENT.json` records separate source-based judgments. Failures and partial
results stay visible. A structural PASS can coexist with a semantic failure; the
imported Appendix C demonstrates this exact limit.

## Observed results

| Saved set | Structural check | Blind source-based review |
|---|---|---|
| Baseline 0.3.3, eight short cases | 8 valid | 8 pass |
| Candidate 0.3.4, same eight cases | 8 valid | 8 pass |
| Imported Appendix C | Valid structure | Known cousin-attribution failure |

The short baseline cases did **not** reproduce the historical failure. There is
no observed quality gain to claim from this pair of small sets. The candidate
makes the participant boundary explicit and passes its positive control. A minor
candidate observation remains visible: the correctly named third child retains
its earlier `unnamed-position` identity label. No output was repaired to remove it.
See `ASSESSMENT.json` for case-specific reasons, frozen hashes and limits.

## Historical known failure

`history/appendix-c.initial.json` is imported unchanged from the owner's supplied
independent review dated 2026-11-06, with a matched original SHA-256 and byte count.
Its `cousin_of(P9,Nina)` attribution is too definite for the supplied wording.
The historical execution was not repeated here or repaired. Its provided task
context is reconstructed, with transcript lines verbatim according to the review;
client/model details were not recorded. See `history/provenance.json` for limits.

## Execution conditions and limitations

The paired sets use two fresh executor contexts, one per runtime, each receiving
all eight cases separately in the same context. Those are sixteen saved responses (public copies remove only local path prefixes),
not sixteen independent model contexts. Executors receive no rubrics or prior
outputs, do not validate/repair deliveries, and have no network authorization.
One candidate-executor delegation attempt was rejected by the concurrency limit;
no additional executor was created. The exact provider model/client version is unavailable; do not treat this as a
pinned-model benchmark. Separate blind assessors receive inputs, rubrics and
anonymized first outputs, without runtime instructions or variant identities.

These short explicit-invocation observations do not establish statistical
reliability, superiority to an agent without a skill, automatic discovery,
installation, live archive access, all languages or real-tree mutation fidelity.
Keeping the same test inputs does not eliminate model nondeterminism or effects
of the shared per-variant context. The source and byte hashes make the evidence
inspectable; they do not turn a limited observation into universal support.
