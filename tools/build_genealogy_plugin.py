"""Build local-only OpenAI/Anthropic wrappers from one committed three-skill core."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

try:
    from . import verify_genealogy_plugin as plugin
except ImportError:
    import verify_genealogy_plugin as plugin

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = "release/genealogy/plugins/"


def source_map(target):
    mapping = {name: name for name in plugin.RUNTIME_FILES}
    mapping.update({
        "LICENSE": "LICENSE.genealogy", "README.md": TEMPLATES + "README.md",
        "THIRD_PARTY_NOTICES.md": TEMPLATES + "THIRD_PARTY_NOTICES.md", "CORE.json": TEMPLATES + "core.json",
        "tools/verify_genealogy_plugin.py": "tools/verify_genealogy_plugin.py",
        "tools/check_genealogy_release.py": "tools/check_genealogy_release.py",
        "schemas/plugin.schema.json": TEMPLATES + "schemas/plugin.schema.json",
        "schemas/LICENSE-Agent-Plugins.md": TEMPLATES + "schemas/LICENSE-Agent-Plugins.md",
    })
    if target == "openai":
        mapping.update({"plugin.json": TEMPLATES + "openai/plugin.json", "assets/icon.svg": TEMPLATES + "openai/assets/icon.svg"})
    elif target == "anthropic":
        mapping[".claude-plugin/plugin.json"] = TEMPLATES + "anthropic/plugin.json"
    else:
        raise ValueError("unsupported plugin target")
    return mapping


def capture(root, target):
    root = Path(root).resolve()
    result = {}
    for destination, source in sorted(source_map(target).items()):
        parts = Path(source).parts
        if any(root.joinpath(*parts[:i]).is_symlink() for i in range(1, len(parts) + 1)):
            raise ValueError("symlink in plugin source")
        path = root / source
        if not path.is_file() or path.stat().st_size > plugin.MAX_FILE_BYTES:
            raise ValueError("missing or oversized plugin source")
        result[destination] = path.read_bytes()
    return result


def assemble(contents, revision, target):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("a full committed source SHA is required")
    contents = dict(contents)
    core = plugin.load_json(contents["CORE.json"])
    identity = {"version": plugin.VERSION, "source_commit": revision, "target": target,
                "status": "prepared-local-only", "public_core_commit": core["public_core_commit"],
                "runtime_sha256": {name: plugin.digest(contents[name]) for name in sorted(plugin.RUNTIME_FILES)}}
    contents["PLUGIN_BUILD.json"] = (json.dumps(identity, indent=2) + "\n").encode()
    contents["MANIFEST.sha256"] = "".join(plugin.digest(data) + "  " + name + "\n" for name, data in sorted(contents.items())).encode()
    errors = plugin.verify_members(contents, target)
    if errors:
        raise ValueError("; ".join(errors))
    return contents


def payloads(root, revision, target):
    return assemble(capture(root, target), revision, target)


def build(root, output, *, target):
    root = Path(root).resolve()
    # Preserve the final path component: resolving a dangling symlink would
    # turn exclusive creation into an unintended write to its external target.
    output = Path(os.path.abspath(output))
    if os.path.lexists(output):
        raise ValueError("plugin output already exists; no overwrite")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    contents = capture(root, target)
    # Compare the same captured bytes that will be packaged, without rereading.
    for destination, source in source_map(target).items():
        committed = subprocess.check_output(["git", "show", revision + ":" + source], cwd=root)
        if contents[destination] != committed:
            raise ValueError("plugin input differs from the committed source")
    builder_data = (root / "tools/build_genealogy_plugin.py").read_bytes()
    if builder_data != subprocess.check_output(["git", "show", revision + ":tools/build_genealogy_plugin.py"], cwd=root):
        raise ValueError("plugin builder differs from committed source")
    contents = assemble(contents, revision, target)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream, zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(contents.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 6, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compresslevel=9)
    return revision, plugin.digest(output.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--target", choices=plugin.TARGETS, required=True)
    args = parser.parse_args()
    try:
        revision, sha = build(ROOT, args.output, target=args.target)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"FAIL: {exc}\n")
    print(f"Prepared {args.target} plugin {plugin.VERSION} from {revision}\nSHA-256 {sha}")


if __name__ == "__main__":
    main()
