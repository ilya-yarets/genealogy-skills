"""Verify preserved synthetic evaluation evidence; does not grade genealogy."""

import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import sys

if __name__ == "__main__":
    sys.dont_write_bytecode = True

try:
    from .validate_genealogy_handoff import validate
    from .verify_genealogy_package import EVAL_CASES, COMMON
except ImportError:
    from validate_genealogy_handoff import validate
    from verify_genealogy_package import EVAL_CASES, COMMON


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_member(root, name):
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("invalid evaluation member")
    relative = Path(name)
    if relative.is_absolute() or PureWindowsPath(name).drive or ".." in relative.parts:
        raise ValueError("evaluation path escapes root")
    path = root / relative
    if any(root.joinpath(*relative.parts[:i]).is_symlink()
           for i in range(1, len(relative.parts) + 1)):
        raise ValueError("symlink in evaluation member")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("evaluation path escapes root")
    return path.read_bytes()


def verify(root):
    """Compare hashes, saved structural outcomes and assessment inventories."""
    root = Path(root).resolve()
    errors = []
    try:
        runs = json.loads(read_member(root, "evals/RUNS.json"))
        assessment = json.loads(read_member(root, "evals/ASSESSMENT.json"))
        expected = {(variant, case) for variant in ("baseline", "candidate") for case in EVAL_CASES}
        observed = set()
        runtime_files = {"skills/family-interview-to-tree/" + name for name in COMMON}
        for run in runs["runs"]:
            key = (run["variant"], run["case_id"])
            if key in observed:
                errors.append("duplicate evaluation run")
            observed.add(key)
            expected_paths = {
                "input": f"evals/cases/{run['case_id']}.md",
                "rubric": f"evals/rubrics/{run['case_id']}.json",
                "output": f"evals/runs/{run['variant']}/{run['case_id']}.json",
            }
            for field in ("input", "output", "rubric"):
                if run[field] != expected_paths[field]:
                    errors.append(f"{key}: {field} does not belong to this case/variant")
                data = read_member(root, run[field])
                if digest(data) != run[field + "_sha256"]:
                    errors.append(f"{key}: {field} checksum mismatch")
            actual = validate(json.loads(read_member(root, run["output"])))
            if actual != run["structural_errors"]:
                errors.append(f"{key}: structural outcome differs from preserved record")
            if set(run["skill_files_sha256"]) != runtime_files:
                errors.append(f"{key}: runtime file inventory mismatch")
            for name, checksum in run["skill_files_sha256"].items():
                if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-f]{64}", checksum):
                    errors.append(f"{key}: invalid runtime checksum")
                if run["variant"] == "candidate" and digest(read_member(root, name)) != checksum:
                    errors.append(f"{key}: candidate runtime checksum mismatch")
        if observed != expected:
            errors.append("evaluation inventory mismatch")
        grades = [(row["variant"], row["case_id"]) for row in assessment["assessments"]]
        if len(grades) != len(set(grades)) or set(grades) != expected:
            errors.append("assessment inventory mismatch")
        for row in assessment["assessments"]:
            if row.get("status") not in {"pass", "fail", "partial"} or not row.get("reason", "").strip():
                errors.append("assessment requires explicit status and source-based reason")
            output = f"evals/runs/{row['variant']}/{row['case_id']}.json"
            if row.get("output_sha256") != digest(read_member(root, output)):
                errors.append("assessment is not bound to its evaluated output")
            for field, path in (("input", f"evals/cases/{row['case_id']}.md"),
                                ("rubric", f"evals/rubrics/{row['case_id']}.json")):
                if row.get(field + "_sha256") != digest(read_member(root, path)):
                    errors.append(f"assessment is not bound to its evaluated {field}")
        history = json.loads(read_member(root, "evals/history/provenance.json"))
        original = read_member(root, "evals/history/appendix-c.initial.json")
        if digest(original) != history["output_sha256"] or len(original) != history["output_bytes"]:
            errors.append("historical first-output identity mismatch")
        if validate(json.loads(original)):
            errors.append("historical structural outcome changed; record compatibility explicitly")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        errors.append(f"evaluation evidence unreadable or malformed ({type(exc).__name__})")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = verify(args.root)
    for error in errors:
        print(f"FAIL: {error}")
    if not errors:
        print("PASS: 16 saved runs, hashes, structural outcomes and assessment inventory; "
              "semantic grades are recorded judgments, not established by this check")
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
