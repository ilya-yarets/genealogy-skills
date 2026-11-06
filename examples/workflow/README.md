# One case through the Genealogy Skills family

This is a complete, authored teaching example for fictional case **GS-DEMO-01**.
It is not a recorded agent run, real family research or evidence of an automatic
multi-agent workflow. All people, records and reported searches are invented.
The JSON files are editorial reference results; original evaluation responses
elsewhere in the source project remain unchanged.

The question evolves from an interview into a record lead and then a decision:
can a candidate birth entry be assigned to Mara Vale and replace her accepted
birth year? The useful final result is a bounded answer with the identity still
unresolved. No tree is changed.

## Before you start

Use the relevant skill's instructions for each step. The example uses Codex's
`$skill-name` notation; in Claude Code use `/skill-name` with the same request.
Other hosts may require their own invocation method. There is no need to install
all three just to read this walkthrough. All source material is text provided
here; no browser, archive account, private data or special application is needed.

For an actual trial, give the agent the input and appropriate skill first. Keep
these reference answers out of its context until you want to compare results.
Save or copy your actual output for the next step. If files cannot be attached,
paste the request, relevant source text and previous result into the chat.
Different wording or newly assigned local IDs is acceptable if identity and
source mappings remain consistent.

## Step 1: preserve the interview

**Skill:** [family-interview-to-tree](../../skills/family-interview-to-tree/SKILL.md).
**Give it:** [Step 1 input](01-interview-input.md), containing the supplied person
IDs, accepted-value snapshot and three labeled utterances.

```text
Use $family-interview-to-tree to carry out the request in the attached Step 1
input. Work only with those materials. Return a brief explanation and
one genealogy-handoff-1 JSON object. Do not browse or change a tree.
```

**Worked outcome:** Nora's family account says Mara was born about 1880 in
Northmere and her mother was called Elin. Tomas is only a name reportedly found
in an unseen online tree. The snapshot's accepted year 1880 is recorded as an
existing decision, not established historical truth. Four working people and
five claims preserve the mentions without inventing an intermediate parent,
reading the online tree or confirming Tomas as Mara's father.

[Step 1 JSON](01-interview-result.json) contains seven coverage rows. Its
`task.status: unresolved` reflects the remaining family question; it does not
mean that the supplied transcript was left unprocessed.

**Pass onward:** your actual Step 1 result and the original Step 1 input. Include
both: a summary alone may lose the source wording or distinction between a
reported tree entry and a document actually read.

## Step 2: investigate the supplied record lead

**Skill:** [genealogy-researcher](../../skills/genealogy-researcher/SKILL.md).
**Give it:** the preceding output, [Step 1 input](01-interview-input.md) and
[Step 2 input](02-research-input.md). The new input supplies a register
transcription, a dependent index and an earlier search-log extract.

```text
Use $genealogy-researcher to continue GS-DEMO-01 from the attached interview
result and source inputs. Investigate the supplied record lead, preserve
existing IDs and identify the next distinguishing check. Return updated
genealogy-handoff-1 JSON. Use supplied text only; do not browse or edit a tree.
```

**Worked outcome:** a register transcription describes a Mara Vale born in 1879,
with parents Elin Voss and Tomas Vale and a household address. The example keeps
this person as GS-P5, separate from the family subject GS-P1. The new parent
records also remain separate from the earlier Elin and Tomas mentions. Similar
names are reasons to investigate, not permission to merge people.

The index explicitly copies the register, so it adds no independent witness.
The original scan is unavailable. A supplied log records an earlier index search;
the example preserves its date and unread-page boundary as `origin: supplied-log`.
A proposed check of the original is `origin: planned`, `outcome: not-run`, with
no invented execution date. No external search occurs in this walkthrough.

[Step 2 JSON](02-research-result.json) retains every Step 1 source, person, claim
and coverage row. It adds the candidate's records and GS-H1, an unresolved
identity hypothesis. This is a cumulative snapshot, not a file to concatenate
with Step 1: concatenation would duplicate IDs.

**Pass onward:** your actual Step 2 result, the original Step 1 and Step 2 inputs,
and the Step 3 review request. In real research, also pass the records actually
obtained and the search log; never substitute this fictional example for evidence.

## Step 3: assess the proposed change

**Skill:** [genealogy-evidence-review](../../skills/genealogy-evidence-review/SKILL.md).
**Give it:** the cumulative result and source inputs above, plus
[Step 3 input](03-review-input.md). No additional evidence arrives in this step.

```text
Use $genealogy-evidence-review to carry out the Step 3 request using the
attached prior result and source inputs. Explain whether identification and
replacing the accepted year are justified. Keep existing evidence and owner
acceptance unchanged. Return a brief explanation and updated handoff JSON.
```

**Worked outcome:** the material does not establish that GS-P5 is GS-P1 and does
not justify replacing the accepted year yet. The name, approximate period and
mother's given name support a possible match, but no independent record ties
GS-P1 to the candidate's parents or address. The index repeats the same source,
and the online tree's origin remains unknown. Keeping 1880 in the source tree
is not a claim that 1880 has been historically verified.

[Step 3 JSON](03-review-result.json) keeps all prior evidence and adds GS-H2,
a review of the proposed change. `task.status: answered` means the review can
answer **whether the proposed change is justified now**. The actual identity
and birth year remain unresolved; no claim becomes accepted automatically.
The next useful evidence is a record independently tied to GS-P1 naming parents
or an address, compared with the original entry-7 image.

## Trace the same objects across all three steps

| Object | Step 1 | Step 2 | Step 3 |
|---|---|---|---|
| GS-P1, family subject | Supplied Mara Vale ID | Retained; distinct from GS-P5 | Still distinct; no identity merge |
| GS-C2, family birth account | About 1880, Northmere | Original claim retained | Original precision and attribution retained |
| GS-C5 / GS-S2, accepted year | Snapshot says 1880, accepted | Snapshot unchanged | No replacement or acceptance change |
| GS-S3 / GS-C4, online-tree lead | Unseen, unknown provenance | Not treated as independent support | Remains a lead |
| GS-P5 / GS-C6, record subject | Not yet supplied | Candidate born 3 May 1879 | Date remains attached to the candidate |
| GS-S4 and GS-S5 | Not yet supplied | Transcription plus copied index | One underlying record, not two witnesses |
| GS-Q1 / GS-Q2, searches | No searches | Inherited log plus future plan | Same provenance; no new execution |
| GS-H1, identity question | No candidate yet | Unresolved | Still unresolved despite answered review question |

## Check and compare

From the extracted collection root:

```sh
python3 tools/validate_genealogy_handoff.py examples/workflow/01-interview-result.json examples/workflow/02-research-result.json examples/workflow/03-review-result.json
```

The handoff validator checks structure. Source-based review must also check the
meaning: no unsupported merge, no promoted precision, no false independent
corroboration, no claimed access to the missing scan and no permission inferred
from `answered`. The maintainer's example tests check preservation of records
and separation of the family subject and candidate across these specific files.
They do not establish that a model will always reproduce the example.

For a new case, use its own IDs, sources and permissions. For a continuation,
reuse that case's supplied IDs and explain any revision with its evidence; do
not silently overwrite earlier claims. These example snapshots preserve prior
records exactly for clarity, but real corrections can require an explicitly
recorded revision. See [development rules](../../CONTRIBUTING.md).
