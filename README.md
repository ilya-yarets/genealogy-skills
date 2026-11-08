# Genealogy Skills

A family of independent AI agent skills for collecting family testimony,
researching records and reviewing genealogical evidence. Start with one task
or carry a source-linked result from one skill to the next.

**Version 0.3.4 · Prepared locally · English instructions · MIT · By Illia Yarats**

[Project repository](https://github.com/ilya-yarets/genealogy-skills) ·
[Release downloads](https://github.com/ilya-yarets/genealogy-skills/releases) ·
[Report an issue](https://github.com/ilya-yarets/genealogy-skills/issues)

The 0.3.4 skill runtime is pinned to public source commit
[`f095c56`](https://github.com/ilya-yarets/genealogy-skills/commit/f095c56cb78b09a28beb98ee0ac14e054eb7325c).
These prepared archives also include later documentation and packaging work;
their delivery metadata identifies the exact committed source revision. Preparing
them does not create a GitHub tag, release or directory listing.

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
jurisdiction, language and available access. No regional archive database is included. Editorial instructions are in English; synthetic evaluations also preserve original
Russian text. You may ask for an answer in your preferred language.
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

## Install standalone skill folders

This section describes standalone folders. If you received
`genealogy-skills-0.3.4-openai.zip` or `genealogy-skills-0.3.4-anthropic.zip`, use
that archive's README for the plugin route and namespaced commands instead.
The native checks below exercised plugin loading, rather than the standalone
copy commands in this section. Avoid loading both copies of a skill at once.

Download the
[main branch as a ZIP](https://github.com/ilya-yarets/genealogy-skills/archive/refs/heads/main.zip)
or clone the repository:

```sh
git clone --branch main --single-branch https://github.com/ilya-yarets/genealogy-skills.git
```

Open the extracted folder or cloned `genealogy-skills` directory. Downloading or
cloning does not install the skills. A locally supplied versioned release ZIP
uses the same `skills/` layout. Prepared local archives are not downloadable
GitHub releases; published releases, when available, appear under
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
to import. An empty `coverage` list remains valid in v1; a nonempty list also does
not prove completeness against the input. Version 0.3.4 rejects invalid typed
references and missing participants in documented binary relationships. If an old
handoff now fails, correct its source-backed links or preserve an unresolved
kinship mention as a lead; do not invent a participant to obtain PASS. Checksums detect changes; they are not a signed authenticity guarantee.

A **GitHub source checkout** has CI files and editable sources rather than a
frozen release manifest. From its root, run:

```sh
python3 -B tools/check_genealogy_repository.py
python3 -B -m unittest discover -s tests -p 'test_genealogy*.py' -v
python3 -B tools/check_genealogy_evals.py
```

The source checker creates a temporary consumer package, verifies it and removes
the temporary files. It leaves the checkout unchanged. Do not run the strict
release-archive verifier directly on a Git checkout. For a local source export
without Git history, add `--source-commit <full-source-sha>` from its delivery
receipt to the source-check command. See [contribution rules](CONTRIBUTING.md)
for the source/archive distinction and CI limits.

The source checkout also includes the OpenAI/Anthropic plugin builder, verifier,
templates and focused regressions. From a committed Git checkout, the offline
build check creates two builds of each profile, verifies the actual ZIPs and
extractions, and compares runtime files and repeated bytes:

```sh
python3 -B tools/check_genealogy_plugin_builds.py --output-dir ../genealogy-plugin-check-0.3.4
```

Use a new output directory outside the checkout so generated files do not enter
the strict source inventory. This check does not load or install a plugin, call
a model or use the network. See the contribution rules for individual ZIP build
commands. The source templates are not plugin installations.

## Compatibility and limits

The folders use the [Agent Skills format](https://agentskills.io/specification).
`agents/openai.yaml` adds Codex UI metadata; the core workflow is in `SKILL.md`
and local references. No host-specific tool name is required by the workflow.

Version 0.3.4 includes a focused participant-attribution rule and
[eight paired synthetic cases](evals/README.md), with first-output copies,
declared path-only redactions, separate rubrics and recorded limitations. Earlier
Russian-instruction and small English explicit-invocation checks remain
historical evidence. The three-stage example is authored teaching material,
checked for structure and continuity; it is not a new multi-agent execution.
Original failures remain preserved rather than replaced by reference answers.

Separate native checks on 2026-11-06 used the unchanged 0.3.4 runtime in isolated
profiles and external workspaces, with synthetic supplied text and no live
archive access:

| Client and tested route | Native loading | Explicit model calls |
|---|---|---|
| Codex CLI 0.166.0, temporary local marketplace and plugin installation | Exactly three plugin skills in the test catalog | Three first responses completed; all JSONs validate and all 21 independent content/scope criteria pass |
| Claude Code 2.1.206, session-only `--plugin-dir` | All three plugin skills and slash commands registered | Not verified: the attempted call stopped at authentication; the test account lacked an eligible subscription |

Codex was configured for `gpt-6.1-sol` with low reasoning effort; its event JSON
did not independently report the server-side model identity. The interview call
warned that inline instructions were truncated, then successfully read the full
installed `SKILL.md` and both references before answering. The research and
review calls had no such warning and read both references. First responses were
preserved without repair or retry. These observations apply to three bounded
cases, not a reliability percentage or proof of historical accuracy.

This packaging work updates documentation and build/verification support; it does
not repeat native installation or model calls. Its runtime remains byte-identical
to the tested core. Automatic skill selection, ChatGPT GUI/Cowork, other hosts,
live research and improvement over the same model without skills remain
unverified. The standalone installation table describes host conventions, not
an execution result for the copy commands.

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

The new synthetic first-output copies (with declared local-path redactions) and
imported unchanged known failure are preserved
in [evals](evals/README.md). Earlier evaluation responses, including failures, remain unchanged in the
source project. The concise English examples are labeled editorial adaptations,
not replacement test answers. This collection excludes the mixed source
repository's Git history, unrelated skills, private files and historical archive
excerpts. Preparing these archives does not itself publish or install them.
