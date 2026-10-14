#!/usr/bin/env python3
"""Validate the front matter of the discrepancy records.

Usage: validate_records.py [ROOT]

ROOT is the repository root (default: the parent of this script's directory).
Each error is printed to stderr as `path: message`. The exit status is 1 when
there is an error. The rules are those of docs/record-format.md.
"""

from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

import yaml

KINDS = {
    "spec-contradiction",
    "spec-gap",
    "spec-vs-implementation",
    "implementation-vs-implementation",
}
SEVERITIES = {"crash", "playback", "acceptance", "round-trip", "documentation"}
STATUSES = {
    "draft",
    "confirmed",
    "reported",
    "acknowledged",
    "resolved",
    "wontfix",
    "duplicate",
    "withdrawn",
}
# The statuses that need at least one upstream issue URL in report_to.
REPORTED_STATUSES = {"reported", "acknowledged", "resolved", "wontfix"}
# The kinds that can compare one source only.
SINGLE_SOURCE_KINDS = {"spec-contradiction"}

REQUIRED_FIELDS = (
    "id",
    "title",
    "kind",
    "severity",
    "status",
    "format_versions",
    "sources",
    "report_to",
    "found",
    "checked",
)
OPTIONAL_FIELDS = ("pulseq_analysis", "duplicate_of")

FILE_NAME_RE = re.compile(r"^(DIS-\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
ID_RE = re.compile(r"^DIS-\d{4}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
URL_RE = re.compile(r"^https?://\S+$")
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def read_front_matter(text: str) -> tuple[object, str | None]:
    """Return (front matter, error). The front matter is between the first
    two `---` lines; the first line of the file must be `---`."""
    lines = text.splitlines()
    if not lines or lines[0].rstrip() != "---":
        return None, "the first line is not '---'"
    for end in range(1, len(lines)):
        if lines[end].rstrip() == "---":
            break
    else:
        return None, "the front matter has no closing '---'"
    try:
        data = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as e:
        return None, f"the front matter is not valid YAML: {e}"
    if not isinstance(data, dict):
        return None, "the front matter is not a mapping"
    return data, None


def is_date(value: object) -> bool:
    if isinstance(value, datetime.datetime):
        return False
    if isinstance(value, datetime.date):
        return True
    if isinstance(value, str) and DATE_RE.match(value):
        try:
            datetime.date.fromisoformat(value)
        except ValueError:
            return False
        return True
    return False


def is_nonempty_str(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def check_record(
    data: dict, file_id: str, source_keys: set[str]
) -> list[str]:
    """Return the errors of one record's front matter that need no other record."""
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing required field '{field}'")
    for field in data:
        if field not in REQUIRED_FIELDS and field not in OPTIONAL_FIELDS:
            errors.append(f"unknown field '{field}'")

    rid = data.get("id")
    if "id" in data:
        if not isinstance(rid, str) or not ID_RE.match(rid):
            errors.append(f"id {rid!r} is not DIS-NNNN")
        elif rid != file_id:
            errors.append(f"id {rid} is not the file name's prefix {file_id}")

    if "title" in data and not is_nonempty_str(data["title"]):
        errors.append("title is not a non-empty string")

    for field, allowed in (
        ("kind", KINDS),
        ("severity", SEVERITIES),
        ("status", STATUSES),
    ):
        if field in data and data[field] not in allowed:
            errors.append(
                f"{field} {data[field]!r} is not one of: {', '.join(sorted(allowed))}"
            )

    if "format_versions" in data:
        fv = data["format_versions"]
        if (
            not isinstance(fv, list)
            or not fv
            or not all(is_nonempty_str(v) for v in fv)
        ):
            errors.append("format_versions is not a non-empty list of strings")

    if "sources" in data:
        errors.extend(check_sources(data["sources"], data.get("kind"), source_keys))

    if "report_to" in data:
        errors.extend(check_report_to(data["report_to"], data.get("status")))

    if "pulseq_analysis" in data:
        errors.extend(check_pulseq_analysis(data["pulseq_analysis"]))

    for field in ("found", "checked"):
        if field in data and not is_date(data[field]):
            errors.append(f"{field} {data[field]!r} is not a date YYYY-MM-DD")

    status = data.get("status")
    if status == "duplicate" and "duplicate_of" not in data:
        errors.append("status is duplicate, but duplicate_of is missing")
    if status != "duplicate" and "duplicate_of" in data:
        errors.append("duplicate_of is given, but status is not duplicate")
    if "duplicate_of" in data:
        dup = data["duplicate_of"]
        if not isinstance(dup, str) or not ID_RE.match(dup):
            errors.append(f"duplicate_of {dup!r} is not DIS-NNNN")
        elif dup == rid:
            errors.append("duplicate_of is the record's own id")

    return errors


def check_sources(sources: object, kind: object, source_keys: set[str]) -> list[str]:
    if not isinstance(sources, list):
        return ["sources is not a list"]
    errors: list[str] = []
    minimum = 1 if kind in SINGLE_SOURCE_KINDS else 2
    # An unknown kind is reported once, by check_record.
    if kind in KINDS and len(sources) < minimum:
        errors.append(
            f"sources has {len(sources)} entries; kind {kind!r} needs at least {minimum}"
        )
    for i, entry in enumerate(sources):
        where = f"sources[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{where} is not a mapping")
            continue
        for field in ("key", "behavior"):
            if field not in entry:
                errors.append(f"{where} is missing '{field}'")
        for field in entry:
            if field not in ("key", "behavior", "version"):
                errors.append(f"{where} has unknown field '{field}'")
        if "key" in entry and entry["key"] not in source_keys:
            errors.append(f"{where}.key {entry['key']!r} is not in sources.yaml")
        if "behavior" in entry and not is_nonempty_str(entry["behavior"]):
            errors.append(f"{where}.behavior is not a non-empty string")
        if "version" in entry and not is_nonempty_str(entry["version"]):
            errors.append(f"{where}.version is not a non-empty string")
    return errors


def check_report_to(report_to: object, status: object) -> list[str]:
    if not isinstance(report_to, list) or not report_to:
        return ["report_to is not a non-empty list"]
    errors: list[str] = []
    issues = []
    for i, entry in enumerate(report_to):
        where = f"report_to[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{where} is not a mapping")
            continue
        for field in ("repo", "component", "issue"):
            if field not in entry:
                errors.append(f"{where} is missing '{field}'")
        for field in entry:
            if field not in ("repo", "component", "issue"):
                errors.append(f"{where} has unknown field '{field}'")
        if "repo" in entry and not (
            isinstance(entry["repo"], str) and REPO_RE.match(entry["repo"])
        ):
            errors.append(f"{where}.repo {entry['repo']!r} is not owner/name")
        if "component" in entry and not is_nonempty_str(entry["component"]):
            errors.append(f"{where}.component is not a non-empty string")
        issue = entry.get("issue")
        if issue is not None:
            if isinstance(issue, str) and URL_RE.match(issue):
                issues.append(issue)
            else:
                errors.append(f"{where}.issue {issue!r} is not an http(s) URL or null")
    if status in REPORTED_STATUSES and not issues:
        errors.append(f"status is {status}, but no report_to entry has an issue URL")
    return errors


def check_pulseq_analysis(pa: object) -> list[str]:
    if not isinstance(pa, dict):
        return ["pulseq_analysis is not a mapping"]
    errors: list[str] = []
    for field in pa:
        if field not in ("ids", "commit"):
            errors.append(f"pulseq_analysis has unknown field '{field}'")
    ids = pa.get("ids", [])
    if ids is None:
        ids = []
    if not isinstance(ids, list):
        errors.append("pulseq_analysis.ids is not a list")
    elif ids:
        commit = pa.get("commit")
        if not (isinstance(commit, str) and SHA_RE.match(commit)):
            errors.append(
                f"pulseq_analysis.commit {commit!r} is not a hex SHA of 7-40 "
                "characters, and pulseq_analysis.ids is not empty"
            )
    return errors


def load_source_keys(root: Path) -> tuple[set[str], list[str]]:
    path = root / "sources.yaml"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        return set(), [f"{path}: cannot read: {e}"]
    if not isinstance(data, dict):
        return set(), [f"{path}: is not a mapping"]
    return set(data), []


def validate(root: Path) -> list[str]:
    """Return the errors of all the records under root, as `path: message`."""
    source_keys, errors = load_source_keys(root)
    directory = root / "discrepancies"
    if not directory.is_dir():
        return errors + [f"{directory}: is not a directory"]

    ids: dict[str, Path] = {}
    duplicates: list[tuple[Path, str]] = []
    for path in sorted(directory.iterdir()):
        if path.name == ".gitkeep":
            continue
        match = FILE_NAME_RE.match(path.name)
        if not path.is_file() or not match:
            errors.append(f"{path}: the name is not DIS-NNNN-<kebab-slug>.md")
            continue
        file_id = match.group(1)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            errors.append(f"{path}: cannot read: {e}")
            continue
        data, error = read_front_matter(text)
        if error:
            errors.append(f"{path}: {error}")
            continue
        errors.extend(f"{path}: {e}" for e in check_record(data, file_id, source_keys))

        rid = data.get("id")
        if isinstance(rid, str) and ID_RE.match(rid):
            if rid in ids:
                errors.append(f"{path}: id {rid} is also the id of {ids[rid]}")
            else:
                ids[rid] = path
        dup = data.get("duplicate_of")
        if isinstance(dup, str) and ID_RE.match(dup) and dup != rid:
            duplicates.append((path, dup))

    for path, dup in duplicates:
        if dup not in ids:
            errors.append(f"{path}: duplicate_of {dup} is not the id of a record")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    root = Path(argv[1]) if len(argv) == 2 else Path(__file__).resolve().parent.parent
    errors = validate(root)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print(f"validate_records: {len(errors)} error(s)", file=sys.stderr)
        return 1
    count = sum(1 for p in (root / "discrepancies").glob("DIS-*.md"))
    print(f"validate_records: {count} record(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
