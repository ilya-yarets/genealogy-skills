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
    from .check_genealogy_release import inspect_text, path_errors
except ImportError:
    import verify_genealogy_package as package
    from check_genealogy_release import inspect_text, path_errors


SUPPORT_FILES = {
    ".github/workflows/check.yml", ".gitignore", ".gitattributes",
    "tools/check_genealogy_repository.py", "tools/check_genealogy_release.py",
    "tests/test_genealogy_repository.py",
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
    return contents


def payloads(root, revision):
    """Stage current source bytes; a repository is not a frozen release archive."""
    contents = collect(root)
    payload = {name: contents[name] for name in package.expected_files() - {"RELEASE.json"}}
    payload["RELEASE.json"] = package.release_identity(revision)
    payload["MANIFEST.sha256"] = "".join(
        f"{package.digest(data)}  {name}\n" for name, data in sorted(payload.items())
    ).encode()
    return payload


def verify(root, revision):
    contents = payloads(root, revision)
    with tempfile.TemporaryDirectory(prefix="genealogy-ci-") as temporary:
        stage = Path(temporary)
        for name, data in contents.items():
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        return package.verify(stage)


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
        print(f"PASS: genealogy {package.VERSION}; repository scope and staged package checks; "
              f"{len(package.JSON_EXAMPLES)} JSON examples")
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
