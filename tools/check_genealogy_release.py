"""Check genealogy release paths and common secrets, not all personal data.

Checkout mode inspects only Git's tracked/unignored genealogy files, including
their names. Other skills and general repository documents are outside scope.
ZIP mode accepts only the same genealogy scope, optionally in one enclosing
folder. It rejects other members; it does not extract an archive or create one.
The clean English consumer layout is built by build_genealogy_release.py,
which applies these content/path checks to its explicit map and then runs the
standalone verify_genealogy_package.py check. It is not this legacy ZIP layout.
This is adapted from the standalone genealogy candidate's check_release.py.
"""

import argparse
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("genealogy-researcher", "family-interview-to-tree", "genealogy-evidence-review")
SCOPE_DIRS = tuple(f"skills/{name}" for name in SKILLS) + ("evals/genealogy", "release/genealogy")
SCOPE_FILES = {
    "LICENSE.genealogy", "LICENSING.md",
    "contracts/genealogy-handoff-v1.md", "contracts/genealogy-task-context.md",
    "tools/check_genealogy_bundle.py", "tools/check_genealogy_release.py",
    "tools/validate_genealogy_handoff.py", "tests/test_genealogy_handoff.py",
    "tests/test_genealogy_release.py",
    "tools/build_genealogy_release.py", "tools/verify_genealogy_package.py",
    "tests/test_genealogy_package.py",
    "tools/check_genealogy_repository.py", "tests/test_genealogy_repository.py",
    "tools/check_genealogy_evals.py", "tests/test_genealogy_evals.py",
    "tests/test_genealogy_handoff_references.py",
}
BLOCKED_PARTS = {
    ".git", ".local", ".venv", "source-cache", "__pycache__", "dist", "build",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "__MACOSX", ".DS_Store",
}
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py"}
TEXT_NAMES = {".gitignore", ".gitattributes", "MANIFEST.sha256", "LICENSE", "LICENSE.genealogy", "COPYING"}
PATTERNS = {
    "local-environment-path": re.compile(r"/(?:Users|home)/[^/\s]+/|/(?:private/)?var/folders/|" + "/" + r"tmp/[^\s]+"),
    "email-address": re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I),
    "private-key": re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----"),
    "credential-token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{24,})\b"),
    "access-bearing-url": re.compile(r"https?://[^\s]+[?&](?:access_token|token|signature|X-Amz-Signature)=[^\s&]+", re.I),
    "windows-environment-path": re.compile(r"\b[A-Z]:[\\/](?:Users|Documents and Settings|Temp)[\\/]", re.I),
}


def inspect_text(label, data):
    """Report locations/categories without printing matched content."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return [f"{label}: non-UTF-8 payload"]
    return [
        f"{label}:{number}: {category}"
        for number, line in enumerate(text.splitlines(), 1)
        for category, pattern in PATTERNS.items()
        if pattern.search(line)
    ]


def safe_label(name):
    if any(ord(char) < 32 or ord(char) == 127 for char in name):
        return "<redacted filename>"
    if inspect_text("release filename", name.encode("utf-8", errors="replace")):
        return "<redacted filename>"
    return name


def path_errors(name, *, directory=False):
    errors = inspect_text("release filename", name.encode("utf-8", errors="replace"))
    label = safe_label(name)
    path = PurePosixPath(name.replace("\\", "/"))
    if path.is_absolute() or PureWindowsPath(name).drive or ".." in path.parts or BLOCKED_PARTS.intersection(path.parts):
        errors.append(f"{label}: excluded path")
    canonical = name[:-1] if directory and name.endswith("/") else name
    if (not canonical or "\\" in name or path.as_posix() != canonical
            or any(ord(char) < 32 or ord(char) == 127 for char in name)):
        errors.append(f"{label}: noncanonical release path")
    if not directory and path.suffix not in TEXT_SUFFIXES and path.name not in TEXT_NAMES:
        errors.append(f"{label}: non-release file type")
    return errors


def in_scope(name, *, directory=False):
    name = name.rstrip("/")
    if any(name == folder or name.startswith(folder + "/") for folder in SCOPE_DIRS):
        return True
    if directory:
        return any(target.startswith(name + "/") for target in (*SCOPE_DIRS, *SCOPE_FILES))
    return name in SCOPE_FILES


def inspect_zip(path):
    errors = []
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.comment:
                errors.append("ZIP: unexpected comment")
            items = archive.infolist()
            file_names = [item.filename for item in items if not item.is_dir()]
            # At most one enclosing folder. Mixed wrapped/unwrapped contents are
            # deliberately rejected instead of silently broadening the scan.
            prefix = ""
            if file_names and not any(in_scope(name) for name in file_names):
                first = file_names[0].partition("/")
                if first[1] and all(name.startswith(first[0] + "/") for name in file_names):
                    prefix = first[0] + "/"
            names = set()
            scoped_files = 0
            for item in items:
                label = safe_label(item.filename)
                if item.filename in names:
                    errors.append(f"{label}: duplicate ZIP entry")
                names.add(item.filename)
                entry_errors = path_errors(item.filename, directory=item.is_dir())
                errors.extend(entry_errors)
                relative = item.filename[len(prefix):] if prefix else item.filename
                wrapper = bool(prefix and item.is_dir() and item.filename == prefix)
                selected = in_scope(relative, directory=item.is_dir())
                if not selected and not wrapper:
                    errors.append(f"{label}: outside genealogy release scope")
                mode = item.external_attr >> 16
                if stat.S_ISLNK(mode):
                    errors.append(f"{label}: symlink")
                    continue
                if item.comment or item.extra:
                    errors.append(f"{label}: unexpected ZIP metadata")
                if selected and not item.is_dir():
                    scoped_files += 1
                    if entry_errors:
                        continue
                    try:
                        payload = archive.read(item)
                    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, NotImplementedError):
                        errors.append(f"{label}: unreadable ZIP payload")
                        continue
                    errors.extend(inspect_text(label, payload))
            if not scoped_files:
                errors.append("ZIP: no genealogy release files")
    except (OSError, ValueError, zipfile.BadZipFile, NotImplementedError):
        errors.append("ZIP: unreadable archive")
    return errors


def inspect_checkout(root):
    try:
        raw = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--",
             *SCOPE_DIRS, *sorted(SCOPE_FILES)], cwd=root, stderr=subprocess.DEVNULL,
        )
        names = sorted(set(filter(None, raw.decode("utf-8").split("\0"))))
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
        return ["checkout: unable to enumerate UTF-8 genealogy release paths"]
    errors = []
    if not names:
        return ["checkout: no genealogy release files"]
    for name in names:
        if not in_scope(name):
            continue
        label = safe_label(name)
        entry_errors = path_errors(name)
        errors.extend(entry_errors)
        if entry_errors:
            continue
        path = root / name
        # Check every component before reading: a normal file can be reached
        # through a directory symlink, including one outside the checkout.
        parts = PurePosixPath(name).parts
        if any(root.joinpath(*parts[:index]).is_symlink() for index in range(1, len(parts) + 1)):
            errors.append(f"{label}: symlink in release path")
            continue
        try:
            if not path.resolve().is_relative_to(root.resolve()):
                errors.append(f"{label}: path escapes checkout")
            elif path.is_file():
                errors.extend(inspect_text(label, path.read_bytes()))
            else:
                errors.append(f"{label}: missing release file")
        except (OSError, RuntimeError):
            errors.append(f"{label}: unreadable release file")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", nargs="?", type=Path, help="Genealogy-only ZIP, optionally with one enclosing folder.")
    args = parser.parse_args()
    errors = inspect_zip(args.zip) if args.zip else inspect_checkout(ROOT)
    for error in errors:
        print(f"FAIL: {error}")
    if not errors:
        print("PASS: genealogy release scope, paths and common secret patterns; manual personal-data review still required")
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
