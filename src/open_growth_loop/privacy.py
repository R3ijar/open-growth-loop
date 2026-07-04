from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from .events import PRIVATE_COLUMN_HINTS

DEFAULT_EXCLUDED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "build", "dist", "outbox", "tests"}
TEXT_EXTENSIONS = {".csv", ".md", ".toml", ".json", ".txt", ".yml", ".yaml"}
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|client[_-]?secret|private[_-]?key|secret|token|password)\b\s*[:=]\s*['\"]?([A-Za-z0-9_\-./+=]{8,})"
)
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")


@dataclass(frozen=True)
class PrivacyFinding:
    path: str
    line: int
    kind: str
    detail: str


@dataclass(frozen=True)
class PrivacyScanResult:
    ok: bool
    checked_files: int
    findings: list[PrivacyFinding]


def scan_privacy(workspace: Path, include_tests: bool = False) -> PrivacyScanResult:
    findings: list[PrivacyFinding] = []
    checked_files = 0
    excluded_dirs = set(DEFAULT_EXCLUDED_DIRS)
    if include_tests:
        excluded_dirs.discard("tests")

    for path in _iter_scan_files(workspace, excluded_dirs):
        checked_files += 1
        if path.suffix.lower() == ".csv":
            findings.extend(_scan_csv_header(workspace, path))
        findings.extend(_scan_text_patterns(workspace, path))

    return PrivacyScanResult(ok=not findings, checked_files=checked_files, findings=findings)


def render_privacy_scan_markdown(result: PrivacyScanResult) -> str:
    lines = [
        "# Privacy Scan",
        "",
        f"Checked files: {result.checked_files}",
        f"Status: {'ok' if result.ok else 'findings'}",
        "",
    ]
    if result.ok:
        lines.append("No private-looking CSV headers, email addresses, or secret assignments were found.")
        return "\n".join(lines) + "\n"

    lines.append("## Findings")
    lines.append("")
    for finding in result.findings:
        location = f"{finding.path}:{finding.line}" if finding.line else finding.path
        lines.append(f"- {location} [{finding.kind}] {finding.detail}")
    return "\n".join(lines) + "\n"


def _iter_scan_files(workspace: Path, excluded_dirs: set[str]) -> list[Path]:
    files: list[Path] = []
    for path in workspace.rglob("*"):
        if not path.is_file():
            continue
        if any(part in excluded_dirs for part in path.relative_to(workspace).parts[:-1]):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        files.append(path)
    return sorted(files)


def _scan_csv_header(workspace: Path, path: Path) -> list[PrivacyFinding]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
    except UnicodeDecodeError:
        return []

    private = sorted({field.strip().lower() for field in header if field.strip().lower() in PRIVATE_COLUMN_HINTS})
    if not private:
        return []
    return [
        PrivacyFinding(
            path=_relative_path(workspace, path),
            line=1,
            kind="private_csv_header",
            detail=f"Private-looking CSV columns are not allowed: {', '.join(private)}",
        )
    ]


def _scan_text_patterns(workspace: Path, path: Path) -> list[PrivacyFinding]:
    findings: list[PrivacyFinding] = []
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except UnicodeDecodeError:
        return findings

    for line_number, line in enumerate(lines, start=1):
        if EMAIL_RE.search(line):
            findings.append(
                PrivacyFinding(
                    path=_relative_path(workspace, path),
                    line=line_number,
                    kind="email_address",
                    detail="Email address-like text found.",
                )
            )
        if PRIVATE_KEY_RE.search(line):
            findings.append(
                PrivacyFinding(
                    path=_relative_path(workspace, path),
                    line=line_number,
                    kind="private_key",
                    detail="Private key block marker found.",
                )
            )
        match = SECRET_ASSIGNMENT_RE.search(line)
        if match:
            findings.append(
                PrivacyFinding(
                    path=_relative_path(workspace, path),
                    line=line_number,
                    kind="secret_assignment",
                    detail=f"Secret-like assignment found for {match.group(1)}.",
                )
            )
    return findings


def _relative_path(workspace: Path, path: Path) -> str:
    try:
        return path.relative_to(workspace).as_posix()
    except ValueError:
        return str(path)
