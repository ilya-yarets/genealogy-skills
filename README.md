# Genealogy Skills

A family of independent AI agent skills for collecting family testimony,
researching records and reviewing genealogical evidence. Start with one task
or carry a source-linked result from one skill to the next.

**Version 0.3.3 · English instructions · MIT · By Illia Yarats**

[Project repository](https://github.com/ilya-yarets/genealogy-skills) ·
[Release downloads](https://github.com/ilya-yarets/genealogy-skills/releases) ·
[Report an issue](https://github.com/ilya-yarets/genealogy-skills/issues)

This is the initial publication candidate, under review on
[`codex/initial-publication`](https://github.com/ilya-yarets/genealogy-skills/tree/codex/initial-publication).
No tagged release has been issued, and the candidate has not been merged into `main`.

These are instruction folders for an AI agent, not a family-tree application.
You can use any one of them on its own. No private project, database, account,
API key or companion skill is required by the package. Your chosen agent may
require its own account, tools or subscription.

## Find your starting point

| Skill | Use it when you want to… | What you get |
|---|---|---|
| [genealogy-researcher](skills/genealogy-researcher/SKILL.md) | Find a record, investigate an ancestor or plan the next search | Findings with sources, actual search coverage, unresolved questions and a resumption point |
| [family-interview-to-tree](skills/family-interview-to-tree/SKILL.md) | Process a family interview or transcript | Source-linked people and relationship proposals, stories, photo leads, corrections and a mention ledger |
| [genealogy-evidence-review](skills/genealogy-evidence-review/SKILL.md) | Assess a disputed identity, relationship or date | Comparison of evidence, source dependence, contradictions and a bounded conclusion |

Choose by the work you want done now. An interview can produce the question for
a later search; a search can produce candidates for review; a review can identify
the next missing record. These are optional handoffs, not a required sequence.
Each skill keeps its own instructions, references and license and works without
installing the other two.

The methods are region-independent; source selection depends on historical
jurisdiction, language and available access. No regional archive database is included. Instructions
and examples are in English; you may ask for an answer in your preferred language.
Keep source quotations in their original form, with a clearly labeled translation
when useful.

## What makes this a family

The skills share a few commitments:

- **Traceable claims.** Keep source IDs and exact locators with each material
  claim, and distinguish testimony, documents and inference.
- **Preserved uncertainty.** Keep approximate dates, alternative readings,
  source dependence and separate identity candidates visible.
- **Continuity within one case.** Carry supplied IDs, prior results, corrections
  and open questions forward; do not mix different families' case records.
- **Proposals with clear boundaries.** A result can answer a question without
  changing a tree, accepting a relationship or authorizing another action.

They share the optional `genealogy-handoff-1` JSON format. Its complete reference
is included in every skill, so an individual installation has no dependency on
a sibling folder. Markdown remains a supported way to pass a result onward.

## Use the skills together

The [end-to-end example](examples/workflow/README.md) follows one fictional case:

1. **Interview:** preserve a narrator's account, an existing accepted value and
   an unverified lead about a parent.
2. **Research:** examine supplied record extracts, retain a separate namesake
   candidate and plan the next check without pretending to browse.
3. **Evidence review:** assess the candidate against the family account, explain
   the limits of a copied index and leave the accepted tree value unchanged.

For each handoff, give the next skill the actual previous result, the source
material it needs and a specific request with the current access limits. A new
chat does not automatically know an earlier chat's context. When trying the
example, use your own preceding output; the worked JSON files are optional
reference answers. In real work, keep those outputs with your private case.

This collection does not launch the three skills automatically. Installing a
skill does not grant access to a family archive or permission to update a tree.

## Install

For this candidate, download the
[review branch as a ZIP](https://github.com/ilya-yarets/genealogy-skills/archive/refs/heads/codex/initial-publication.zip)
or clone that branch:

```sh
git clone --branch codex/initial-publication --single-branch https://github.com/ilya-yarets/genealogy-skills.git
```

Open the extracted folder or cloned `genealogy-skills` directory. Downloading or
cloning does not install the skills. A locally supplied versioned release ZIP
uses the same `skills/` layout. No downloadable tagged release is available yet;
future releases will appear under
[release downloads](https://github.com/ilya-yarets/genealogy-skills/releases).
Each folder under `skills/` is a complete installable skill. Copy the
**whole selected skill folder**, including `references/`, `agents/` and `LICENSE`.
Do not copy just `SKILL.md` or install the collection's top-level folder as one skill.

Choose one location:

| Agent | Personal installation | Project-only installation |
|---|---|---|
| Codex | `~/.agents/skills/<skill-name>/` | `.agents/skills/<skill-name>/` in your project |
| Claude Code, local sessions | `~/.claude/skills/<skill-name>/` | `.claude/skills/<skill-name>/` in your project |

You can create the destination folder and copy with your file manager. On Windows,
`~` means your user home folder; use your agent's documented location. For a
terminal example on macOS/Linux, run this **from the extracted collection folder**
to install all three for Codex:

```sh
(
  skill_dest="$HOME/.agents/skills"
  for skill in genealogy-researcher family-interview-to-tree genealogy-evidence-review; do
    if [ -e "$skill_dest/$skill" ] || [ -L "$skill_dest/$skill" ]; then
      echo "Existing skill found: $skill. Stop and review it before updating."
      exit 1
    fi
  done
  mkdir -p "$skill_dest"
  for skill in genealogy-researcher family-interview-to-tree genealogy-evidence-review; do
    cp -R "skills/$skill" "$skill_dest/$skill" || exit 1
  done
)
```

For Claude Code, use `skill_dest="$HOME/.claude/skills"` in the same block.
For a project installation, set `skill_dest` to that project's `.agents/skills`
or `.claude/skills` directory. To install only one skill, copy only its folder.
The block stops before copying if any selected destination already exists.
For an update, preserve your customized copy first, then replace the whole
selected folder; overlaying files can leave obsolete references behind.

Start a new agent session after copying. In Codex, select the skill or mention
`$genealogy-researcher`. In Claude Code, use `/genealogy-researcher`. Substitute
the other skill names as needed. Installation locations follow
[OpenAI's documentation](https://learn.chatgpt.com/docs/build-skills) and
[Claude Code's local skills documentation](https://code.claude.com/docs/en/skills),
checked on 2026-11-06. Cloud upload, Cowork and API installation are separate
workflows and are not covered here.

## Your first request

Start with supplied text and a narrow question. For example, in Codex:

```text
Use $genealogy-researcher to plan the next search for my great-grandmother's
parents from the notes below. Use only these notes for now; do not browse.
Explain what record would distinguish the possible families.
```

```text
Use $family-interview-to-tree on this transcript. Keep speakers and corrections
separate, include unnamed relatives, and account for all substantive mentions.
Return proposals only; do not change my tree.
```

```text
Use $genealogy-evidence-review to assess whether these two records describe
the same person. Use only the supplied material. Show evidence for and against,
identify copies of the same source, and preserve my already accepted values.
```

In Claude Code, begin with `/genealogy-researcher`, `/family-interview-to-tree`
or `/genealogy-evidence-review`, followed by the same request. Then paste or
attach the relevant materials. Include existing person/source IDs and prior
results when continuing the same case. State what is off-limits.

For external research, explicitly give the question and permission to search.
The agent needs an available browser or source tool; the skill itself supplies
neither. If access is missing, it should return an honest plan, not claim it
searched. Interviews can start from plain text; audio transcription and image
reading depend on the host's tools.

See [the examples catalog](examples/README.md) for three focused examples and
the complete three-stage workflow. No family data is needed to try them.

## Understand the result

- Markdown is the default. JSON is optional: ask for `genealogy-handoff-1`.
- A working person or relationship is a proposal, not an accepted tree entry.
- Confident oral testimony remains oral testimony; an unavailable scan remains
  unavailable even when its index can be read.
- An unresolved question can be a useful result. The next step should identify
  a record or detail that could distinguish the alternatives.
- Search permission does not authorize correspondence, payments, publication,
  external uploads or tree edits. DNA and genetic-match analysis are excluded.

Keep private research in a separate folder from this distributable package.
Review your agent's data handling before supplying personal material. The skill
provides instructions, not a technical sandbox or a guarantee of source accuracy.

## Optional offline checks

Using the skills does not require Python. The bundled checks require Python 3.10+
with only the standard library. From the extracted **versioned release ZIP**:

```sh
python3 tools/verify_genealogy_package.py
python3 tools/validate_genealogy_handoff.py examples/research/result.json examples/interview/result.json examples/evidence-review/result.json
python3 tools/validate_genealogy_handoff.py examples/workflow/01-interview-result.json examples/workflow/02-research-result.json examples/workflow/03-review-result.json
```

On Windows, use `py -3` instead of `python3` if appropriate for your installation.
The package check verifies its manifest, file set, local links, licenses and
all six example JSON files. The handoff validator can also check your own JSON file. A PASS
checks structure and integrity, not historical truth, model quality or permission
to import. Checksums detect changes; they are not a signed authenticity guarantee.

A **GitHub source checkout** has CI files and editable sources rather than a
frozen release manifest. From its root, run:

```sh
python3 -B tools/check_genealogy_repository.py
python3 -B -m unittest discover -s tests -p test_genealogy_repository.py -v
```

The source checker creates a temporary consumer package, verifies it and removes
the temporary files. It leaves the checkout unchanged. Do not run the strict
release-archive verifier directly on a Git checkout. For a local source export
without Git history, add `--source-commit <full-source-sha>` from its delivery
receipt to the source-check command. See [contribution rules](CONTRIBUTING.md)
for the source/archive distinction and CI limits.

## Compatibility and limits

The folders use the [Agent Skills format](https://agentskills.io/specification).
`agents/openai.yaml` adds Codex UI metadata; the core workflow is in `SKILL.md`
and local references. No host-specific tool name is required by the workflow.

Local packaging and schema checks are recorded in the source project. Earlier
synthetic executions used Russian instructions. Version 0.3.1 also received
three small English explicit-invocation checks and a fresh research recheck
after clarifying coverage target IDs. Versions 0.3.2 and 0.3.3 retain exactly those
runtime instructions. The 0.3.2 end-to-end example is authored teaching material, checked
for structure and continuity; it is not a new multi-agent execution. The initial
structural failure remains in the source project. These limited observations
are not a reliability percentage. Clean installation, automatic skill selection,
Claude runtime behavior, other hosts, live archives and a no-skill comparison
have not been verified for this edition. The installation table describes
supported host conventions, not a claim that those installation tests ran.

If a skill is missing, check that its name folder directly contains `SKILL.md`,
that you copied all references, that the folder is in the active agent's local
skills location, and that another copy does not have the same name. Start a new
session and try explicit invocation. If a source cannot be opened, provide the
text you can access and ask the agent to state the resulting limits.

## Grow the family

The family currently contains these three skills. Improvements should address a
clear user task and preserve standalone use, traceability and existing results.
New skills need a distinct purpose and demonstrated value beyond an existing
skill's reference or example. See [development and contribution rules](CONTRIBUTING.md)
for proposing changes, testing handoffs, keeping the shared format consistent
and preparing a release. Possible extensions are proposals, not availability
or release commitments.

## Version, license and provenance

[Release notes](CHANGELOG.md) describe this edition. In a versioned release ZIP,
`RELEASE.json` binds it to its source commit, and `MANIFEST.sha256` lists every
other delivered file. The GitHub source export omits these generated files;
its checker creates them only in temporary staging from the current source.

The included instructions, code and synthetic examples are under the
[MIT License](LICENSE), copyright 2026 Illia Yarats. Each skill retains its own
license when copied independently. See [notices](THIRD_PARTY_NOTICES.md) for
external references and excluded historical test material.

The original evaluation responses, including failures, remain unchanged in the
source project. The concise English examples are labeled editorial adaptations,
not replacement test answers. This collection excludes the mixed source
repository's Git history, unrelated skills, private files and historical archive
excerpts. Preparing this candidate does not itself publish or install it.
