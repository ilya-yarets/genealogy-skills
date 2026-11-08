"""Check a clean genealogy-skills source export, without installing or publishing."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

if __name__ == "__main__":
    sys.dont_write_bytecode = True

try:
    from . import verify_genealogy_package as package
    from . import build_genealogy_plugin as plugin_builder
    from . import verify_genealogy_plugin as plugin
    from .check_genealogy_release import inspect_text, path_errors
except ImportError:
    import verify_genealogy_package as package
    import build_genealogy_plugin as plugin_builder
    import verify_genealogy_plugin as plugin
    from check_genealogy_release import inspect_text, path_errors


SUPPORT_FILES = {
    ".github/workflows/check.yml", ".gitignore", ".gitattributes",
    "tools/check_genealogy_repository.py", "tools/check_genealogy_release.py",
    "tools/build_genealogy_plugin.py", "tools/verify_genealogy_plugin.py",
    "tools/check_genealogy_plugin_builds.py", "LICENSE.genealogy",
    "tests/test_genealogy_repository.py",
    "tests/test_genealogy_handoff_references.py", "tests/test_genealogy_evals.py",
    "tests/test_genealogy_plugins.py", "notes/v0.3.4.md",
    "release/genealogy/plugins/README.md",
    "release/genealogy/plugins/THIRD_PARTY_NOTICES.md",
    "release/genealogy/plugins/core.json",
    "release/genealogy/plugins/openai/plugin.json",
    "release/genealogy/plugins/openai/assets/icon.svg",
    "release/genealogy/plugins/anthropic/plugin.json",
    "release/genealogy/plugins/schemas/plugin.schema.json",
    "release/genealogy/plugins/schemas/LICENSE-Agent-Plugins.md",
}


def expected_files():
    return (package.expected_files() - {"RELEASE.json"}) | SUPPORT_FILES


def collect(root):
    """Reject unknown files and symlinks; only root Git metadata is ignored."""
    root = Path(root).resolve()
    actual = set()
    for parent, directories, files in os.walk(root, followlinks=False):
        parent = Path(parent)
        for name in directories[:]:
            path = parent / name
            if parent == root and name == ".git":
                directories.remove(name)
            elif path.is_symlink():
                raise ValueError("Symlink in repository source")
        for name in files:
            if parent == root and name == ".git":
                continue
            path = parent / name
            if path.is_symlink():
                raise ValueError("Symlink in repository source")
            actual.add(path.relative_to(root).as_posix())
    if actual != expected_files():
        # Avoid printing unknown names that may themselves contain private data.
        raise ValueError(f"Repository file set mismatch: {len(expected_files()-actual)} missing, "
                         f"{len(actual-expected_files())} unexpected")
    contents = {}
    for name in sorted(actual):
        data = (root / name).read_bytes()
        errors = path_errors(name) + inspect_text(name, data)
        if errors:
            raise ValueError("; ".join(errors))
        contents[name] = data
    if contents["LICENSE"] != contents["LICENSE.genealogy"]:
        raise ValueError("Repository MIT license copies differ")
    return contents


def consumer_payloads(contents, revision):
    """Make the consumer projection from one captured source inventory."""
    payload = {name: contents[name] for name in package.expected_files() - {"RELEASE.json"}}
    payload["RELEASE.json"] = package.release_identity(revision)
    payload["MANIFEST.sha256"] = "".join(
        f"{package.digest(data)}  {name}\n" for name, data in sorted(payload.items())
    ).encode()
    return payload


def payloads(root, revision):
    """Stage current source bytes; a repository is not a frozen release archive."""
    return consumer_payloads(collect(root), revision)


def verify(root, revision):
    contents = collect(root)
    consumer = consumer_payloads(contents, revision)
    with tempfile.TemporaryDirectory(prefix="genealogy-ci-") as temporary:
        stage = Path(temporary)
        for name, data in consumer.items():
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        errors = package.verify(stage)
    # Validate exactly the captured source bytes, never a later filesystem read.
    # The support allowlist retains the canonical plugin paths in a clean export.
    for target in plugin.TARGETS:
        inputs = {name: contents[source]
                  for name, source in plugin_builder.source_map(target).items()}
        try:
            plugin_builder.assemble(inputs, revision, target)
        except (ValueError, TypeError, KeyError, UnicodeError) as exc:
            errors.append(f"{target} plugin: {exc}")
    return errors


def source_revision(root):
    """Do not accidentally attribute a nested export to its parent checkout."""
    root = Path(root).resolve()
    top = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=root, text=True).strip()
    if Path(top).resolve() != root:
        raise ValueError("No Git repository at this root; supply --source-commit for a local export")
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-commit", help="Full source SHA for a local export without Git history")
    args = parser.parse_args()
    try:
        revision = args.source_commit or source_revision(args.root)
        errors = verify(args.root, revision)
    except (OSError, UnicodeError, ValueError, subprocess.CalledProcessError) as exc:
        errors = [str(exc)]
    for error in errors:
        print(f"FAIL: {error}")
    if not errors:
        print(f"PASS: genealogy {package.VERSION}; repository scope, consumer and both plugin profiles; "
              f"{len(package.JSON_EXAMPLES)} JSON examples")
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
