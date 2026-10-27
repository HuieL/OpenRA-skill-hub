#!/usr/bin/env python3
"""Validate the registry: entry.json contract, in-repo content hashes, and
skills.json consistency. Zero dependencies beyond the Python standard library;
CI runs exactly this script with no secrets and no install step.
"""

import hashlib
import json
import pathlib
import re
import sys

def _root() -> pathlib.Path:
    """The registry tree to read: `--root <dir>` (CI runs the base branch's
    trusted scripts against a pull request's tree), else this checkout."""
    if "--root" in sys.argv:
        index = sys.argv.index("--root")
        if index + 1 >= len(sys.argv):
            sys.exit("--root needs a directory")
        return pathlib.Path(sys.argv[index + 1]).resolve()
    return pathlib.Path(__file__).resolve().parent.parent


ROOT = _root()
ENTRIES = ROOT / "entries" / "skills"
MAX_TOTAL_BYTES = 20 * 1024 * 1024  # = the OpenAR client staging budget (raised from 2 MiB, 10-23)
MAX_FILES = 500
I18N_LANGS = {"en", "zh-CN", "ja", "ko", "es"}
REVIEW_STATUSES = {"unreviewed", "reviewed", "deprecated", "high-risk"}
DELIVERIES = {"hub"}
ENTRY_FIELDS = {
    "schemaVersion", "id", "kind", "name", "summary", "summaryI18n", "authors",
    "maintainers", "contributors", "adapters", "registrySubmitter", "categories",
    "source", "upstream", "version", "license", "licenseFile", "review", "compat",
    "delivery", "files", "totalBytes", "requires", "permissionsNote",
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
# Mirrors the CLI wire contract (namespaced_id): at least two dot-separated
# segments, each starting [a-z0-9], only [a-z0-9-], never ending with '-'.
SEGMENT = r"[a-z0-9]([a-z0-9-]*[a-z0-9])?"
ID = re.compile(rf"^{SEGMENT}(\.{SEGMENT})+$")
RESERVED_NAMESPACES = {"openra", "ora"}
# Skills that ship inside OpenAR itself (built in to every session). The host
# refuses to install a user skill under these names, so a hub entry for one
# could never install; built-in skills are not listed here (user ruling
# 2026-10-12). `ora-*` names are reserved the same way.
BUILTIN_SKILL_NAMES = {"diagram-design"}
SKILL_NAME_LINE = re.compile(r"^name:\s*['\"]?([^'\"\s]+)", re.MULTILINE)
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
HANDLE = re.compile(r"^[A-Za-z0-9-]{1,39}$")

errors: list[str] = []

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import listing as listing_mod  # noqa: E402


def fail(entry_id: str, message: str) -> None:
    errors.append(f"{entry_id}: {message}")


def safe_rel_path(raw: str) -> bool:
    if not raw or raw.startswith("/") or "\\" in raw:
        return False
    parts = raw.split("/")
    return all(part not in ("", ".", "..") for part in parts)


def check_common(entry: dict, entry_id: str):
    unknown = set(entry) - ENTRY_FIELDS
    if unknown:
        fail(entry_id, f"unknown fields: {sorted(unknown)}")
    missing = {
        "schemaVersion", "id", "kind", "name", "summary", "authors", "source",
        "version", "license", "review", "compat", "delivery", "files", "totalBytes",
    } - set(entry)
    if missing:
        fail(entry_id, f"missing fields: {sorted(missing)}")
        return None
    if entry["schemaVersion"] != 1:
        fail(entry_id, "schemaVersion must be 1")
    if entry["kind"] != "skill":
        fail(entry_id, "kind must be 'skill'")
    if not isinstance(entry["name"], str) or not entry["name"] or len(entry["name"]) > 64:
        fail(entry_id, "name must be a non-empty string of at most 64 chars")
    if not isinstance(entry["summary"], str) or not entry["summary"].strip() or len(entry["summary"]) > 1000:
        fail(entry_id, "summary must be a non-empty string of at most 1000 chars")
    if "summaryI18n" in entry:
        i18n = entry["summaryI18n"]
        if not isinstance(i18n, dict) or set(i18n) - I18N_LANGS:
            fail(entry_id, "summaryI18n keys must be a subset of " + ", ".join(sorted(I18N_LANGS)))
        elif any(not isinstance(v, str) or not v.strip() or len(v) > 1000 for v in i18n.values()):
            fail(entry_id, "summaryI18n values must be non-empty strings of at most 1000 chars")
    if not isinstance(entry["version"], str) or not entry["version"] or len(entry["version"]) > 128:
        fail(entry_id, "version must be a non-empty string of at most 128 chars")
    if not isinstance(entry["license"], str) or not entry["license"]:
        fail(entry_id, "license (SPDX) is required")
    return entry


def check_attribution(entry: dict, entry_id: str) -> None:
    authors = entry.get("authors")
    if not isinstance(authors, list) or not authors:
        fail(entry_id, "authors must be a non-empty list of original creators")
    else:
        for author in authors:
            if not isinstance(author, dict) or set(author) - {"name", "github"} or not author.get("name"):
                fail(entry_id, "each author needs a name (and at most a github login)")
                continue
            if not isinstance(author["name"], str) or len(author["name"]) > 64:
                fail(entry_id, "author name must be a string of at most 64 chars")
            github = author.get("github")
            if github is not None and (not isinstance(github, str) or not HANDLE.match(github)):
                fail(entry_id, f"author github {github!r} must be a login without '@'")
    for field in ("maintainers", "contributors", "adapters"):
        logins = entry.get(field, [])
        if not isinstance(logins, list) or any(
            not isinstance(login, str) or not HANDLE.match(login) for login in logins
        ):
            fail(entry_id, f"{field} must be a list of GitHub logins")
    submitter = entry.get("registrySubmitter")
    if submitter is not None and (not isinstance(submitter, str) or not HANDLE.match(submitter)):
        fail(entry_id, "registrySubmitter must be a GitHub login")
    categories = entry.get("categories", [])
    if not isinstance(categories, list) or any(
        not isinstance(category, str) or not category or len(category) > 32 for category in categories
    ):
        fail(entry_id, "categories must be a list of non-empty strings of at most 32 chars")


def check_source(entry: dict, entry_id: str) -> None:
    source = entry["source"]
    if not isinstance(source, dict) or set(source) != {"repo", "path", "revision"}:
        fail(entry_id, "source must have exactly repo, path, revision")
        return
    if not isinstance(source["repo"], str) or not REPO.match(source["repo"]):
        fail(entry_id, "source.repo must be owner/name")
    if source["path"] != "." and not (isinstance(source["path"], str) and safe_rel_path(source["path"])):
        fail(entry_id, "source.path must be '.' or a safe relative path")
    if not isinstance(source["revision"], str) or not HEX40.match(source["revision"]):
        fail(entry_id, "source.revision must be a 40-hex commit SHA (no main/latest/tags)")


def check_upstream(entry: dict, entry_id: str) -> None:
    adapted = bool(entry.get("adapters"))
    upstream = entry.get("upstream")
    if upstream is None:
        if adapted:
            fail(entry_id, "adapted entries (adapters set) must record upstream provenance")
        return
    if not isinstance(upstream, dict) or set(upstream) - {"repo", "revision", "path", "license"}:
        fail(entry_id, "upstream may only have repo, revision, path, license")
        return
    missing = {"repo", "revision", "license"} - set(upstream)
    if missing:
        fail(entry_id, f"upstream is missing: {sorted(missing)}")
        return
    if not REPO.match(upstream["repo"]):
        fail(entry_id, "upstream.repo must be owner/name")
    if not HEX40.match(upstream["revision"]):
        fail(entry_id, "upstream.revision must be a 40-hex commit SHA")
    if "path" in upstream and upstream["path"] != "." and not safe_rel_path(upstream["path"]):
        fail(entry_id, "upstream.path must be '.' or a safe relative path")
    if not upstream["license"]:
        fail(entry_id, "upstream.license (SPDX) is required")


def check_review(entry: dict, entry_id: str) -> None:
    review = entry["review"]
    if not isinstance(review, dict) or set(review) - {"status", "reviewedRevision", "reviewer"}:
        fail(entry_id, "review may only have status, reviewedRevision, reviewer")
        return
    if review.get("status") not in REVIEW_STATUSES:
        fail(entry_id, "review.status must be one of " + ", ".join(sorted(REVIEW_STATUSES)))
    if review.get("status") == "reviewed":
        revision = review.get("reviewedRevision")
        if not isinstance(revision, str) or not HEX40.match(revision):
            fail(entry_id, "review.status 'reviewed' requires a 40-hex reviewedRevision")
    reviewer = review.get("reviewer")
    if reviewer is not None and not isinstance(reviewer, str):
        fail(entry_id, "review.reviewer must be a string or null")


def check_compat(entry: dict, entry_id: str) -> None:
    compat = entry["compat"]
    if not isinstance(compat, dict) or set(compat) - {"minHost", "harnesses"}:
        fail(entry_id, "compat may only have minHost, harnesses")
        return
    if "minHost" in compat and (not isinstance(compat["minHost"], str) or not compat["minHost"]):
        fail(entry_id, "compat.minHost must be a non-empty string")
    harnesses = compat.get("harnesses", [])
    if not isinstance(harnesses, list) or any(not isinstance(h, str) or not h for h in harnesses):
        fail(entry_id, "compat.harnesses must be a list of strings")


def check_files(entry: dict, entry_id: str, entry_dir: pathlib.Path) -> None:
    files = entry["files"]
    if not isinstance(files, list):
        fail(entry_id, "files must be a list")
        return
    if entry["delivery"] == "hub" and not files:
        fail(entry_id, "delivery 'hub' requires a non-empty files manifest")
    if entry["delivery"] not in DELIVERIES:
        fail(entry_id, "delivery must be 'hub' (built-in OpenAR skills are not listed on this hub)")
    seen: set[str] = set()
    total = 0
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "bytes", "executable"}:
            fail(entry_id, "each file needs exactly path, sha256, bytes, executable")
            continue
        path = item["path"]
        if not isinstance(path, str) or not safe_rel_path(path):
            fail(entry_id, f"file path {path!r} is not a safe relative path")
            continue
        if path in seen:
            fail(entry_id, f"duplicate file path {path!r}")
        seen.add(path)
        if not isinstance(item["sha256"], str) or not HEX64.match(item["sha256"]):
            fail(entry_id, f"file {path!r} sha256 must be 64-hex")
        if not isinstance(item["bytes"], int) or item["bytes"] < 1:
            fail(entry_id, f"file {path!r} bytes must be a positive integer")
        if not isinstance(item["executable"], bool):
            fail(entry_id, f"file {path!r} executable must be a boolean")
        total += item["bytes"] if isinstance(item["bytes"], int) else 0
    if entry["totalBytes"] != total:
        fail(entry_id, f"totalBytes {entry['totalBytes']} != sum of files bytes {total}")
    if total > MAX_TOTAL_BYTES:
        fail(entry_id, f"entry exceeds the {MAX_TOTAL_BYTES} byte cap")
    if len(files) > MAX_FILES:
        fail(entry_id, f"entry lists {len(files)} files, over the {MAX_FILES}-file cap")
    if "licenseFile" in entry:
        license_file = entry["licenseFile"]
        if not isinstance(license_file, str) or not safe_rel_path(license_file):
            fail(entry_id, "licenseFile must be a safe relative path")
        elif not (entry_dir / license_file).is_file():
            fail(entry_id, f"licenseFile {license_file!r} not found in the entry directory")
    requires = entry.get("requires", [])
    if not isinstance(requires, list) or any(not isinstance(r, str) or not r for r in requires):
        fail(entry_id, "requires must be a list of ids")
    if "permissionsNote" in entry and not isinstance(entry["permissionsNote"], str):
        fail(entry_id, "permissionsNote must be a string")
    elif isinstance(entry.get("permissionsNote"), str) and len(entry["permissionsNote"]) > 500:
        # The host rejects an over-long note at install time
        # (skill_hub_entry.rs: bounded(p, 500)); catch it at the gate.
        fail(entry_id, "permissionsNote must be at most 500 chars (host install limit)")
    skill_dir = entry_dir / "skill"
    if skill_dir.is_dir():
        hosted: set[pathlib.Path] = {
            p for p in skill_dir.rglob("*") if p.is_file() or p.is_symlink()
        }
        listed: set[str] = {item["path"] for item in files if isinstance(item, dict) and isinstance(item.get("path"), str)}
        for real in sorted(hosted):
            rel = real.relative_to(skill_dir).as_posix()
            if real.is_symlink():
                fail(entry_id, f"symlinks are not allowed in hosted content: {rel}")
                continue
            if rel not in listed:
                fail(entry_id, f"hosted file {rel!r} is not listed in files")
                continue
            digest = hashlib.sha256(real.read_bytes()).hexdigest()
            listed_item = next(i for i in files if i.get("path") == rel)
            if digest != listed_item["sha256"] or real.stat().st_size != listed_item["bytes"]:
                fail(entry_id, f"hosted file {rel!r} hash or size does not match files")
        for rel in sorted(listed):
            if not (skill_dir / rel).is_file():
                fail(entry_id, f"files lists {rel!r} but it is not under skill/")


def check_not_builtin(entry_id: str, entry_dir: pathlib.Path) -> None:
    names = {entry_id.split(".")[-1]}
    hosted = entry_dir / "skill" / "SKILL.md"
    if hosted.is_file():
        found = SKILL_NAME_LINE.search(hosted.read_text(errors="replace").split("\n---", 1)[0])
        if found:
            names.add(found.group(1))
    for name in sorted(names):
        if name in BUILTIN_SKILL_NAMES or name.startswith("ora-"):
            fail(entry_id, f"`{name}` is a built-in OpenAR skill name; built-in skills are not listed on this hub")


def check_hosted_names_unique(by_id: dict[str, pathlib.Path]) -> None:
    """`npx skills add` installs hosted skills by their SKILL.md name and
    drops duplicates, so two hosted skills must not share one."""
    seen: dict[str, str] = {}
    for entry_id, entry_dir in sorted(by_id.items()):
        hosted = entry_dir / "skill" / "SKILL.md"
        if not hosted.is_file():
            continue
        found = SKILL_NAME_LINE.search(hosted.read_text(errors="replace").split("\n---", 1)[0])
        if not found:
            fail(entry_id, "hosted SKILL.md has no name")
            continue
        name = found.group(1)
        if name in seen:
            fail(entry_id, f"hosted skill name `{name}` is already used by {seen[name]}")
        seen[name] = entry_id


def validate_entries() -> dict[str, pathlib.Path]:
    by_id: dict[str, pathlib.Path] = {}
    if not ENTRIES.is_dir():
        return by_id
    for entry_dir in sorted(ENTRIES.iterdir()):
        if not entry_dir.is_dir():
            fail(entry_dir.name, "entries/skills must contain directories only")
            continue
        entry_path = entry_dir / "entry.json"
        if not entry_path.is_file():
            fail(entry_dir.name, "missing entry.json")
            continue
        for real in entry_dir.rglob("*"):
            if real.is_symlink():
                fail(entry_dir.name, f"symlinks are not allowed: {real.relative_to(ROOT)}")
        try:
            entry = json.loads(entry_path.read_text())
        except json.JSONDecodeError as error:
            fail(entry_dir.name, f"entry.json is not valid JSON: {error}")
            continue
        if not isinstance(entry, dict):
            fail(entry_dir.name, "entry.json must be an object")
            continue
        entry_id = entry.get("id", entry_dir.name)
        if not isinstance(entry_id, str) or not ID.match(entry_id) or len(entry_id) > 128:
            fail(entry_dir.name, f"id {entry_id!r} does not match {ID.pattern} (max 128 chars)")
            continue
        if entry_id.split(".")[0] in RESERVED_NAMESPACES:
            fail(entry_dir.name, "id namespace is reserved for built-ins; hub entries use `hub.*` or a publisher namespace")
            continue
        if entry_dir.name != entry_id:
            fail(entry_id, f"directory name {entry_dir.name!r} must equal id")
        if entry_id in by_id:
            fail(entry_id, "duplicate id")
            continue
        by_id[entry_id] = entry_dir
        if check_common(entry, entry_id) is None:
            continue
        check_attribution(entry, entry_id)
        check_source(entry, entry_id)
        check_upstream(entry, entry_id)
        check_review(entry, entry_id)
        check_compat(entry, entry_id)
        check_files(entry, entry_id, entry_dir)
        check_not_builtin(entry_id, entry_dir)
        for problem in listing_mod.check_listing(entry_dir, ICONS):
            fail(entry_id, problem)
    return by_id


def validate_index() -> None:
    path = ROOT / "skills.json"
    if not path.is_file():
        errors.append("skills.json is missing; run scripts/build-index.py")
        return
    try:
        index = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        errors.append(f"skills.json is not valid JSON: {error}")
        return
    if index.get("schemaVersion") != 1 or not isinstance(index.get("entries"), list):
        errors.append("skills.json must have schemaVersion 1 and an entries array")
        return
    ids = [row.get("id") for row in index["entries"] if isinstance(row, dict)]
    if len(ids) != len(index["entries"]):
        errors.append("skills.json has non-object rows")
    if ids != sorted(ids):
        errors.append("skills.json entries are not sorted by id")
    if len(set(ids)) != len(ids):
        errors.append("skills.json has duplicate ids")


def load_community(name):
    path = ROOT / "community" / name
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as error:
        errors.append(f"community/{name}: not valid JSON: {error}")
        return None


def check_community_ref(ref, known_skill_ids, where):
    if not isinstance(ref, str) or ref.count(":") != 1:
        fail(where, f"reference {ref!r} must be kind:id")
        return
    kind, entry_id = ref.split(":")
    if kind not in ("skill", "extension"):
        fail(where, f"reference {ref!r} has unknown kind {kind!r}")
    elif kind == "skill" and entry_id not in known_skill_ids:
        fail(where, f"reference {ref!r} matches no skill entry")


def validate_community(skill_ids):
    if not (ROOT / "community").is_dir():
        return
    featured = load_community("featured.json")
    if featured is not None:
        if featured.get("schemaVersion") != 1 or not isinstance(featured.get("featured"), list):
            errors.append("community/featured.json: schemaVersion 1 and a featured array are required")
        else:
            seen = set()
            for item in featured["featured"]:
                if not isinstance(item, dict) or set(item) != {"id", "reason", "featuredBy", "date"}:
                    errors.append("community/featured.json: each item needs exactly id, reason, featuredBy, date")
                    continue
                check_community_ref(item["id"], skill_ids, "community/featured.json")
                if item["id"] in seen:
                    errors.append(f"community/featured.json: duplicate id {item['id']!r}")
                seen.add(item["id"])
                if not isinstance(item["reason"], str) or not 1 <= len(item["reason"]) <= 500:
                    errors.append("community/featured.json: reason must be 1-500 chars")
                if not isinstance(item["featuredBy"], str) or not HANDLE.match(item["featuredBy"]):
                    errors.append("community/featured.json: featuredBy must be a GitHub login")
                if not isinstance(item["date"], str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", item["date"]):
                    errors.append("community/featured.json: date must be YYYY-MM-DD")
    collections = load_community("collections.json")
    if collections is not None:
        if collections.get("schemaVersion") != 1 or not isinstance(collections.get("collections"), list):
            errors.append("community/collections.json: schemaVersion 1 and a collections array are required")
        else:
            seen = set()
            for item in collections["collections"]:
                if not isinstance(item, dict) or set(item) != {"id", "title", "description", "curators", "entries"}:
                    errors.append("community/collections.json: each item needs exactly id, title, description, curators, entries")
                    continue
                if not isinstance(item["id"], str) or not re.match(r"^[a-z0-9][a-z0-9-]{0,63}$", item["id"]):
                    errors.append(f"community/collections.json: bad collection id {item['id']!r}")
                if item["id"] in seen:
                    errors.append(f"community/collections.json: duplicate collection id {item['id']!r}")
                seen.add(item["id"])
                curators = item["curators"]
                if not isinstance(curators, list) or not curators or any(
                    not isinstance(c, str) or not HANDLE.match(c) for c in curators
                ):
                    errors.append(f"community/collections.json: {item['id']!r} curators must be a non-empty list of GitHub logins")
                entries = item["entries"]
                if not isinstance(entries, list) or not entries or len(set(entries)) != len(entries):
                    errors.append(f"community/collections.json: {item['id']!r} entries must be a non-empty, duplicate-free list")
                    continue
                for ref in entries:
                    check_community_ref(ref, skill_ids, "community/collections.json")
    creators = load_community("creators.json")
    if creators is not None:
        if creators.get("schemaVersion") != 1 or not isinstance(creators.get("creators"), list):
            errors.append("community/creators.json: schemaVersion 1 and a creators array are required")
        else:
            roles = {"author", "maintainer", "contributor", "adapter", "submitter"}
            for creator in creators["creators"]:
                if not isinstance(creator, dict) or set(creator) != {"github", "name", "credits"}:
                    errors.append("community/creators.json: each creator needs exactly github, name, credits")
                    continue
                if creator["github"] is not None and (not isinstance(creator["github"], str) or not HANDLE.match(creator["github"])):
                    errors.append(f"community/creators.json: bad github login {creator['github']!r}")
                if creator["name"] is not None and (not isinstance(creator["name"], str) or not creator["name"]):
                    errors.append("community/creators.json: name must be a non-empty string or null")
                if not creator["github"] and not creator["name"]:
                    errors.append("community/creators.json: a creator needs a github login or a name")
                if not isinstance(creator["credits"], list) or not creator["credits"]:
                    errors.append("community/creators.json: credits must be a non-empty list")
                    continue
                for credit in creator["credits"]:
                    if not isinstance(credit, dict) or set(credit) != {"entry", "roles"}:
                        errors.append("community/creators.json: each credit needs exactly entry, roles")
                        continue
                    check_community_ref(credit["entry"], skill_ids, "community/creators.json")
                    if not isinstance(credit["roles"], list) or not credit["roles"] or not set(credit["roles"]) <= roles:
                        errors.append(f"community/creators.json: bad roles {credit['roles']!r}")
    discovery = load_community("discovery.json")
    if discovery is not None:
        if discovery.get("schemaVersion") != 1:
            errors.append("community/discovery.json: schemaVersion must be 1")
        trending = discovery.get("trending")
        if not isinstance(trending, dict) or not trending.get("metric") or not trending.get("window"):
            errors.append("community/discovery.json: trending needs metric and window")


ICONS = listing_mod.load_icons()


def main() -> None:
    for problem in listing_mod.check_icons(ICONS):
        errors.append(f"icons.json: {problem}")
    by_id = validate_entries()
    check_hosted_names_unique(by_id)
    validate_index()
    validate_community(set(by_id))
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        sys.exit(1)
    print("registry valid")


if __name__ == "__main__":
    main()
