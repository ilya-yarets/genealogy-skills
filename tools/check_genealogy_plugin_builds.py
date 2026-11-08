"""Build and verify both plugin profiles offline; never install or load them."""

import argparse
import json
from pathlib import Path
import subprocess
import zipfile

try:
    from . import build_genealogy_plugin as builder
    from . import verify_genealogy_plugin as verifier
except ImportError:
    import build_genealogy_plugin as builder
    import verify_genealogy_plugin as verifier


ROOT = Path(__file__).resolve().parents[1]


def snapshot(root):
    return {path.relative_to(root).as_posix(): verifier.digest(path.read_bytes())
            for path in sorted(root.rglob("*")) if path.is_file()}


def check(root, output):
    root, output = Path(root).resolve(), Path(output)
    # Exclusive creation also refuses a pre-existing or dangling output symlink.
    output.mkdir(parents=True, exist_ok=False)
    expected_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    reports, runtimes = {}, []
    for target in verifier.TARGETS:
        folder = output / target
        folder.mkdir()
        first, repeat = folder / "plugin.zip", folder / "repeat.zip"
        revision, checksum = builder.build(root, first, target=target)
        repeat_revision, repeat_checksum = builder.build(root, repeat, target=target)
        if (revision != expected_revision or repeat_revision != revision
                or checksum != repeat_checksum or first.read_bytes() != repeat.read_bytes()):
            raise ValueError("plugin builds differ or use an unexpected source revision")
        errors = verifier.verify_zip(first, target) + verifier.verify_zip(repeat, target)
        if errors:
            raise ValueError("; ".join(errors))

        extracted = folder / "extracted"
        extracted.mkdir()
        # verify_zip has already checked exact members, paths, regular-file
        # metadata and size limits. The destination was created exclusively.
        with zipfile.ZipFile(first) as archive:
            archive.extractall(extracted)
        before = snapshot(extracted)
        errors = verifier.verify_directory(extracted, target)
        if errors:
            raise ValueError("; ".join(errors))
        if snapshot(extracted) != before:
            raise ValueError("plugin verification changed the extraction")
        runtimes.append({name: before[name] for name in sorted(verifier.RUNTIME_FILES)})
        identity = json.loads((extracted / "PLUGIN_BUILD.json").read_bytes())
        if identity["source_commit"] != revision:
            raise ValueError("plugin source identity mismatch")
        reports[target] = {
            "source_commit": revision, "sha256": checksum,
            "members": len(before), "repeat_identical": True,
            "extracted_read_only": True,
        }
    if runtimes[0] != runtimes[1]:
        raise ValueError("plugin profiles contain different runtime bytes")
    result = {"version": verifier.VERSION, "profiles": reports,
              "shared_runtime_files": len(runtimes[0]),
              "installation_or_runtime_execution": False}
    (output / "verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="New output directory; existing paths are never overwritten")
    args = parser.parse_args()
    try:
        result = check(ROOT, args.output_dir)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        parser.exit(1, f"FAIL: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
