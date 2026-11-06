# Developing Genealogy Skills

Genealogy Skills is a family of independently usable skills for family-history
work. Changes should help a specific task while preserving source attribution,
case boundaries and user control. The current family contains three skills;
there is no required coordinator or automatic workflow engine.

## Propose a focused change

Describe the task, current behavior, desired result and a small reproducible
example. Use invented people and records where possible. A useful report says
which skill and package version were used, which host/tools were available,
what was actually read and what remained unavailable. Remove private data and
access-bearing links before sharing. Keep any original response unchanged in
private evidence storage; label a redacted public copy and record what changed.

The repository is [ilya-yarets/genealogy-skills](https://github.com/ilya-yarets/genealogy-skills).
Use [issues](https://github.com/ilya-yarets/genealogy-skills/issues)
for a reproducible problem or proposal, and
[pull requests](https://github.com/ilya-yarets/genealogy-skills/pulls) for a focused change.
The initial candidate is on `codex/initial-publication`; `main` contains only an
empty bootstrap commit until separately approved integration. Base proposed
candidate fixes on that review branch. No tagged release has been issued.
Do not include private family records or unredacted responses.

## Decide where a change belongs

| Change | Preferred home |
|---|---|
| Correction to an existing task's decisions or behavior | That skill's instructions, with evidence for the correction |
| Regional source guidance or an additional worked case | A focused reference or example for the existing skill |
| Shared handoff or case-context rule | Canonical contract, then all three skill-local copies together |
| Distinct recurring task with different inputs and outputs | A new-skill proposal, reviewed before implementation |
| Host-specific setup or metadata | A host adapter or installation guidance, keeping the core workflow portable |

A new-skill proposal should give its trigger, input, output, exclusions and the
reason an existing skill cannot handle the task cleanly. Include a realistic
example and a way to judge success. Potential directions such as record
transcription, interview preparation or sourced family narratives are ideas to
validate, not implemented skills or promised releases.

Keep the existing skill IDs stable. Prefer a descriptive `genealogy-...` name
for new family members when it accurately describes the task; a new naming
preference is not a reason to rename published skills. A folder name must match
its `SKILL.md` name. Explain renames, file-path changes and migration effects
before releasing them.

## Preserve the family contract

- Each skill must work from its own folder. Include the references, scripts and
  license it actually needs; do not require a sibling skill, private application
  or unpublished family archive.
- Keep shared contract text synchronized. In the maintainer source, `contracts/`
  is authoritative; update its skill-local copies and run the bundle check.
  Do not introduce cross-folder runtime links to avoid copying a shared reference.
- Preserve same-case IDs, source locators, original precision, corrections and
  evidence dependence. A same-name candidate is not automatically the same person.
- Keep proposal, evidence assessment, owner acceptance and execution permission
  separate. Neither a successful test nor a ready handoff grants permission to
  search, contact people, publish or change a tree.
- Keep the existing DNA exclusion and minimize living-person data. A proposal
  to expand a boundary needs its own review; packaging changes do not expand it.
- Pass the actual previous result and required source material when switching
  skills or chats. Restate the current request and access scope; do not assume
  that another context loaded them or that a status field grants permission.

## Verify what changed

For documentation-only changes, check the instructions, relative links, examples
and export contents. For behavior changes, choose realistic success, ambiguity
or boundary cases relevant to the changed decision. Add a regression for an
observed code defect. Do not add tests that merely assert wording or weaken a
validator to accept a failed response.

When a fresh agent execution is warranted, retain its exact inputs, skill version,
first output and limitations. Keep expected answers out of the executor context.
Separate structural validation from source-based assessment. Record who assessed
the result and what was tested; an author-reviewed example is not an independent
benchmark. Preserve failures and compare a later run separately. Do not rewrite
historical responses or rehash old evidence as if it were the original.

For handoffs, check that required people, claims, sources and unresolved questions
survive the transition. Keep searches as performed, inherited or planned according
to what happened. Test case isolation where relevant. A follow-up may revise an
assessment with a stated reason; it must not silently erase the earlier evidence.
The bundled workflow deliberately retains its prior records unchanged to make
this continuity easy to inspect; append-only data is not a universal schema rule.

State host compatibility per tested surface. A schema PASS does not prove source
truth, implicit discovery, live archive access or improvement over an agent without
the skill. Do not introduce a universal test-count or score threshold without a
reason tied to the task.

## Commands: release, GitHub source and integration checkout

From an extracted release, Python 3.10+ and its standard library are enough for:

```sh
python3 tools/verify_genealogy_package.py
python3 tools/validate_genealogy_handoff.py examples/workflow/01-interview-result.json examples/workflow/02-research-result.json examples/workflow/03-review-result.json
```

These check the delivered artifact and example structure. They do not install
anything. The manifest describes the shipped bytes, so an intentional local edit
will fail the integrity check until a maintainer builds a new release. Validate
an edited JSON with the handoff validator directly; do not alter a released
manifest merely to conceal a failed check.

The clean GitHub source tree includes the skills, examples, repository checker
and focused tests. It does not contain a frozen `MANIFEST.sha256` or `RELEASE.json`.
With Python 3.10+ and Git available, run from that checkout's root:

```sh
python3 -B tools/check_genealogy_repository.py
python3 -B -m unittest discover -s tests -p test_genealogy_repository.py -v
```

The checker reads the current files and checkout revision, builds a consumer
package in a temporary directory and checks its structure, examples, links,
licenses and generated manifest. It rejects unexpected files, symlinks and
common private-path/credential patterns. Keep personal notes outside the tree.
Intentional source edits are checked as new content; they do not require changing
a shipped manifest. This is validation, not a committed-release build or proof
that an edited checkout is clean. For a source export without `.git`, pass
`--source-commit <full-source-sha>` from the delivery receipt explicitly.

The prepared GitHub Actions workflow runs these commands for pushes, pull
requests and manual dispatch. Its matrix is Linux/Python 3.10, macOS/Python 3.14
and Windows/Python 3.14. Actions are pinned to full commits; the token has only
`contents: read`, checkout credentials are not persisted, and no release, install
or merge step is present. No dependencies beyond Python's standard library are
needed by these checks. Symlink rejection tests report a skip if the OS does
not permit creating a test symlink. The matrix is configuration, not evidence
that GitHub jobs or agent-host compatibility tests have run. Add required status
checks to branch protection only after their first successful GitHub execution.

Until an explicit source transition, maintainers work in the designated
integration checkout identified by its `AGENTS.md`
and `docs/HANDOFF.md`. That checkout additionally contains canonical contracts,
historical evaluations, tests and the builder; the consumer archive omits those
maintenance-only files. Follow its root README for Python 3.11+ and development
dependencies. With that environment already available, run from the source root:

```sh
python3 tools/validate_skills.py skills/genealogy-researcher skills/family-interview-to-tree skills/genealogy-evidence-review
python3 tools/check_genealogy_bundle.py
python3 tools/check_genealogy_release.py
python3 -m unittest discover -s tests -q
```

Run any changed skill's relevant tests as well. Review the complete diff and
confirm that historical outputs and unrelated skills remain unchanged. Record
checks and unresolved limits in the existing verification and handoff documents.
There is one authoritative development source. Reconcile an accepted GitHub
patch into that checkout and regenerate the export; do not maintain two divergent
runtime copies. This preparation does not move source authority to GitHub.

## Version and release deliberately

Use one collection version while the skills share this maintenance/release cycle.
The optional data format has its own version, currently `genealogy-handoff-1`.
Do not change that schema identifier just because README or examples changed.

For the current pre-1.0 collection, use a patch increment for compatible fixes or
documentation/example updates, and a minor increment for added skills or material
capability changes. An incompatible handoff change requires an explicit new schema
version, migration guidance and compatibility checks for affected consumers;
announce incompatibilities even before 1.0. Revisit independent skill versions
only if their release cycles actually diverge.

Update release notes and the explicit export file list for new distributable
files. Commit reviewed source inputs before building, then run:

```sh
python3 tools/build_genealogy_release.py .local/releases/genealogy-skills-0.3.3.zip
python3 tools/build_genealogy_release.py --github .local/releases/genealogy-skills-0.3.3-github.zip
```

For a later version, update the package version and filename first. The builder
requires a new output path and will not overwrite an existing ZIP. Verify the
extracted package, its source revision and checksums; retain the previous release.
Keep MIT notices with owned material and separately identify any third-party
content. Never export private archives, raw local paths, unrelated skills or the
mixed source repository's old Git history. The GitHub export includes CI and
source checks and excludes generated release identity/manifest files. It is a
clean file tree, not an initialized Git repository. Keep its source SHA and ZIP
checksum in the delivery receipt; eventual public Git history starts separately.

Building, merging, installing and publishing are separate actions. The maintainer
must have the appropriate authorization for each; passing checks alone does not
publish a release or authorize a main-branch merge.
