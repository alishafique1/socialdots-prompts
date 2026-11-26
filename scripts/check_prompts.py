#!/usr/bin/env python3
"""Check that every prompt file follows the format in docs/format.md.

Each file `prompts/<id>.md` must open with YAML frontmatter holding the
required fields, and its body must hold the prompt. Blanks in the body are
written `{{name}}` or `{{name: default}}` and must match the `blanks` list.
The script also refuses committed media files, which belong on hosted
storage and are referenced by URL.

Needs PyYAML. Usage: python3 scripts/check_prompts.py
"""
from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = "prompts"

KINDS = {"video-generation", "image-generation", "claude-text"}
ACCOUNTS = {"social-dots", "ali-shafique", "zaira"}
PLATFORMS = {"instagram", "tiktok", "facebook", "youtube", "linkedin", "x", "threads", "google"}
POST_STATUSES = {"posted", "scheduled"}
RESULT_TYPES = {"video", "image"}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BLANK_RE = re.compile(r"\{\{\s*([a-z0-9_]+)\s*(?::[^}]*)?\}\}")
MEDIA_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v", ".mkv", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".heic"}
MAX_MEDIA_BYTES = 300_000

REQUIRED = [
    "id", "title", "kind", "model", "settings", "account", "posts", "date",
    "adapted_from", "result", "offer", "product", "related", "blanks",
]


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("file must start with a '---' frontmatter line")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("frontmatter is not closed with a '---' line")
    return text[4:end], text[end + 5:]


def is_url(value: object) -> bool:
    return isinstance(value, str) and value.startswith("https://")


def optional_url(errors: list[str], field: str, value: object) -> None:
    if value is not None and not is_url(value):
        errors.append(f"{field} must be an https URL or null")


def optional_slug(errors: list[str], field: str, value: object) -> None:
    if value is not None and not (isinstance(value, str) and ID_RE.match(value)):
        errors.append(f"{field} must be a lower-case slug or null")


def check_posts(errors: list[str], posts: object) -> None:
    if not isinstance(posts, list):
        errors.append("posts must be a list")
        return
    for i, post in enumerate(posts):
        where = f"posts[{i}]"
        if not isinstance(post, dict):
            errors.append(f"{where} must be a mapping")
            continue
        if post.get("platform") not in PLATFORMS:
            errors.append(f"{where}.platform must be one of {sorted(PLATFORMS)}")
        if post.get("status") not in POST_STATUSES:
            errors.append(f"{where}.status must be one of {sorted(POST_STATUSES)}")
        at = post.get("at")
        if not isinstance(at, (str, dt.datetime)):
            errors.append(f"{where}.at must be an ISO date-time")
        optional_url(errors, f"{where}.url", post.get("url"))
        if post.get("status") == "posted" and not is_url(post.get("url")):
            errors.append(f"{where}.url is required once a post is posted")


def check_result(errors: list[str], result: object) -> None:
    if result is None:
        return
    if not isinstance(result, dict):
        errors.append("result must be a mapping or null")
        return
    if result.get("type") not in RESULT_TYPES:
        errors.append(f"result.type must be one of {sorted(RESULT_TYPES)}")
    optional_url(errors, "result.url", result.get("url"))
    optional_url(errors, "result.poster", result.get("poster"))
    gallery = result.get("gallery", [])
    if not isinstance(gallery, list) or not all(is_url(g) for g in gallery):
        errors.append("result.gallery must be a list of https URLs")


def check_prompt(path: Path, known_ids: set[str]) -> list[str]:
    errors: list[str] = []
    try:
        head, body = split_frontmatter(path.read_text(encoding="utf-8"))
        meta = yaml.safe_load(head)
    except (ValueError, yaml.YAMLError) as exc:
        return [str(exc)]
    if not isinstance(meta, dict):
        return ["frontmatter must be a mapping"]

    missing = [k for k in REQUIRED if k not in meta]
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
    unknown = sorted(set(meta) - set(REQUIRED))
    if unknown:
        errors.append(f"unknown fields: {', '.join(unknown)}")

    if meta.get("id") != path.stem:
        errors.append(f"id must equal the file name ({path.stem})")
    if not ID_RE.match(str(meta.get("id", ""))):
        errors.append("id must be a lower-case slug")
    for field in ("title", "model"):
        if field in meta and not (isinstance(meta[field], str) and meta[field].strip()):
            errors.append(f"{field} must be a non-empty string")
    if "kind" in meta and meta["kind"] not in KINDS:
        errors.append(f"kind must be one of {sorted(KINDS)}")
    if "account" in meta and meta["account"] not in ACCOUNTS:
        errors.append(f"account must be one of {sorted(ACCOUNTS)}")
    if "settings" in meta and not isinstance(meta["settings"], dict):
        errors.append("settings must be a mapping")
    if "date" in meta and not isinstance(meta["date"], dt.date):
        errors.append("date must be a YYYY-MM-DD date")
    if "posts" in meta:
        check_posts(errors, meta["posts"])
    if "adapted_from" in meta:
        optional_url(errors, "adapted_from", meta["adapted_from"])
    if "result" in meta:
        check_result(errors, meta["result"])
    for field in ("offer", "product"):
        if field in meta:
            optional_slug(errors, field, meta[field])

    related = meta.get("related", [])
    if not isinstance(related, list):
        errors.append("related must be a list of prompt ids")
    else:
        for rid in related:
            if rid not in known_ids:
                errors.append(f"related id '{rid}' has no prompt file")
            if rid == meta.get("id"):
                errors.append("related must not list the prompt itself")

    stripped = body.strip()
    if not (stripped.startswith("```text\n") and stripped.endswith("\n```") and stripped.count("```") == 2):
        errors.append("body must be exactly one ```text fenced block holding the prompt")
    declared = meta.get("blanks", [])
    if not isinstance(declared, list):
        errors.append("blanks must be a list of names")
    else:
        used = set(BLANK_RE.findall(body))
        if set(declared) != used:
            errors.append(
                f"blanks {sorted(declared)} do not match the blanks in the body {sorted(used)}"
            )
    return errors


def committed_media(root: Path) -> list[str]:
    found = []
    for path in root.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.suffix.lower() in MEDIA_EXTENSIONS and path.stat().st_size > MAX_MEDIA_BYTES:
            found.append(str(path.relative_to(root)))
    return sorted(found)


def main(root: Path = ROOT) -> int:
    files = sorted((root / PROMPTS_DIR).glob("*.md"))
    known_ids = {p.stem for p in files}
    failed = 0
    for path in files:
        for error in check_prompt(path, known_ids):
            print(f"{path.relative_to(root)}: {error}")
            failed += 1
    for media in committed_media(root):
        print(f"{media}: media over {MAX_MEDIA_BYTES} bytes must be hosted, not committed")
        failed += 1
    print(f"prompt check: {len(files)} prompts, {failed} problems", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
