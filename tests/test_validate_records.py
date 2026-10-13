"""Tests of scripts/validate_records.py.

The fixture tree is tests/fixtures: its own sources.yaml, the valid records of
good/, and the invalid records of bad/. Each bad record has one error, and a
`# expect: <text>` line (or `<!-- expect: <text> -->` when it has no front
matter) with a part of the error message. Each test builds a repository tree in
tmp_path from these files.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import validate_records

FIXTURES = Path(__file__).parent / "fixtures"
GOOD = sorted((FIXTURES / "good").glob("*.md"))
BAD = sorted((FIXTURES / "bad").glob("*.md"))
REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "validate_records.py"
EXPECT_RE = re.compile(r"(?:# |<!-- )expect: (.*?)(?: -->)?$", re.MULTILINE)


def make_tree(tmp_path: Path, records: list[Path]) -> Path:
    """A repository tree with the fixture sources.yaml and the records."""
    shutil.copy(FIXTURES / "sources.yaml", tmp_path / "sources.yaml")
    directory = tmp_path / "discrepancies"
    directory.mkdir()
    (directory / ".gitkeep").touch()
    for record in records:
        shutil.copy(record, directory / record.name)
    return tmp_path


def expected_message(record: Path) -> str:
    match = EXPECT_RE.search(record.read_text(encoding="utf-8"))
    assert match, f"{record.name} has no expect line"
    return match.group(1)


def test_fixtures_exist():
    assert len(GOOD) >= 3
    assert len(BAD) >= 30


def test_good_records_pass(tmp_path):
    assert validate_records.validate(make_tree(tmp_path, GOOD)) == []


def test_empty_discrepancies_passes(tmp_path):
    assert validate_records.validate(make_tree(tmp_path, [])) == []


@pytest.mark.parametrize("record", BAD, ids=[p.stem for p in BAD])
def test_bad_record_fails(tmp_path, record):
    errors = validate_records.validate(make_tree(tmp_path, GOOD + [record]))
    message = expected_message(record)
    assert errors, f"{record.name} gave no error"
    # Each error is about the bad record, and one of them is the expected one.
    assert all(e.startswith(str(tmp_path / "discrepancies" / record.name)) for e in errors), errors
    assert any(message in e for e in errors), (message, errors)


def test_each_bad_record_has_one_error(tmp_path):
    for record in BAD:
        tree = tmp_path / record.stem
        tree.mkdir()
        errors = validate_records.validate(make_tree(tree, GOOD + [record]))
        assert len(errors) == 1, (record.name, errors)


@pytest.mark.parametrize(
    "name",
    [
        "notes.md",
        "PQD-0001.md",
        "PQD-001-short-id.md",
        "PQD-0901-Upper-Case.md",
        "PQD-0901-under_score.md",
        "PQD-0901-trailing-.md",
        "PQD-0901-slug.txt",
        "README",
    ],
)
def test_bad_file_name_fails(tmp_path, name):
    tree = make_tree(tmp_path, GOOD)
    shutil.copy(GOOD[0], tree / "discrepancies" / name)
    errors = validate_records.validate(tree)
    assert errors == [
        f"{tree / 'discrepancies' / name}: the name is not PQD-NNNN-<kebab-slug>.md"
    ]


def test_subdirectory_fails(tmp_path):
    tree = make_tree(tmp_path, GOOD)
    (tree / "discrepancies" / "PQD-0901-a-directory.md").mkdir()
    errors = validate_records.validate(tree)
    assert len(errors) == 1 and "the name is not" in errors[0]


def test_duplicate_id_fails(tmp_path):
    tree = make_tree(tmp_path, GOOD)
    # The same id, PQD-0001, in a second file with another slug: the file name
    # prefix and the id agree, so only uniqueness catches it.
    shutil.copy(GOOD[0], tree / "discrepancies" / "PQD-0001-another-slug.md")
    errors = validate_records.validate(tree)
    assert len(errors) == 1
    assert "id PQD-0001 is also the id of" in errors[0]


def test_template_is_not_checked(tmp_path):
    tree = make_tree(tmp_path, GOOD)
    (tree / "templates").mkdir()
    shutil.copy(REPO / "templates" / "discrepancy.md", tree / "templates" / "discrepancy.md")
    assert validate_records.validate(tree) == []


def test_source_key_comes_from_root_sources_yaml(tmp_path):
    # PQD-0002 uses the key fixture-only, which only the fixture sources.yaml has.
    tree = make_tree(tmp_path, GOOD)
    (tree / "sources.yaml").write_text("spec: {}\ncpp-reader: {}\n", encoding="utf-8")
    errors = validate_records.validate(tree)
    assert len(errors) == 1 and "'fixture-only' is not in sources.yaml" in errors[0]


def test_cli_exit_status_and_stderr(tmp_path):
    (tmp_path / "good").mkdir()
    good = make_tree(tmp_path / "good", GOOD)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(good)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""

    (tmp_path / "bad").mkdir()
    bad = make_tree(tmp_path / "bad", GOOD + [BAD[0]])
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(bad)], capture_output=True, text=True
    )
    assert result.returncode == 1
    assert f"{bad / 'discrepancies' / BAD[0].name}: " in result.stderr


def test_repository_validates():
    assert validate_records.validate(REPO) == []
