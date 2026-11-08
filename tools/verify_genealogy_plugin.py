"""Check this local three-skill plugin profile offline; no loading or installation."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import posixpath
import re
import stat
import sys
import xml.etree.ElementTree as ET
import zipfile

if __name__ == "__main__":
    sys.dont_write_bytecode = True

try:
    from .check_genealogy_release import inspect_text
except ImportError:
    from check_genealogy_release import inspect_text


VERSION = "0.3.4"
TARGETS = ("openai", "anthropic")
SKILLS = ("genealogy-researcher", "family-interview-to-tree", "genealogy-evidence-review")
COMMON = ("SKILL.md", "LICENSE", "agents/openai.yaml", "references/handoff-format.md", "references/task-context.md")
RUNTIME_FILES = ({f"skills/{skill}/{name}" for skill in SKILLS for name in COMMON}
                 | {"skills/genealogy-researcher/references/research-sheet.md"})
CORE_SHA256 = "2fbe52a090876d407b824ef0b0341f1ebae3d0e4850e4604caf7b2590d4967e1"
SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
SCHEMA_SHA256 = "0a4aad95ce337878ad38802ebf0daa3fde76abe3f65400c86bcbb1ec0b3ab883"
SCHEMA_LICENSE_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
ROOT_FILES = {"README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "CORE.json", "PLUGIN_BUILD.json", "MANIFEST.sha256",
              "tools/verify_genealogy_plugin.py", "tools/check_genealogy_release.py",
              "schemas/plugin.schema.json", "schemas/LICENSE-Agent-Plugins.md"}
MAX_FILE_BYTES = 256 * 1024
MAX_TOTAL_BYTES = 16 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def expected_files(target):
    if target not in TARGETS:
        raise ValueError("unsupported plugin target")
    profile = {"plugin.json", "assets/icon.svg"} if target == "openai" else {".claude-plugin/plugin.json"}
    return ROOT_FILES | RUNTIME_FILES | profile


def valid_path(name):
    if not isinstance(name, str) or not name or "\\" in name or any(ord(c) < 32 or ord(c) == 127 for c in name):
        return False
    path = PurePosixPath(name)
    return (not path.is_absolute() and not PureWindowsPath(name).drive and ".." not in path.parts
            and path.as_posix() == name and len(path.parts) <= 12)


def load_json(data):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON key")
            value[key] = item
        return value
    return json.loads(data.decode("utf-8"), object_pairs_hook=unique)


def schema_errors(value, rule, location="plugin"):
    """Evaluate all assertion keywords used by the pinned schema, fail on others.

    This intentionally is not a general JSON Schema implementation or a vendor
    portal validator. Unknown schema vocabulary needs an explicit implementation.
    """
    annotations = {"$schema", "$id", "title", "description"}
    supported = annotations | {"type", "const", "minLength", "maxLength", "pattern", "properties", "required", "additionalProperties", "items"}
    if not isinstance(rule, dict) or set(rule) - supported:
        return ["unsupported schema vocabulary"]
    errors = []
    types = {"object": dict, "array": list, "string": str}
    kind = rule.get("type")
    if kind is not None and (kind not in types or not isinstance(value, types[kind])):
        return [location + ": invalid type"]
    if "const" in rule and value != rule["const"]:
        errors.append(location + ": invalid constant")
    if isinstance(value, str):
        if len(value) < rule.get("minLength", 0) or len(value) > rule.get("maxLength", float("inf")):
            errors.append(location + ": invalid length")
        if "pattern" in rule and not re.search(rule["pattern"], value):
            errors.append(location + ": invalid pattern")
    if isinstance(value, dict):
        properties = rule.get("properties", {})
        if not set(rule.get("required", [])) <= set(value):
            errors.append(location + ": missing required fields")
        for key, child in properties.items():
            if key in value:
                errors.extend(schema_errors(value[key], child, location + "." + key))
        extra = set(value) - set(properties)
        additional = rule.get("additionalProperties", True)
        if extra and additional is False:
            errors.append(location + ": unknown fields")
        elif isinstance(additional, dict):
            for key in extra:
                errors.extend(schema_errors(value[key], additional, location + ".extension"))
    if isinstance(value, list) and "items" in rule:
        for item in value:
            errors.extend(schema_errors(item, rule["items"], location + "[]"))
    return errors


def svg_errors(data):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return ["icon: expected UTF-8 SVG"]
    if any(ord(char) < 32 and char not in "\t\r\n" for char in text):
        return ["icon: invalid text encoding/control characters"]
    if "<!" in text or "<?" in text:
        return ["icon: XML declarations, entities and processing instructions are not allowed"]
    try:
        root = ET.fromstring(text)
        allowed = {"svg", "g", "path", "line", "rect", "circle"}
        attributes = {"width", "height", "viewBox", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry",
                      "fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin", "d", "transform"}
        if root.tag != "{http://www.w3.org/2000/svg}svg":
            return ["icon: expected SVG root"]
        width, height = (float(root.attrib[name]) for name in ("width", "height"))
        box = [float(item) for item in root.attrib["viewBox"].split()]
        if (not all(math.isfinite(x) for x in [width, height, *box]) or width != height or not 48 <= width <= 4096
                or box != [0, 0, width, height]):
            return ["icon: expected square numeric dimensions of at least 48"]
        for node in root.iter():
            if node.tag.removeprefix("{http://www.w3.org/2000/svg}") not in allowed or set(node.attrib) - attributes:
                return ["icon: unsupported active content or attributes"]
            # Paint is a solid color in this authored icon. An allowlist avoids
            # CSS-escaped or protocol-relative external paint-server references.
            for key in ("fill", "stroke"):
                if key in node.attrib and not re.fullmatch(r"(?:#[0-9a-fA-F]{6}|none)", node.attrib[key]):
                    return ["icon: only solid hex colors or none are supported"]
            for value in node.attrib.values():
                if re.search(r"url\s*\(|https?:|javascript:|data:", value, re.I):
                    return ["icon: external/active references are not allowed"]
    except (ET.ParseError, ValueError, KeyError):
        return ["icon: invalid SVG"]
    return []


def manifest_errors(manifest, target, schema):
    errors = []
    if not isinstance(manifest, dict):
        return ["plugin manifest: expected object"]
    if target == "openai":
        errors.extend(schema_errors(manifest, schema))
    else:
        # This profile intentionally uses the common core field types; the
        # native Claude validator is still a separate check of its own schema.
        rule = dict(schema, required=["name"], properties={
            key: value for key, value in schema["properties"].items() if key not in {"$schema", "extensions"}
        })
        errors.extend(schema_errors(manifest, rule))
    if manifest.get("name") != "genealogy-skills" or manifest.get("version") != VERSION or manifest.get("license") != "MIT":
        errors.append("plugin manifest: incorrect package identity")
    author = manifest.get("author")
    if not isinstance(author, dict) or author.get("name") != "Illia Yarats":
        errors.append("plugin manifest: confirmed author missing")
    if not isinstance(manifest.get("description"), str) or not manifest["description"].strip():
        errors.append("plugin manifest: description missing")
    for key in ("homepage", "repository"):
        if manifest.get(key) != "https://github.com/ilya-yarets/genealogy-skills":
            errors.append("plugin manifest: incorrect public project URL")
    if target == "openai":
        extensions = manifest.get("extensions")
        if not isinstance(extensions, dict) or set(extensions) != {"com.openai"}:
            return errors + ["OpenAI extension: unexpected namespace"]
        extension = extensions["com.openai"]
        if not isinstance(extension, dict) or set(extension) != {"interface"}:
            return errors + ["OpenAI extension: only listing metadata is supported"]
        interface = extension["interface"]
        if not isinstance(interface, dict):
            return errors + ["OpenAI interface: expected object"]
        required = {"displayName": 30, "shortDescription": 30, "longDescription": 4000, "developerName": 80, "category": 120}
        allowed = set(required) | {"capabilities", "websiteURL", "supportURL", "defaultPrompt", "brandColor", "composerIcon", "logo"}
        if set(interface) - allowed:
            errors.append("OpenAI interface: unsupported fields")
        for key, maximum in required.items():
            value = interface.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 for c in value):
                errors.append("OpenAI interface: invalid " + key)
        if interface.get("developerName") != "Illia Yarats" or interface.get("category") != "Productivity":
            errors.append("OpenAI interface: incorrect publisher/category")
        for key in ("logo", "composerIcon"):
            if interface.get(key) != "./assets/icon.svg":
                errors.append("OpenAI interface: icon path must use the bundled asset")
        capabilities = interface.get("capabilities", [])
        if not isinstance(capabilities, list) or len(capabilities) > 20 or any(not isinstance(x, str) or not x.strip() or len(x) > 120 for x in capabilities):
            errors.append("OpenAI interface: invalid capabilities")
        prompts = interface.get("defaultPrompt", [])
        if isinstance(prompts, str):
            prompts = [prompts]
        if not isinstance(prompts, list) or len(prompts) > 3 or any(not isinstance(x, str) or not x.strip() or len(x) > 128 or "@" in x for x in prompts):
            errors.append("OpenAI interface: invalid starter prompts")
        for key in ("websiteURL", "supportURL"):
            if key in interface and interface[key] not in {"https://github.com/ilya-yarets/genealogy-skills", "https://github.com/ilya-yarets/genealogy-skills/issues"}:
                errors.append("OpenAI interface: incorrect public listing URL")
        if "brandColor" in interface and interface["brandColor"] != "#26474B":
            errors.append("OpenAI interface: unexpected brand color")
    return errors


def verify_members(members, target):
    wanted = expected_files(target)
    if set(members) != wanted:
        return ["plugin file set mismatch (unknown names omitted)"]
    errors = []
    for name, data in members.items():
        if not valid_path(name) or len(data) > MAX_FILE_BYTES:
            errors.append("plugin has a nonportable path or oversized file")
        errors.extend(inspect_text(name, data))
    if sum(map(len, members.values())) > MAX_TOTAL_BYTES or errors:
        return errors or ["plugin exceeds total size limit"]
    try:
        rows = {}
        for line in members["MANIFEST.sha256"].decode().splitlines():
            match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
            if not match or not valid_path(match[2]) or match[2] in rows:
                raise ValueError("invalid/duplicate manifest row")
            rows[match[2]] = match[1]
        if set(rows) != wanted - {"MANIFEST.sha256"}:
            errors.append("plugin manifest coverage mismatch")
        for name in wanted - {"MANIFEST.sha256"}:
            if rows.get(name) != digest(members[name]):
                errors.append(name + ": checksum mismatch")
        schema_data = members["schemas/plugin.schema.json"]
        if digest(schema_data) != SCHEMA_SHA256 or digest(members["schemas/LICENSE-Agent-Plugins.md"]) != SCHEMA_LICENSE_SHA256:
            errors.append("pinned schema/license identity mismatch")
        else:
            schema = load_json(schema_data)
            manifest_name = "plugin.json" if target == "openai" else ".claude-plugin/plugin.json"
            errors.extend(manifest_errors(load_json(members[manifest_name]), target, schema))
        if digest(members["CORE.json"]) != CORE_SHA256:
            errors.append("pinned canonical core identity mismatch")
        core, build = (load_json(members[name]) for name in ("CORE.json", "PLUGIN_BUILD.json"))
        actual_runtime = {name: digest(members[name]) for name in sorted(RUNTIME_FILES)}
        if not isinstance(core, dict) or not isinstance(build, dict):
            raise ValueError("invalid build identity")
        if (core.get("version") != VERSION or core.get("public_core_commit") != "f095c56cb78b09a28beb98ee0ac14e054eb7325c"
                or core.get("runtime_sha256") != actual_runtime):
            errors.append("canonical runtime identity mismatch")
        if (build.get("target") != target or build.get("version") != VERSION or build.get("status") != "prepared-local-only"
                or not re.fullmatch(r"[0-9a-f]{40}", str(build.get("source_commit", "")))
                or build.get("runtime_sha256") != actual_runtime or build.get("public_core_commit") != core.get("public_core_commit")):
            errors.append("plugin build identity mismatch")
        license_data = members["LICENSE"]
        if not license_data.startswith(b"MIT License\n") or b"Copyright (c) 2026 Illia Yarats" not in license_data:
            errors.append("confirmed MIT license missing")
        for skill in SKILLS:
            base = "skills/" + skill
            entry = members[base + "/SKILL.md"].decode()
            if not entry.startswith("---\nname: " + skill + "\ndescription:") or "\nlicense: MIT\n---\n" not in entry:
                errors.append("skill frontmatter identity mismatch")
            if members[base + "/LICENSE"] != license_data:
                errors.append("standalone skill license differs")
            for reference in ("handoff-format.md", "task-context.md"):
                if members[base + "/references/" + reference] != members["skills/" + SKILLS[0] + "/references/" + reference]:
                    errors.append("shared skill reference differs")
        for name, data in members.items():
            if not name.endswith(".md"):
                continue
            for url in re.findall(r"\]\(([^)]+)\)", data.decode()):
                if url.startswith(("https://", "http://", "#")):
                    continue
                dest = posixpath.normpath(posixpath.join(posixpath.dirname(name), url.split("#")[0]))
                boundary = "/".join(name.split("/")[:2]) + "/" if name.startswith("skills/") else ""
                if not valid_path(dest) or dest not in members or (boundary and not dest.startswith(boundary)):
                    errors.append(name + ": broken/escaping local link")
        if target == "openai":
            errors.extend(svg_errors(members["assets/icon.svg"]))
    except (ValueError, TypeError, KeyError, UnicodeError):
        errors.append("invalid plugin JSON/hash metadata")
    return errors


def verify_directory(root, target):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        return ["plugin root is not a regular directory"]
    wanted = expected_files(target)
    actual = set()
    for parent, directories, files in os.walk(root, followlinks=False):
        for name in [*directories, *files]:
            path = Path(parent) / name
            if path.is_symlink() or (not path.is_dir() and not path.is_file()):
                return ["plugin contains a symlink or special file"]
            if path.is_file():
                actual.add(path.relative_to(root).as_posix())
    if actual != wanted:
        return ["plugin file set mismatch (unknown names omitted)"]
    if any((root / name).stat().st_size > MAX_FILE_BYTES for name in actual):
        return ["plugin file size limit exceeded"]
    try:
        return verify_members({name: (root / name).read_bytes() for name in actual}, target)
    except OSError:
        return ["unreadable plugin file"]


def verify_zip(path, target):
    try:
        if Path(path).is_symlink() or Path(path).stat().st_size > MAX_TOTAL_BYTES:
            return ["plugin ZIP is a symlink or oversized"]
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if archive.comment or len(names) != len(set(names)) or set(names) != expected_files(target):
                return ["plugin ZIP file set/metadata mismatch (unknown names omitted)"]
            if sum(info.file_size for info in infos) > MAX_TOTAL_BYTES:
                return ["plugin ZIP size limit exceeded"]
            for info in infos:
                mode = info.external_attr >> 16
                if (not valid_path(info.filename) or info.is_dir() or info.file_size > MAX_FILE_BYTES
                        or info.flag_bits & 1 or info.comment or info.extra
                        or info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                        or stat.S_IFMT(mode) not in {0, stat.S_IFREG}):
                    return ["plugin ZIP has unsafe members or metadata"]
            return verify_members({info.filename: archive.read(info) for info in infos}, target)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, NotImplementedError):
        return ["unreadable plugin ZIP"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--target", required=True, choices=TARGETS)
    args = parser.parse_args()
    errors = verify_zip(args.path, args.target) if args.path.is_file() else verify_directory(args.path, args.target)
    for error in errors:
        print("FAIL: " + error)
    if not errors:
        print(f"PASS: {args.target} plugin {VERSION}; exact scope, hashes, manifests and three unchanged skills; no install/runtime claim")
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
