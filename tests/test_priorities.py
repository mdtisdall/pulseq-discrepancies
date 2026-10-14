"""Tests of scripts/priorities.py, on the valid fixture records of
tests/fixtures/good (see test_validate_records.py)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import priorities

FIXTURES = Path(__file__).parent / "fixtures"
GOOD = sorted((FIXTURES / "good").glob("*.md"))
REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "priorities.py"


def make_tree(tmp_path: Path) -> Path:
    directory = tmp_path / "discrepancies"
    directory.mkdir()
    for record in GOOD:
        shutil.copy(record, directory / record.name)
    (tmp_path / "docs").mkdir()
    return tmp_path


def section(text: str, heading: str) -> str:
    """The text of one `## ` section."""
    start = text.index(f"## {heading}\n")
    end = text.find("\n## ", start + 1)
    return text[start : end if end != -1 else len(text)]


def test_groups(tmp_path):
    text = priorities.render(priorities.load(make_tree(tmp_path)))
    # DIS-0001: low. DIS-0002 and DIS-0004: fixed. DIS-0003: duplicate, not listed.
    assert "DIS-0001" in section(text, "Low priority")
    assert section(text, "High priority").endswith("None.\n")
    assert section(text, "Medium priority").endswith("None.\n")
    fixed = section(text, "Fixed on master")
    assert "DIS-0002" in fixed and "DIS-0004" in fixed
    assert "DIS-0003" not in text
    assert "| Low | 1 |" in text and "| Fixed on master | 2 |" in text


def test_sorted_by_severity_then_id(tmp_path):
    tree = make_tree(tmp_path)
    # Two more low records: a crash after the playback DIS-0001 in ID order.
    src = (tree / "discrepancies" / "DIS-0001-rf-field-count.md").read_text()
    crash = src.replace("DIS-0001", "DIS-0009").replace("severity: playback", "severity: crash")
    (tree / "discrepancies" / "DIS-0009-crash.md").write_text(crash)
    low = section(priorities.render(priorities.load(tree)), "Low priority")
    assert low.index("DIS-0009") < low.index("DIS-0001")


def test_cell_escapes_pipe():
    assert priorities.escape("a | b\n c") == "a \\| b c"


def test_check_mode(tmp_path):
    tree = make_tree(tmp_path)
    run = lambda *a: subprocess.run(
        [sys.executable, str(SCRIPT), *a, str(tree)], capture_output=True, text=True
    )
    assert run("--check").returncode == 1
    assert run().returncode == 0
    assert run("--check").returncode == 0
    (tree / "docs" / "priorities.md").write_text("edited\n")
    result = run("--check")
    assert result.returncode == 1 and "not up to date" in result.stderr


def test_repository_is_up_to_date():
    expected = priorities.render(priorities.load(REPO))
    assert (REPO / "docs" / "priorities.md").read_text(encoding="utf-8") == expected
