import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools import check_genealogy_evals as evaluations


class EvaluationEvidence(unittest.TestCase):
    def stage(self, directory):
        source = Path(__file__).resolve().parents[1]
        data = source / "evals"
        if not (data / "RUNS.json").is_file():
            data = source / "release/genealogy/evals"
        root = Path(directory)
        shutil.copytree(data, root / "evals")
        shutil.copytree(source / "skills/family-interview-to-tree", root / "skills/family-interview-to-tree")
        return root

    def test_preserved_runs_are_read_only_and_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.stage(directory)
            before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual(evaluations.verify(root), [])
            self.assertEqual(before, {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()})
            output = root / "evals/runs/candidate/kinship-ambiguous.json"
            output.write_bytes(output.read_bytes() + b"\n")
            self.assertTrue(any("output checksum" in e for e in evaluations.verify(root)))

    def test_missing_run_and_changed_candidate_runtime_are_detected(self):
        for defect in ("missing", "runtime"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                root = self.stage(directory)
                if defect == "missing":
                    path = root / "evals/RUNS.json"
                    data = json.loads(path.read_text(encoding="utf-8"))
                    data["runs"].pop()
                    path.write_text(json.dumps(data), encoding="utf-8")
                    expected = "inventory mismatch"
                else:
                    path = root / "skills/family-interview-to-tree/SKILL.md"
                    path.write_bytes(path.read_bytes() + b"\n")
                    expected = "runtime checksum"
                self.assertTrue(any(expected in e for e in evaluations.verify(root)))

    def test_changed_rubric_cannot_reuse_a_previous_grade(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.stage(directory)
            path = root / "evals/rubrics/kinship-ambiguous.json"
            path.write_bytes(path.read_bytes() + b"\n")
            index = root / "evals/RUNS.json"
            data = json.loads(index.read_text(encoding="utf-8"))
            for row in data["runs"]:
                if row["case_id"] == "kinship-ambiguous":
                    row["rubric_sha256"] = evaluations.digest(path.read_bytes())
            index.write_text(json.dumps(data), encoding="utf-8")
            self.assertTrue(any("evaluated rubric" in e for e in evaluations.verify(root)))

    def test_evidence_paths_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("../private.json", "/private.json", "..\\private.json", "C:private.json", "C:/private.json"):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    evaluations.read_member(root, name)

    def test_swapped_cases_and_nonruntime_identity_are_rejected(self):
        for defect in ("output", "input", "rubric", "runtime"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                root = self.stage(directory)
                path = root / "evals/RUNS.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                row, other = data["runs"][:2]
                if defect == "runtime":
                    row["skill_files_sha256"] = {row["input"]: row["input_sha256"]}
                    expected = "runtime file inventory"
                else:
                    row[defect] = other[defect]
                    row[defect + "_sha256"] = other[defect + "_sha256"]
                    expected = "does not belong"
                path.write_text(json.dumps(data), encoding="utf-8")
                self.assertTrue(any(expected in e for e in evaluations.verify(root)))


if __name__ == "__main__":
    unittest.main()
