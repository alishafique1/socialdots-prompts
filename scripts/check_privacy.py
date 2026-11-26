#!/usr/bin/env python3
"""Block private material from this public repository.

Scans every text file in the repository for material that must never be
published: client names, API keys and tokens, email addresses, phone numbers,
internal file paths and Higgsfield element ids. Exits 1 when anything is found.

Client names are not stored in this repository, because the list itself would
leak them. They come from the PRIVACY_DENYLIST environment variable (one name
per line or comma separated; set as a GitHub Actions secret) and from an
optional, git-ignored `.privacy-denylist` file for local runs.

A literal string that is safe to publish can be added, one per line, to
`privacy-allowlist.txt`. Any finding whose matched text equals an allowlisted
line (case-insensitive) is skipped. Use it sparingly, for example for a
Higgsfield element id that has been made public on purpose.

Usage:
    python3 scripts/check_privacy.py [--require-denylist] [paths...]
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWLIST_FILE = "privacy-allowlist.txt"
DENYLIST_FILE = ".privacy-denylist"
DENYLIST_ENV = "PRIVACY_DENYLIST"

# The checker's own source holds the patterns, and the tests build their
# samples at run time, so neither is scanned. Nothing private may live there.
EXCLUDED = {"scripts/check_privacy.py"}
EXCLUDED_DIRS = ("tests/", ".git/")

RULES: list[tuple[str, re.Pattern[str]]] = [
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("api-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("api-key", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("api-key", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}")),
    ("api-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("api-key", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}")),
    ("api-key", re.compile(r"\bpit-[0-9a-fA-F]{8}-[0-9a-fA-F-]{27}")),
    ("api-key", re.compile(r"\bhf_[A-Za-z0-9]{30,}")),
    ("token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{20,}")),
    (
        "secret-assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|client[_-]?secret)\b"
            r"[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9/+_.-]{16,}"
        ),
    ),
    ("internal-id", re.compile(r"(?i)\blocation[_ -]?id\b[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9]{12,}")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")),
    ("phone", re.compile(r"(?<![\w/])(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?![\w])")),
    ("phone", re.compile(r"(?<![\w/])\+\d{10,15}\b")),
    ("internal-path", re.compile(r"/Users/[^\s\"')]+")),
    ("internal-path", re.compile(r"/home/[A-Za-z0-9_.-]+/")),
    ("internal-path", re.compile(r"(?<![\w.])~/[^\s\"')]+")),
    ("internal-path", re.compile(r"/volume\d+/")),
    ("internal-path", re.compile(r"(?i)\b[A-Z]:\\Users\\")),
    ("internal-path", re.compile(r"(?<![\w])\.data/")),
    ("internal-path", re.compile(r"\b\d-(?:Areas|Projects|Resources|Inbox)/")),
    ("internal-path", re.compile(r"(?<![\w])\.orca/")),
    ("internal-path", re.compile(r"(?<![\w])\.env(?:\.secrets|\.local)?\b")),
    ("internal-path", re.compile(r"\blife-os\b")),
    (
        "higgsfield-element-id",
        re.compile(r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"),
    ),
    ("higgsfield-element-id", re.compile(r"(?i)\belement[_ -]?ids?\b[\"']?\s*[:=]\s*\S+")),
]


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    text: str

    def redacted(self) -> str:
        shown = self.text if len(self.text) <= 6 else self.text[:4] + "..."
        return f"{self.path}:{self.line}: {self.rule}: {shown}"


def parse_terms(raw: str) -> list[str]:
    terms = []
    for part in re.split(r"[\n,]", raw):
        term = part.strip()
        if term and not term.startswith("#"):
            terms.append(term)
    return terms


def load_denylist(root: Path, env: dict[str, str]) -> list[str]:
    terms = parse_terms(env.get(DENYLIST_ENV, ""))
    local = root / DENYLIST_FILE
    if local.is_file():
        terms += parse_terms(local.read_text(encoding="utf-8"))
    return sorted(set(terms), key=str.lower)


def load_allowlist(root: Path) -> set[str]:
    path = root / ALLOWLIST_FILE
    if not path.is_file():
        return set()
    return {t.lower() for t in parse_terms(path.read_text(encoding="utf-8"))}


def term_pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term)
    start = r"(?<!\w)" if term[0].isalnum() else ""
    end = r"(?!\w)" if term[-1].isalnum() else ""
    return re.compile(start + escaped + end, re.IGNORECASE)


def scan_text(path: str, text: str, denylist: list[str], allowlist: set[str]) -> list[Finding]:
    rules = list(RULES) + [("client-name", term_pattern(t)) for t in denylist]
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in rules:
            for match in pattern.finditer(line):
                if match.group(0).lower() in allowlist:
                    continue
                findings.append(Finding(path, number, rule, match.group(0)))
    return findings


def repo_files(root: Path) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=root, capture_output=True, text=True, check=True,
        ).stdout
        files = out.splitlines()
    except (OSError, subprocess.CalledProcessError):
        files = [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()]
    return sorted(f for f in files if (root / f).is_file())


def is_scanned(rel: str) -> bool:
    if rel in EXCLUDED or rel == ALLOWLIST_FILE:
        return False
    return not any(rel.startswith(d) for d in EXCLUDED_DIRS)


def read_text(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\0" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def main(argv: list[str] | None = None, root: Path = ROOT, env: dict[str, str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", help="files to scan (default: the whole repository)")
    parser.add_argument(
        "--require-denylist", action="store_true",
        help=f"fail when no client names were loaded from {DENYLIST_ENV} or {DENYLIST_FILE}",
    )
    args = parser.parse_args(argv)
    env = dict(os.environ) if env is None else env

    denylist = load_denylist(root, env)
    if args.require_denylist and not denylist:
        print(
            f"privacy check: no client names loaded. Set the {DENYLIST_ENV} secret "
            f"or create {DENYLIST_FILE}.", file=sys.stderr,
        )
        return 2
    allowlist = load_allowlist(root)

    files = args.paths or repo_files(root)
    findings: list[Finding] = []
    scanned = 0
    for rel in files:
        if not is_scanned(rel):
            continue
        text = read_text(root / rel)
        if text is None:
            continue
        scanned += 1
        findings += scan_text(rel, text, denylist, allowlist)

    for finding in findings:
        print(finding.redacted())
    print(
        f"privacy check: {scanned} files, {len(denylist)} client names, "
        f"{len(findings)} findings", file=sys.stderr,
    )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
