#!/usr/bin/env python3
"""Add a skill to the hub in one command.

    python3 scripts/add-entry.py <source> --id <you>.<skill> --license <SPDX> \
        --author "<Name>" [--author-github <login>] [--submitter <login>] \
        [--skill <name>] [--category <c>]... [--version <v>]

<source> is what `npx skills add` takes for GitHub: `owner/repo`,
`owner/repo/path/to/skill`, `owner/repo@skill`, or
`https://github.com/owner/repo/tree/<ref>/<path>`. The script clones the
repository, pins the exact 40-hex commit, finds the skill (its SKILL.md),
hashes every file into the manifest, copies the repository's LICENSE file
into the entry directory when there is one, writes
entries/skills/<id>/entry.json, rebuilds the generated files and runs the
validator. Nothing is pushed: commit the result and open a pull request.

The skill's own files stay in its repository; this hub stores the entry
(the pin and the manifest). Review status starts at `unreviewed`.
"""

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEGMENT = re.compile(r"^[A-Za-z0-9_.-]+$")
SKIP_DIRS = {".git", "node_modules", "dist", "build", "__pycache__", "target"}
LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE")
DEFAULT_PERMISSIONS_NOTE = (
    "allowed-tools or similar declarations inside SKILL.md are claims by the "
    "skill's author, not host approvals; OpenAR enforces its own permission gates."
)


def die(message: str) -> None:
    sys.exit(f"add-entry: {message}")


def parse_source(text: str) -> tuple[str, str | None, str, str | None]:
    """-> (owner/repo, ref or None, subpath ('' for none), skill or None)."""
    text = text.strip()
    if text.startswith("github:"):
        text = text[len("github:"):]
    skill = None
    url = re.match(r"^https?://github\.com/(.+)$", text)
    if url:
        parts = url.group(1).rstrip("/").removesuffix(".git").split("/")
        if len(parts) < 2:
            die(f"not a repository URL: {text}")
        repo = f"{parts[0]}/{parts[1]}"
        ref, sub = None, ""
        if len(parts) > 2:
            if parts[2] not in ("tree", "blob") or len(parts) < 4:
                die(f"expected …/tree/<ref>/<path>: {text}")
            ref = parts[3]
            rest = parts[4:]
            if rest and rest[-1] == "SKILL.md":
                rest = rest[:-1]
            sub = "/".join(rest)
    else:
        if "@" in text:
            text, skill = text.rsplit("@", 1)
        parts = text.rstrip("/").split("/")
        if len(parts) < 2:
            die(f"expected owner/repo[/path], got {text!r}")
        repo = f"{parts[0]}/{parts[1]}"
        ref, sub = None, "/".join(parts[2:])
    if not all(SEGMENT.match(p) for p in repo.split("/")):
        die(f"bad repository name {repo!r}")
    if any(p in ("", ".", "..") for p in sub.split("/") if sub):
        die(f"bad path {sub!r}")
    return repo, ref, sub, skill


def git(*args: str, cwd: pathlib.Path | None = None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        die(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def checkout(repo: str, ref: str | None, into: pathlib.Path) -> str:
    url = f"https://github.com/{repo}.git"
    if ref and re.fullmatch(r"[0-9a-f]{40}", ref):
        git("init", "-q", str(into))
        git("fetch", "-q", "--depth", "1", url, ref, cwd=into)
        git("checkout", "-q", "FETCH_HEAD", cwd=into)
    else:
        git("clone", "-q", "--depth", "1", *(["--branch", ref] if ref else []), url, str(into))
    return git("rev-parse", "HEAD", cwd=into)


def frontmatter(skill_md: pathlib.Path) -> dict:
    text = skill_md.read_text(errors="replace")
    if not text.startswith("---"):
        return {}
    block = text[3:].split("\n---", 1)[0]
    out = {}
    for line in block.splitlines():
        found = re.match(r"^(name|description):\s*(.*)$", line)
        if found:
            out[found.group(1)] = found.group(2).strip().strip("'\"")
    return out


def find_skills(base: pathlib.Path, depth: int = 0) -> list[pathlib.Path]:
    if (base / "SKILL.md").is_file():
        return [base]
    if depth >= 5:
        return []
    found = []
    for child in sorted(base.iterdir()):
        if child.is_dir() and not child.is_symlink() and child.name not in SKIP_DIRS:
            found += find_skills(child, depth + 1)
    return found


def manifest(skill_dir: pathlib.Path) -> list[dict]:
    files = []
    for path in sorted(skill_dir.rglob("*")):
        rel = path.relative_to(skill_dir)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.is_symlink():
            die(f"{rel} is a symlink; the hub does not carry symlinks")
        if not path.is_file():
            continue
        if rel.parts[0] != "SKILL.md" and (path.parent != skill_dir) and (path.parent / "SKILL.md").is_file():
            die(f"{rel.parent} is a nested skill; add it as its own entry")
        data = path.read_bytes()
        if not data:
            die(f"{rel} is empty; the hub manifest needs non-empty files")
        files.append({
            "path": rel.as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "executable": os.access(path, os.X_OK),
        })
    return files


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("--id", required=True, help="namespaced id, e.g. yourname.my-skill")
    ap.add_argument("--license", required=True, help="SPDX identifier, e.g. MIT")
    ap.add_argument("--author", required=True, help="the skill's original author (name)")
    ap.add_argument("--author-github", help="the author's GitHub login")
    ap.add_argument("--submitter", help="your GitHub login (if you are not the author)")
    ap.add_argument("--skill", help="skill name when the source carries several")
    ap.add_argument("--category", action="append", default=[])
    ap.add_argument("--version", help="upstream version; defaults to the pinned commit")
    ap.add_argument("--force", action="store_true", help="replace an existing entry with this id")
    args = ap.parse_args()

    repo, ref, sub, implied = parse_source(args.source)
    want = args.skill or implied
    entry_dir = ROOT / "entries" / "skills" / args.id
    if (entry_dir / "entry.json").exists() and not args.force:
        die(f"{args.id} already exists; pass --force to replace it (a version label is never reused)")

    with tempfile.TemporaryDirectory(prefix="hub-add-") as tmp:
        checkout_dir = pathlib.Path(tmp) / "src"
        revision = checkout(repo, ref, checkout_dir)
        base = checkout_dir / sub if sub else checkout_dir
        if not base.is_dir():
            die(f"{sub!r} is not a directory in {repo}@{revision[:12]}")
        skills = find_skills(base)
        if want:
            skills = [d for d in skills if frontmatter(d / "SKILL.md").get("name") == want or d.name == want]
        if not skills:
            die(f"no skill{' named ' + repr(want) if want else ''} (no SKILL.md) under {repo}/{sub}")
        if len(skills) > 1:
            names = ", ".join(frontmatter(d / "SKILL.md").get("name") or d.name for d in skills)
            die(f"{len(skills)} skills found ({names}); pick one with --skill or a path")
        skill_dir = skills[0]
        fm = frontmatter(skill_dir / "SKILL.md")
        if not fm.get("name") or not fm.get("description"):
            die("SKILL.md frontmatter needs both name and description")
        files = manifest(skill_dir)
        path = skill_dir.relative_to(checkout_dir).as_posix() or "."
        license_file = next((n for n in LICENSE_NAMES if (checkout_dir / n).is_file()), None)

        authors = [{"name": args.author, **({"github": args.author_github} if args.author_github else {})}]
        entry = {
            "schemaVersion": 1,
            "id": args.id,
            "kind": "skill",
            "name": fm["name"].replace("-", " ").title()[:64],
            "summary": fm["description"][:1000],
            "authors": authors,
            **({"registrySubmitter": args.submitter} if args.submitter else {}),
            "categories": args.category,
            "source": {"repo": repo, "path": path, "revision": revision},
            "version": args.version or revision,
            "license": args.license,
            **({"licenseFile": "LICENSE"} if license_file else {}),
            "review": {"status": "unreviewed", "reviewedRevision": None, "reviewer": None},
            "compat": {},
            "delivery": "hub",
            "files": files,
            "totalBytes": sum(f["bytes"] for f in files),
            "requires": [],
            "permissionsNote": DEFAULT_PERMISSIONS_NOTE,
        }
        entry_dir.mkdir(parents=True, exist_ok=True)
        if license_file:
            shutil.copyfile(checkout_dir / license_file, entry_dir / "LICENSE")
        (entry_dir / "entry.json").write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n")

    print(f"wrote entries/skills/{args.id}/entry.json — {repo}/{path} at {revision[:12]}, "
          f"{len(files)} files, {entry['totalBytes']} bytes"
          + ("" if license_file else " (no LICENSE file at the repository root: check the license)"),
          flush=True)
    for script in ("build-index.py", "build-community.py", "validate.py"):
        if subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT).returncode != 0:
            die(f"{script} failed; fix the entry above before opening the pull request")
    print("next: review entry.json (name, summary, categories), commit, and open a pull request")


if __name__ == "__main__":
    main()
