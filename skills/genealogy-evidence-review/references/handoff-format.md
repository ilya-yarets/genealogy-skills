# Result handoff format v1

This optional format supports saving and transferring results between tools.
Ordinary answers can use readable prose and tables. When JSON is requested,
return one object in the shape below; empty lists are allowed. These are
proposals, not tree-write commands. The format performs no import and grants
no permissions.

```json
{
  "schema_version": "genealogy-handoff-1",
  "task": {"kind": "research", "question": "Research question", "status": "unresolved"},
  "sources": [],
  "people": [],
  "claims": [],
  "hypotheses": [],
  "searches": [],
  "coverage": [],
  "next_steps": []
}
```

`task.kind`: `research`, `interview` or `evidence-review`.
`task.status`: `answered`, `unresolved` or `blocked` describes the question,
not permission to change a tree. Successful analysis can yield `unresolved`.

Local IDs (`S1`, `P1`, `C1`, `H1`) stay stable within one case. Reuse supplied
IDs when continuing; namespace collisions between cases. A matching ID does
not establish that two people or sources are the same.

`sources[].notes`, `people[].notes`, `claims[].notes` and `coverage[].reason`
are required in every applicable record, including records inherited from a
previous result. Each must be a string containing a non-whitespace character;
missing fields, `null`, other types, `""` and whitespace-only strings are invalid.
Use `notes` to explain this record's provenance, precision or limitations.
When no separate caveat applies, give the available basis, such as "Reported
by the narrator; not independently checked," only if that fits the material.
Do not invent uncertainty or facts to fill a field, or use empty boilerplate.

## Sources and people

Source:
`{"id":"S1","title":"Title","kind":"document","access":"read","locator":"file or URL","notes":"Provenance and limits"}`.

- `kind`: `document`, `index`, `interview`, `photo`, `tree`, `catalog`, `other`.
- `access`: `read`, `partial`, `metadata-only`, `unavailable`, `not-inspected`.
- For actual external access, add `accessed_at` with the actual access date.
- Supplied text may have been read while the scan it describes is unavailable:
  these are different objects; do not substitute one access state for the other.
- Do not claim to have saved a file, checked a hash or seen an image unless you
  did so. Do not include real secret URLs or access parameters in the report.

Person:
`{"id":"P1","label":"Name or unnamed sister 1","identity":"source-bound","notes":"Basis for this distinct working record"}`.

`identity`: `supplied-person`, `source-bound`, `unnamed-position`.
A candidate record does not establish identity with someone in the tree.
An unnamed position's number is bookkeeping, not birth order.

## Claims

```json
{
  "id": "C1", "person_id": "P1", "predicate": "birth",
  "value": "about 1880", "related_person_id": null,
  "basis": "document", "support": "single-source", "review": "proposed",
  "source_refs": [{"source_id": "S1", "locator": "folio 7, entry 3", "excerpt": "short extract"}],
  "notes": "Approximate date; calendar not established"
}
```

- `value` is a string or object preserving original precision and uncertainty.
  Represent counts as objects, for example `{"count":2,"precision":"exact"}`;
  do not use bare numbers, booleans or `null` as the value.
- `predicate` briefly identifies the claim type; use one event or attribute
  per record. For a relationship, fill `related_person_id` and explain its
  direction in `notes`.
- `basis`: `document`, `oral`, `machine`, `inference`, `calculation`.
- `support`: `unassessed`, `single-source`, `independent-support`, `dependent`,
  `conflicting`. This assesses evidence for this claim, not votes.
- `review` is always `proposed`: the set prepares proposals. Previously accepted
  owner facts may be described in `notes` with the supplied decision basis;
  do not change their status in the source system. Evidence assessment does
  not replace the owner's decision.
- `source_refs` contains at least one precise locator. For a calculation, cite
  its inputs and show the calculation; for a hypothesis, give grounds and a caveat.
- An empty source field does not mean "did not happen." Do not average readings.

## Hypotheses, searches and coverage

Hypothesis:
`{"id":"H1","question":"Whom does the record represent?","candidate_ids":["P1"],"for":["Grounds with C-/S-ID"],"against":["Objection or limitation"],"dependence":"Evidence that is repeated","conclusion":"Current conclusion and limits","resolving_evidence":"What would distinguish alternatives"}`.

Search attempt:
`{"id":"Q1","target":"source or collection","query":"Exact query","scope":"Years, filters, images","outcome":"not-run","origin":"planned","examined":"Material actually read","resume":"Where to continue"}`.

`outcome`: `found`, `no-match-in-scope`, `not-covered`, `access-blocked`,
`error`, `not-run`. Only a performed search gets an outcome other than `not-run`.
For an external performed search, add the actual `searched_at`. When carrying
forward a prior log, use `origin: supplied-log` and preserve its stated date:
this reports a previous search, not a new run. Use `origin: performed-now` for
an actual current lookup and `origin: planned` for a plan.

Coverage row:
`{"item":"S1, 00:40 - account of a sister","disposition":"proposed","target_ids":["P2","C2"],"reason":"What is preserved or missing"}`.

`disposition`: `proposed`, `lead`, `conflict`, `excluded`, `pending`.
`reason` explains the row's status for every disposition: what was transferred
where, which lead or conflict was preserved, why material was excluded, or what
remains unavailable/unprocessed. Having `target_ids` does not replace that explanation.
`target_ids` may refer only to existing source, person, claim or hypothesis IDs,
not search-attempt IDs. Describe a search in `item`/`reason` and link its supplied
source or resulting claim/hypothesis when applicable; use an empty target list
for a lead with no such target. `proposed` and `conflict` must have targets.
`lead` preserves a specific lead. For interviews, `proposed` and `conflict` need at least one person or claim
ID: a source reference alone does not represent a tree proposal. `pending`
honestly marks unprocessed material. Explain exclusions without reproducing
prohibited contents. Saying "everything accounted for" without checkable rows
is not a completeness check.

`next_steps` is a list of specific strings. Distinguish the next useful record
from asking someone to repeat information already supplied. Describe external
actions as proposals unless their execution was separately authorized.

Before returning JSON, check every record, not only the first ones: required
`notes` and `reason` fields exist, are strings, remain nonempty after trimming
and explain the supplied material. Check inherited records too. When adding
an explanation, preserve original IDs, values and correction history. Do not
claim a validator ran unless it actually did.
