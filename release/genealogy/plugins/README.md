# Genealogy Skills plugin — prepared 0.3.4

Version 0.3.4 packages three independently usable genealogy skills by Illia Yarats.
The OpenAI and Anthropic archives contain the same skill instructions and local
references. Their manifests adapt the package layout and presentation for each
host; they do not add another research method or an automatic workflow engine.

| Task | Skill |
|---|---|
| Investigate a genealogy question or plan the next source search | [genealogy-researcher](skills/genealogy-researcher/SKILL.md) |
| Turn supplied family testimony into source-linked proposals | [family-interview-to-tree](skills/family-interview-to-tree/SKILL.md) |
| Compare candidates, conflicting claims and source dependence | [genealogy-evidence-review](skills/genealogy-evidence-review/SKILL.md) |

The skills preserve source locators, original precision, uncertain identities and
corrections. Findings remain proposals. The package has no tree importer, stored
family records, DNA processing, background tasks or connector service. External
research depends on the user's request and the host's available tools. A proposed
next step does not grant permission to contact people, publish or change a tree.

## Package layouts

The OpenAI archive has a root `plugin.json`, with presentation settings inside
`extensions.com.openai`, and a local SVG icon. The Anthropic archive has its
manifest at `.claude-plugin/plugin.json` and uses the standard root `skills/`
directory. Each archive also includes the applicable license, provenance and
offline verification files. Both archives carry the pinned portable manifest schema as an offline verification
resource. Only the OpenAI manifest declares that schema; the Anthropic profile
also receives the separate native Claude check.

## Load and call the plugin

Use the archive for your client. Existing client authentication and any required
account access are separate from the package. The commands below are installation
instructions to run when you choose to load it; extracting or verifying a ZIP
does not install it. Avoid loading a second standalone copy of the same skills.

### Codex CLI: local marketplace

The local-marketplace route was tested with Codex CLI 0.166.0. Start with a new,
dedicated directory, such as `genealogy-marketplace`, without replacing an existing
catalog. Extract the **OpenAI** ZIP directly into its `plugins/genealogy-skills/`
subdirectory, so `plugins/genealogy-skills/plugin.json` exists. Create the file
`.agents/plugins/marketplace.json` under the marketplace root with this content:

```json
{
  "name": "genealogy-local",
  "plugins": [
    {
      "name": "genealogy-skills",
      "source": {"source": "local", "path": "./plugins/genealogy-skills"},
      "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
      "category": "Productivity"
    }
  ]
}
```

The source path is relative to the marketplace root. In the Codex profile where
you intend to use the plugin, replace the example absolute path and run:

```sh
codex --no-daemon plugin marketplace add /absolute/path/to/genealogy-marketplace
codex --no-daemon plugin add genealogy-skills@genealogy-local
```

Start a new session with the installed plugin enabled. An explicit supplied-text
request selects a skill by its native namespace:

```text
$genealogy-skills:genealogy-researcher
Use only the notes below to plan the next source check. Do not browse or change a tree.
```

Substitute `$genealogy-skills:family-interview-to-tree` or
`$genealogy-skills:genealogy-evidence-review` for the other tasks. The test used a
separate temporary marketplace name and profile; the example above gives the
same route a reusable local name. This does not establish GUI installation or
automatic selection. See the [OpenAI plugin packaging guide](https://developers.openai.com/plugins/build/plugins)
for the current marketplace layout and client workflow.

### Claude Code: session-only loading

Extract the **Anthropic** ZIP into a dedicated directory. Point `--plugin-dir` to
the package root containing `.claude-plugin/plugin.json`, rather than `skills/`:

```sh
claude --plugin-dir /absolute/path/to/extracted-anthropic-package
```

In that session, select one command and add the relevant supplied material:

```text
/genealogy-skills:family-interview-to-tree
/genealogy-skills:genealogy-researcher
/genealogy-skills:genealogy-evidence-review
```

This loads the plugin for that session. Native registration of these commands was
verified with Claude Code 2.1.206; completed Claude model calls remain unverified
because the test account could not complete eligible Claude Code authentication.
An installed client and a registered command do not by themselves establish model
access. See [Claude Code plugin documentation](https://code.claude.com/docs/en/plugins/create)
for the current client workflow.

## Local checks

Python 3.10 or newer and its standard library are sufficient for the bundled
package verifier. From the extracted package root, use the matching target:

```sh
python3 -B tools/verify_genealogy_plugin.py . --target openai
python3 -B tools/verify_genealogy_plugin.py . --target anthropic
```

Run only the command for that archive. With an existing Claude Code executable,
the Anthropic manifest can also be checked without installing the plugin:

```sh
claude plugin validate . --strict
```

These are file and manifest checks. They do not substitute for model execution
or establish acceptance by a vendor directory. The delivery report records the
exact source revision, artifact hashes and checks run on the rebuilt archives.

## Native verification and limits

Isolated checks on 2026-11-06 used this unchanged 0.3.4 skill runtime with synthetic
supplied text and no live archive access:

| Client | Loading | Explicit calls |
|---|---|---|
| Codex CLI 0.166.0, temporary local marketplace/plugin installation | Exactly three plugin skills in the native test catalog | Three first responses completed; all JSONs validate and all 21 independent content/scope criteria pass |
| Claude Code 2.1.206, session `--plugin-dir` | Three plugin skills and slash commands registered | No completed model response: the attempted call stopped at authentication; the test account lacked an eligible subscription |

Codex was configured for `gpt-6.1-sol` with low reasoning effort; the event stream
did not independently return the server-side model identity. Only the interview
call emitted an inline-instruction truncation warning. It then read the complete
installed `SKILL.md` and both references before answering. The other two calls
had no such warning and read both references. First responses were preserved
without repair or retry; raw client/authentication traces are not bundled.

This preparation rebuilds documentation and archives without repeating native
installation or model calls. The tested runtime is unchanged. Automatic skill
selection, ChatGPT GUI/Cowork, other hosts, live research, general genealogical
accuracy and improvement over a model without skills remain unverified. These
three cases do not provide a reliability percentage. No directory submission,
publication or permanent working installation is implied by the tests.

## License and data

The project's instructions, packaging code and original illustration use the
included MIT license. [Third-party notices](THIRD_PARTY_NOTICES.md) identify the
portable schema and external documentation separately. No private family material,
historical evaluation excerpt or earlier model-response corpus is bundled.
Keep personal research outside the plugin folder and review the host's data
handling before supplying it. The instructions do not provide a technical sandbox.
