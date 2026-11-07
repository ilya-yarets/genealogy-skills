import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools import check_genealogy_repository as repository


REVISION = "a" * 40


def fixture(root):
    for name in repository.expected_files():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("Synthetic test content\n", encoding="utf-8")


class RepositoryBoundaries(unittest.TestCase):
    def test_staging_uses_current_bytes_and_excludes_git_and_ci(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            (root / ".git").mkdir()
            (root / ".git/config").write_text("Local Git metadata\n")
            (root / "README.md").write_bytes(b"An intentional source edit\n")
            before = {p.relative_to(root).as_posix(): p.read_bytes()
                      for p in root.rglob("*") if p.is_file()}
            payload = repository.payloads(root, REVISION)
            self.assertEqual(set(payload), repository.package.expected_files() | {"MANIFEST.sha256"})
            self.assertFalse(repository.SUPPORT_FILES & payload.keys())
            self.assertEqual(payload["README.md"], b"An intentional source edit\n")
            self.assertEqual(json.loads(payload["RELEASE.json"])["source_commit"], REVISION)
            manifest = dict(line.split("  ", 1)[::-1] for line in payload["MANIFEST.sha256"].decode().splitlines())
            for name in repository.package.expected_files():
                self.assertEqual(manifest[name], repository.package.digest(payload[name]))
            self.assertEqual(before, {p.relative_to(root).as_posix(): p.read_bytes()
                                     for p in root.rglob("*") if p.is_file()})

    def test_unknown_missing_and_symlink_sources_are_rejected(self):
        for defect in ("extra", "missing", "file-link", "directory-link"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root)
                if defect == "extra":
                    (root / "private-notes.md").write_text("Never distribute\n")
                elif defect == "missing":
                    (root / "README.md").unlink()
                else:
                    target = root / "README.md" if defect == "file-link" else root / "linked-directory"
                    if target.is_file():
                        target.unlink()
                    try:
                        target.symlink_to(root / "examples" if defect == "directory-link" else root / "LICENSE",
                                          target_is_directory=defect == "directory-link")
                    except OSError as exc:
                        # Some Windows accounts cannot create symlinks. Record
                        # this narrow platform limitation rather than fake one.
                        self.skipTest(f"Symlink creation unavailable: {exc}")
                with self.assertRaises(ValueError):
                    repository.payloads(root, REVISION)

    def test_private_content_and_invalid_revision_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            with self.assertRaises(ValueError):
                repository.payloads(root, "not-a-commit")
            (root / "README.md").write_text("contact" + "@" + "example.invalid")
            with self.assertRaisesRegex(ValueError, "email-address"):
                repository.payloads(root, REVISION)

    def test_multilingual_content_preserves_source_bytes_and_privacy_checks(self):
        original = "Synthetic source name: Ян Мельнік. Original quote: «Год невядомы».\n"
        private_samples = {
            "local-environment-path": "/" + "Users/fictional/private.md",
            "windows-environment-path": "C:" + "/" + "Users/fictional/private.md",
            "email-address": "fixture" + "@" + "example.invalid",
            "credential-token": "ghp_" + "x" * 24,
            "private-key": "-----BEGIN " + "PRIVATE KEY-----",
            "access-bearing-url": "https://archive.example.invalid/a?" + "access_token=" + "fictional",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            target = root / "examples/interview/input.md"
            target.write_text(original, encoding="utf-8")
            payload = repository.payloads(root, REVISION)
            self.assertEqual(payload["examples/interview/input.md"], original.encode("utf-8"))
            for category, private in private_samples.items():
                with self.subTest(category=category):
                    target.write_text(original + private, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, category) as caught:
                        repository.payloads(root, REVISION)
                    self.assertNotIn(private, str(caught.exception))

    def test_nested_export_cannot_inherit_parent_git_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            nested = root / "export"
            nested.mkdir()
            with self.assertRaisesRegex(ValueError, "No Git repository at this root"):
                repository.source_revision(nested)


if __name__ == "__main__":
    unittest.main()
