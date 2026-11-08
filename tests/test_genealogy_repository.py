import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import build_genealogy_plugin as plugin_builder
from tools import check_genealogy_repository as repository


REVISION = "a" * 40
ROOT = Path(__file__).resolve().parents[1]


def fixture(root):
    for name in repository.expected_files():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("Synthetic test content\n", encoding="utf-8")


def canonical_exporter():
    # The mixed integration source owns this mapper; the clean public source
    # intentionally ships the plugin builder rather than the consumer exporter.
    if (ROOT / "release/genealogy/README.md").is_file():
        from tools import build_genealogy_release
        return build_genealogy_release
    return None


def exported_source(root):
    exporter = canonical_exporter()
    contents = (exporter.payloads(ROOT, REVISION, github=True) if exporter
                else repository.collect(ROOT))
    for name, data in contents.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return contents


class RepositoryBoundaries(unittest.TestCase):
    def test_public_source_contains_every_plugin_input_and_offline_build_tool(self):
        wanted = repository.expected_files()
        for target in repository.plugin.TARGETS:
            self.assertLessEqual(set(plugin_builder.source_map(target).values()), wanted)
        for name in ("tools/build_genealogy_plugin.py", "tools/verify_genealogy_plugin.py",
                     "tools/check_genealogy_plugin_builds.py", "tests/test_genealogy_plugins.py",
                     "LICENSE.genealogy", "notes/v0.3.4.md"):
            self.assertIn(name, wanted)
        exporter = canonical_exporter()
        if exporter:
            mapping = exporter.source_map(github=True)
            for name in wanted:
                if name.startswith("release/genealogy/plugins/") or name == "LICENSE.genealogy":
                    self.assertEqual(mapping[name], name)
            self.assertEqual(mapping["notes/v0.3.4.md"], "release/genealogy/notes/v0.3.4.md")
        else:
            self.assertEqual(set(repository.collect(ROOT)), wanted)

    def test_materialized_public_source_has_identical_plugin_payloads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exported_source(root)
            for target in repository.plugin.TARGETS:
                with self.subTest(target=target):
                    self.assertEqual(plugin_builder.payloads(root, REVISION, target),
                                     plugin_builder.payloads(ROOT, REVISION, target))
            self.assertEqual(repository.verify(root, REVISION), [])

    def test_plugin_manifest_core_and_schema_corruption_fail_repository_check(self):
        defects = {
            "release/genealogy/plugins/openai/plugin.json": "name",
            "release/genealogy/plugins/core.json": "version",
            "release/genealogy/plugins/schemas/plugin.schema.json": "title",
        }
        for name, key in defects.items():
            with self.subTest(source=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                exported_source(root)
                path = root / name
                content = json.loads(path.read_bytes())
                content[key] = "invalid-synthetic-value"
                path.write_text(json.dumps(content), encoding="utf-8")
                self.assertTrue(repository.verify(root, REVISION))

    def test_repository_requires_identical_mit_license_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            (root / "LICENSE.genealogy").write_text("Different synthetic license\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "license copies differ"):
                repository.payloads(root, REVISION)

    def test_plugin_verification_uses_the_same_captured_source_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exported_source(root)
            captured = repository.collect(root)
            (root / "release/genealogy/plugins/openai/plugin.json").write_bytes(b"invalid later bytes")
            with patch.object(repository, "collect", return_value=captured), patch.object(
                    plugin_builder, "capture", side_effect=AssertionError("source reread")):
                self.assertEqual(repository.verify(root, REVISION), [])

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
            for ending in ("\n", "\r\n"):
                supplied_bytes = (original.rstrip("\n") + ending).encode("utf-8")
                target.write_bytes(supplied_bytes)
                payload = repository.payloads(root, REVISION)
                self.assertEqual(payload["examples/interview/input.md"], supplied_bytes)
            for category, private in private_samples.items():
                with self.subTest(category=category):
                    target.write_bytes((original + private).encode("utf-8"))
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
