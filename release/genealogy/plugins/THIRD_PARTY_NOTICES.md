# Scope and external references

The project's own skill instructions, packaging code and original neutral node
illustration use the included MIT license, copyright 2026 Illia Yarats. The icon
is not an OpenAI or Anthropic mark. No private family records, historical scans,
source-derived evaluation excerpts or earlier model responses are included.

## Portable manifest schema

The OpenAI package references the Agent Plugins manifest schema version 1.0.0 at
[`plugin.schema.json`](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json)
and includes a copy at `schemas/plugin.schema.json` for offline validation.
The schema is third-party material licensed under Apache-2.0, as stated in the
[Agent Plugins specification license](https://github.com/agentplugins/agent-plugins-spec/blob/main/LICENSE.md).
Both archives preserve the complete Apache license text at
`schemas/LICENSE-Agent-Plugins.md`. The schema copy is unmodified. The local
packaging report records the retrieved source, version and checksums. The
project's MIT declaration does not replace the schema's upstream license.
The Anthropic archive includes the same offline verification resource; this is
not a claim that Claude uses the Agent Plugins schema for its native manifest.

## External documentation

The manifests and checks were prepared using these references:

- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins).
- [OpenAI plugin submission](https://developers.openai.com/plugins/deploy/submission).
- [Claude plugin manifest reference](https://code.claude.com/docs/en/plugins-reference).
- [Claude plugin commands](https://code.claude.com/docs/en/plugins/cli-reference).
- [Anthropic plugin pre-submission checklist](https://claude.com/docs/plugins/pre-submission-checklist).
- [Anthropic directory publishing](https://claude.com/docs/directory/publish).

These are external references, not bundled documentation or endorsements.
OpenAI, Anthropic, ChatGPT, Codex and Claude names belong to their respective
owners. This is an independently authored package. Local validation does not
certify directory acceptance, host compatibility or genealogical accuracy.
