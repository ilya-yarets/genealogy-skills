"""Local-only plugin packaging regressions; no host installation or network."""

import hashlib
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile

from tools import build_genealogy_plugin as builder
from tools import verify_genealogy_plugin as verifier


ROOT = Path(__file__).resolve().parents[1]
REVISION = "a" * 40
TARGETS = ("openai", "anthropic")
SKILLS = ("genealogy-researcher", "family-interview-to-tree", "genealogy-evidence-review")
SKILL_FILES = ("SKILL.md", "LICENSE", "agents/openai.yaml",
               "references/handoff-format.md", "references/task-context.md")
RUNTIME_FILES = ({f"skills/{skill}/{name}" for skill in SKILLS for name in SKILL_FILES}
                 | {"skills/genealogy-researcher/references/research-sheet.md"})


def materialize(root, contents):
    for name, data in contents.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


def refresh_manifest(root):
    members = {name: data for name, data in snapshot(root).items() if name != "MANIFEST.sha256"}
    (root / "MANIFEST.sha256").write_bytes("".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n"
        for name, data in sorted(members.items())
    ).encode("utf-8"))


def manifest_path(target):
    return "plugin.json" if target == "openai" else ".claude-plugin/plugin.json"


def write_zip(path, contents, *, extra=None, wrapper=""):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(contents.items()):
            info = zipfile.ZipInfo(wrapper + name)
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
        if extra is not None:
            # The duplicate member is an intentional negative fixture.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr(extra[0], extra[1])


def copy_source(root):
    files = set()
    for target in TARGETS:
        files.update(builder.source_map(target).values())
    files.update({"tools/build_genealogy_plugin.py", "tools/verify_genealogy_plugin.py",
                  "tools/check_genealogy_release.py", "release/genealogy/plugins/core.json"})
    for name in files:
        destination = root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def commit_source(root):
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.name=Plugin Fixture",
                    "-c", "user.email=fixture" + "@" + "example.invalid",
                    "-c", "commit.gpgsign=false", "commit", "-qm", "synthetic plugin fixture"],
                   cwd=root, check=True)
    return git(root, "rev-parse", "HEAD")


class GenealogyPluginPackages(unittest.TestCase):
    def test_both_profiles_share_exact_canonical_runtime_and_minimal_scope(self):
        payloads = {target: builder.payloads(ROOT, REVISION, target) for target in TARGETS}
        for target, contents in payloads.items():
            with self.subTest(target=target):
                self.assertEqual(set(contents), verifier.expected_files(target))
                self.assertEqual({name for name in contents if name.startswith("skills/")}, RUNTIME_FILES)
                for name in RUNTIME_FILES:
                    self.assertEqual(contents[name], (ROOT / name).read_bytes(), name)
                self.assertIn(manifest_path(target), contents)
                other = manifest_path("anthropic" if target == "openai" else "openai")
                self.assertNotIn(other, contents)
                self.assertFalse(any(name.startswith(("evals/", ".git/", ".local/", "hooks/",
                                                       "commands/", "settings/")) for name in contents))
                self.assertFalse(any(name in contents for name in ("mcp.json", ".mcp.json", ".app.json")))
                identity = json.loads(contents["PLUGIN_BUILD.json"])
                self.assertEqual(identity["source_commit"], REVISION)
                self.assertEqual(identity["target"], target)
                self.assertEqual(identity["status"], "prepared-local-only")
                self.assertEqual(set(identity["runtime_sha256"]), RUNTIME_FILES)
                self.assertEqual(identity["runtime_sha256"], json.loads(contents["CORE.json"])["runtime_sha256"])
                for name, digest in identity["runtime_sha256"].items():
                    self.assertEqual(digest, hashlib.sha256(contents[name]).hexdigest())
        for name in RUNTIME_FILES:
            self.assertEqual(payloads["openai"][name], payloads["anthropic"][name])

    def test_extracted_bundles_and_standalone_cli_are_read_only(self):
        for target in TARGETS:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                contents = builder.payloads(ROOT, REVISION, target)
                materialize(root, contents)
                before = snapshot(root)
                self.assertEqual(verifier.verify_directory(root, target), [])
                result = subprocess.run(
                    [sys.executable, "-B", "tools/verify_genealogy_plugin.py", str(root), "--target", target],
                    cwd=root, capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(snapshot(root), before)
                self.assertEqual(before, contents)

    def test_authored_readme_preserves_unicode_and_original_newline_bytes(self):
        for target in TARGETS:
            for ending in ("\n", "\r\n"):
                with self.subTest(target=target, ending=repr(ending)), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / "source"
                    root.mkdir()
                    copy_source(root)
                    path = root / builder.source_map(target)["README.md"]
                    original = path.read_bytes()
                    added = (ending + "Synthetic original spelling: Ян Мельнік. Quote: «Год невядомы»." + ending).encode("utf-8")
                    supplied = original + added
                    path.write_bytes(supplied)
                    contents = builder.payloads(root, REVISION, target)
                    self.assertEqual(contents["README.md"], supplied)
                    self.assertEqual(path.read_bytes(), supplied)
                    package = Path(directory) / "package"
                    materialize(package, contents)
                    self.assertEqual(verifier.verify_directory(package, target), [])
                    self.assertEqual((package / "README.md").read_bytes(), supplied)

    def test_changed_missing_extra_and_wrong_profile_files_fail(self):
        for target in TARGETS:
            contents = builder.payloads(ROOT, REVISION, target)
            for defect in ("changed", "missing", "extra", "wrong-profile"):
                with self.subTest(target=target, defect=defect), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    materialize(root, contents)
                    if defect == "changed":
                        (root / "README.md").write_bytes(contents["README.md"] + b"\nChanged.\n")
                    elif defect == "missing":
                        (root / manifest_path(target)).unlink()
                    elif defect == "extra":
                        (root / "family-notes.md").write_bytes(b"Excluded synthetic note.\n")
                    else:
                        other = "anthropic" if target == "openai" else "openai"
                        self.assertTrue(verifier.verify_directory(root, other))
                        continue
                    self.assertTrue(verifier.verify_directory(root, target))

    def test_hash_manifest_rejects_malformed_duplicate_and_incomplete_rows(self):
        contents = builder.payloads(ROOT, REVISION, "openai")
        for defect in ("malformed", "duplicate", "incomplete"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                materialize(root, contents)
                rows = contents["MANIFEST.sha256"].splitlines(keepends=True)
                altered = (b"not a digest row\n" if defect == "malformed" else
                           b"".join(rows + rows[:1]) if defect == "duplicate" else b"".join(rows[1:]))
                (root / "MANIFEST.sha256").write_bytes(altered)
                self.assertTrue(verifier.verify_directory(root, "openai"))

    def test_rehashed_runtime_and_build_identity_edits_fail(self):
        for target in TARGETS:
            for defect in ("runtime", "runtime-and-identities", "target", "revision"):
                with self.subTest(target=target, defect=defect), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    materialize(root, builder.payloads(ROOT, REVISION, target))
                    if defect.startswith("runtime"):
                        path = root / "skills/family-interview-to-tree/SKILL.md"
                        path.write_bytes(path.read_bytes() + b"\nUnreviewed instruction.\n")
                        if defect == "runtime-and-identities":
                            name = path.relative_to(root).as_posix()
                            for identity_name in ("CORE.json", "PLUGIN_BUILD.json"):
                                identity = root / identity_name
                                data = json.loads(identity.read_bytes())
                                data["runtime_sha256"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
                                identity.write_bytes((json.dumps(data, indent=2) + "\n").encode("utf-8"))
                    else:
                        path = root / "PLUGIN_BUILD.json"
                        data = json.loads(path.read_bytes())
                        data["target" if defect == "target" else "source_commit"] = (
                            "anthropic" if target == "openai" else "openai") if defect == "target" else "bad-revision"
                        path.write_bytes((json.dumps(data, indent=2) + "\n").encode("utf-8"))
                    refresh_manifest(root)
                    self.assertTrue(verifier.verify_directory(root, target))

    def test_rehashed_executable_component_declarations_are_refused(self):
        for target in TARGETS:
            for component in ("mcpServers", "hooks", "commands", "settings"):
                with self.subTest(target=target, component=component), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    materialize(root, builder.payloads(ROOT, REVISION, target))
                    path = root / manifest_path(target)
                    data = json.loads(path.read_bytes())
                    data[component] = {"unexpected": "Never execute this synthetic declaration."}
                    path.write_bytes((json.dumps(data, indent=2) + "\n").encode("utf-8"))
                    refresh_manifest(root)
                    self.assertTrue(verifier.verify_directory(root, target))

    def test_anthropic_manifest_metadata_types_and_author_fields_are_checked(self):
        defects = (
            ("author", "Illia Yarats"),
            ("author", {"name": "Illia Yarats", "unexpected": {}}),
            ("author", {"name": "Illia Yarats", "url": {"not": "text"}}),
            ("keywords", {"genealogy": True}),
            ("keywords", ["genealogy", 3]),
        )
        for index, (field, value) in enumerate(defects):
            with self.subTest(defect=index), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                materialize(root, builder.payloads(ROOT, REVISION, "anthropic"))
                path = root / manifest_path("anthropic")
                data = json.loads(path.read_bytes())
                data[field] = value
                path.write_bytes((json.dumps(data, indent=2) + "\n").encode("utf-8"))
                refresh_manifest(root)
                self.assertTrue(verifier.verify_directory(root, "anthropic"))

    def test_missing_escaping_and_active_openai_assets_are_rejected(self):
        for defect in ("missing", "escaping", "script", "external", "doctype", "nonfinite",
                       "stylesheet-pi", "utf16le-pi", "css-escaped-paint"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                materialize(root, builder.payloads(ROOT, REVISION, "openai"))
                icon = root / "assets/icon.svg"
                if defect == "missing":
                    icon.unlink()
                elif defect == "escaping":
                    path = root / "plugin.json"
                    data = json.loads(path.read_bytes())
                    data["extensions"]["com.openai"]["interface"]["logo"] = "./../outside.svg"
                    path.write_bytes((json.dumps(data, indent=2) + "\n").encode("utf-8"))
                elif defect == "nonfinite":
                    icon.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg" width="Infinity" '
                                     b'height="Infinity" viewBox="0 0 96 96"></svg>')
                elif defect in ("stylesheet-pi", "utf16le-pi"):
                    content = ('<?xml-stylesheet type="text/css" href="https://example.invalid/style.css"?>'
                               '<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" '
                               'viewBox="0 0 96 96"></svg>')
                    icon.write_bytes(content.encode("utf-16le" if defect == "utf16le-pi" else "utf-8"))
                elif defect == "css-escaped-paint":
                    content = icon.read_bytes()
                    changed = content.replace(b'fill="#26474B"', b'fill="u\\72l(//example.invalid/paint.svg#p)"')
                    self.assertNotEqual(changed, content, "Negative fixture must change the packaged paint value.")
                    icon.write_bytes(changed)
                else:
                    extra = {"script": '<script>neverExecute()</script>',
                             "external": '<image href="https://example.invalid/image.svg"/>',
                             "doctype": '<!DOCTYPE svg [<!ENTITY test "value">]>'}[defect]
                    prefix = extra if defect == "doctype" else ""
                    body = "" if defect == "doctype" else extra
                    icon.write_bytes((prefix + '<svg xmlns="http://www.w3.org/2000/svg" '
                                      'width="96" height="96" viewBox="0 0 96 96">' + body + '</svg>').encode("utf-8"))
                refresh_manifest(root)
                self.assertTrue(verifier.verify_directory(root, "openai"))

    def test_rehashed_unknown_schema_vocabulary_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materialize(root, builder.payloads(ROOT, REVISION, "openai"))
            path = root / "schemas/plugin.schema.json"
            data = json.loads(path.read_bytes())
            data["properties"]["name"]["unexpectedValidationKeyword"] = True
            path.write_bytes((json.dumps(data, indent=2) + "\n").encode("utf-8"))
            refresh_manifest(root)
            self.assertTrue(verifier.verify_directory(root, "openai"))

    def test_source_privacy_defects_fail_without_echoing_values(self):
        private_values = (
            "/" + "Users/fictional/private.md",
            "fixture" + "@" + "example.invalid",
            "ghp_" + "x" * 24,
            "-----BEGIN " + "PRIVATE KEY-----",
            "https://example.invalid/data?" + "access_token=fictional",
        )
        for target in TARGETS:
            for value in private_values:
                with self.subTest(target=target, value_kind=private_values.index(value)), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    copy_source(root)
                    source = root / builder.source_map(target)["README.md"]
                    source.write_bytes(source.read_bytes() + ("\n" + value + "\n").encode("utf-8"))
                    with self.assertRaises(ValueError) as caught:
                        builder.payloads(root, REVISION, target)
                    self.assertNotIn(value, str(caught.exception))

    def test_rehashed_private_artifact_content_is_refused_without_echo(self):
        private = "/" + "Users/fictional/private.md"
        for target in TARGETS:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                materialize(root, builder.payloads(ROOT, REVISION, target))
                path = root / "README.md"
                path.write_bytes(path.read_bytes() + ("\n" + private + "\n").encode("utf-8"))
                refresh_manifest(root)
                errors = verifier.verify_directory(root, target)
                self.assertTrue(errors)
                self.assertNotIn(private, "\n".join(errors))

    def test_source_and_extracted_symlinks_are_refused(self):
        for defect in ("source-file", "source-directory", "extracted-file"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "source"
                root.mkdir()
                copy_source(root)
                if defect == "extracted-file":
                    package = Path(directory) / "package"
                    materialize(package, builder.payloads(root, REVISION, "openai"))
                    link = package / "README.md"
                    link.unlink()
                    target = package / "LICENSE"
                elif defect == "source-directory":
                    link = root / "skills/family-interview-to-tree"
                    target = root / "retained-skill"
                    link.rename(target)
                else:
                    link = root / builder.source_map("openai")["README.md"]
                    link.unlink()
                    target = root / "LICENSE.genealogy"
                try:
                    link.symlink_to(target, target_is_directory=defect == "source-directory")
                except OSError as exc:
                    self.skipTest(f"Symlink creation unavailable: {exc}")
                if defect == "extracted-file":
                    self.assertTrue(verifier.verify_directory(package, "openai"))
                else:
                    with self.assertRaises(ValueError):
                        builder.payloads(root, REVISION, "openai")

    def test_zip_root_layout_and_paths_are_checked_without_extraction(self):
        contents = builder.payloads(ROOT, REVISION, "openai")
        defects = ("../outside.md", "/outside.md", "C:outside.md", "C:/outside.md",
                   "..\\outside.md", "family-notes.md", "README.md")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            good = root / "good.zip"
            write_zip(good, contents)
            self.assertEqual(verifier.verify_zip(good, "openai"), [])
            before = snapshot(root)
            self.assertEqual(verifier.verify_zip(good, "openai"), [])
            self.assertEqual(snapshot(root), before)
            for index, name in enumerate(defects):
                with self.subTest(name=name):
                    bad = root / f"bad-{index}.zip"
                    write_zip(bad, contents, extra=(name, b"Excluded synthetic content.\n"))
                    self.assertTrue(verifier.verify_zip(bad, "openai"))
                    self.assertFalse((root / "outside.md").exists())
            wrapped = root / "wrapped.zip"
            write_zip(wrapped, contents, wrapper="unexpected-wrapper/")
            self.assertTrue(verifier.verify_zip(wrapped, "openai"))

    def test_zip_symlink_payloads_are_rejected(self):
        contents = builder.payloads(ROOT, REVISION, "openai")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "symlink.zip"
            with zipfile.ZipFile(path, "w") as archive:
                for name, data in sorted(contents.items()):
                    info = zipfile.ZipInfo(name)
                    info.create_system = 3
                    info.external_attr = ((stat.S_IFLNK | 0o777) if name == "README.md"
                                          else (stat.S_IFREG | 0o644)) << 16
                    archive.writestr(info, b"LICENSE" if name == "README.md" else data)
            self.assertTrue(verifier.verify_zip(path, "openai"))

    def test_committed_builds_are_deterministic_rooted_and_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            root.mkdir()
            copy_source(root)
            revision = commit_source(root)
            (root / "unselected-private.md").write_bytes(b"Never export this synthetic note.\n")
            for target in TARGETS:
                with self.subTest(target=target):
                    first, second = Path(directory) / (target + "-first.zip"), Path(directory) / (target + "-second.zip")
                    self.assertEqual(builder.build(root, first, target=target), builder.build(root, second, target=target))
                    self.assertEqual(first.read_bytes(), second.read_bytes())
                    self.assertEqual(verifier.verify_zip(first, target), [])
                    with zipfile.ZipFile(first) as archive:
                        self.assertEqual(set(archive.namelist()), verifier.expected_files(target))
                        self.assertEqual(json.loads(archive.read("PLUGIN_BUILD.json"))["source_commit"], revision)
                    before = first.read_bytes()
                    with self.assertRaises((FileExistsError, ValueError)):
                        builder.build(root, first, target=target)
                    self.assertEqual(first.read_bytes(), before)
            source = root / builder.source_map("openai")["README.md"]
            source.write_bytes(source.read_bytes() + b"\nUncommitted selected edit.\n")
            with self.assertRaises(ValueError):
                builder.build(root, Path(directory) / "dirty.zip", target="openai")
            self.assertFalse((Path(directory) / "dirty.zip").exists())

    def test_existing_output_directory_and_dangling_symlink_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            root.mkdir()
            copy_source(root)
            commit_source(root)
            existing = Path(directory) / "existing-directory"
            existing.mkdir()
            with self.assertRaises((FileExistsError, IsADirectoryError, ValueError)):
                builder.build(root, existing, target="openai")
            missing = Path(directory) / "must-not-be-created.zip"
            link = Path(directory) / "existing-output-link.zip"
            try:
                link.symlink_to(missing)
            except OSError as exc:
                self.skipTest(f"Symlink creation unavailable: {exc}")
            with self.assertRaises((FileExistsError, ValueError)):
                builder.build(root, link, target="openai")
            self.assertTrue(link.is_symlink())
            self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
