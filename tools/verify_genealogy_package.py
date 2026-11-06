"""Verify an extracted English genealogy release, without installing anything."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

# A verification command must not add bytecode files to the archive it checks.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

try:
    from .validate_genealogy_handoff import validate
except ImportError:
    from validate_genealogy_handoff import validate


VERSION = "0.3.3"
SKILLS = ("genealogy-researcher", "family-interview-to-tree", "genealogy-evidence-review")
CASES = ("research", "interview", "evidence-review")
WORKFLOW_STEPS = ("01-interview", "02-research", "03-review")
JSON_EXAMPLES = (tuple(f"examples/{case}/result.json" for case in CASES)
                 + tuple(f"examples/workflow/{step}-result.json" for step in WORKFLOW_STEPS))
COMMON = ("SKILL.md", "LICENSE", "agents/openai.yaml", "references/handoff-format.md", "references/task-context.md")
ROOT_FILES = ("README.md", "CONTRIBUTING.md", "CHANGELOG.md", "THIRD_PARTY_NOTICES.md", "LICENSE", "RELEASE.json",
              "tools/validate_genealogy_handoff.py", "tools/verify_genealogy_package.py",
              "examples/README.md", "examples/provenance.json", "examples/workflow/README.md")


def expected_files():
    return (set(ROOT_FILES)
            | {f"skills/{skill}/{name}" for skill in SKILLS for name in COMMON}
            | {"skills/genealogy-researcher/references/research-sheet.md"}
            | {f"examples/{case}/{name}" for case in CASES for name in ("input.md", "result.md", "result.json")}
            | {f"examples/workflow/{step}-{name}" for step in WORKFLOW_STEPS for name in ("input.md", "result.json")})


def digest(data):
    return hashlib.sha256(data).hexdigest()


def release_identity(revision):
    """Describe the committed source; this does not assert publication."""
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("A full source commit SHA is required")
    return (json.dumps({
        "version": VERSION,
        "source_commit": revision,
        "schema_version": "genealogy-handoff-1",
        "skills": list(SKILLS),
        "language": "en",
        "status": "prepared-candidate",
        "examples": "editorial; not original evaluation outputs",
    }, indent=2) + "\n").encode()


def verify(root):
    """Check strict contents, hashes, English text, references and example structure."""
    root = Path(root).resolve()
    errors = []
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            errors.append(f"{path.relative_to(root)}: symlink is not distributable")
        elif path.is_file():
            actual.add(path.relative_to(root).as_posix())
    wanted = expected_files() | {"MANIFEST.sha256"}
    if actual != wanted:
        errors.append(f"file set mismatch: missing={sorted(wanted-actual)}, extra={sorted(actual-wanted)}")
    if errors:
        return errors
    manifest = {}
    for line in (root / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            errors.append("malformed manifest row")
            continue
        value, name = match.groups()
        if name in manifest:
            errors.append(f"duplicate manifest member: {name}")
        manifest[name] = value
    if set(manifest) != expected_files():
        errors.append("manifest does not cover exactly the release files")
    for name in sorted(expected_files()):
        data = (root / name).read_bytes()
        if manifest.get(name) != digest(data):
            errors.append(f"{name}: checksum mismatch")
        try:
            body = data.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"{name}: non-UTF-8 content")
            continue
        if re.search(r"[\u0400-\u04ff]", body):
            errors.append(f"{name}: untranslated Cyrillic content")
        if name.endswith(".md"):
            for url in re.findall(r"\]\(([^)]+)\)", body):
                if url.startswith(("https://", "http://", "#")):
                    continue
                target = ((root / name).parent / url.split("#", 1)[0]).resolve()
                boundary = root / PurePosixPath(name).parts[0]
                if name.startswith("skills/"):
                    boundary = root.joinpath(*PurePosixPath(name).parts[:2])
                else:
                    boundary = root
                if not target.is_relative_to(boundary) or not target.is_file():
                    errors.append(f"{name}: broken or escaping link {url}")
    license_bytes = (root / "LICENSE").read_bytes()
    if not license_bytes.startswith(b"MIT License\n") or b"Copyright (c) 2026 Illia Yarats" not in license_bytes:
        errors.append("root MIT license or confirmed copyright name missing")
    for skill in SKILLS:
        base = root / "skills" / skill
        entry = (base / "SKILL.md").read_text(encoding="utf-8")
        if not entry.startswith(f"---\nname: {skill}\ndescription:") or "\nlicense: MIT\n---\n" not in entry:
            errors.append(f"{skill}: invalid name/license frontmatter")
        if (base / "LICENSE").read_bytes() != license_bytes:
            errors.append(f"{skill}: license differs")
        if f"${skill}" not in (base / "agents/openai.yaml").read_text(encoding="utf-8"):
            errors.append(f"{skill}: default invocation missing")
        for name in ("handoff-format.md", "task-context.md"):
            reference = root / "skills" / SKILLS[0] / "references" / name
            if (base / "references" / name).read_bytes() != reference.read_bytes():
                errors.append(f"{skill}: shared contract differs: {name}")
    for name in JSON_EXAMPLES:
        try:
            data = json.loads((root / name).read_text(encoding="utf-8"))
            errors.extend(f"{name}: {error}" for error in validate(data))
        except (ValueError, TypeError) as exc:
            errors.append(f"{name}: invalid JSON: {exc}")
    try:
        release = json.loads((root / "RELEASE.json").read_text(encoding="utf-8"))
        if (not isinstance(release, dict) or release.get("version") != VERSION
                or release.get("skills") != list(SKILLS)
                or release.get("schema_version") != "genealogy-handoff-1"
                or not re.fullmatch(r"[0-9a-f]{40}", str(release.get("source_commit", "")))):
            errors.append("invalid release identity")
    except (ValueError, TypeError):
        errors.append("invalid RELEASE.json")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        errors = verify(args.root)
    except (OSError, UnicodeError) as exc:
        errors = [str(exc)]
    for error in errors:
        print(f"FAIL: {error}")
    if not errors:
        print(f"PASS: genealogy {VERSION}; exact file set, checksums, licenses, local links and {len(JSON_EXAMPLES)} JSON examples")
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
