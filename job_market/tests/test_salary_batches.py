"""Nhập lô tin tuyển dụng từ CSV (#105)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from career_market.salary_batches import BatchError, import_batch, load_batch, stored_batches

HEADER = "source,title,company,location,salary_text,experience_text,description,url,posted_date"
GOOD = [
    "Lô thử (TopCV),Backend Developer Java,Công ty A,Hà Nội,15 - 25 triệu,2 năm,Java Spring,"
    "https://example.test/1,2026-11-01",
    "Lô thử (TopCV),Data Engineer,Công ty B,Hồ Chí Minh,20 - 30 triệu,3 năm,Python SQL,"
    "https://example.test/2,",
]
BAD = [
    "Lô thử (TopCV),,Công ty C,Hà Nội,10 - 12 triệu,1 năm,,https://example.test/3,2026-11-01",
    "Lô thử (TopCV),Tester,Công ty D,Hà Nội,,1 năm,,https://example.test/4,không-rõ",
]


def _csv(tmp_path, lines, name="lo.csv"):
    path = tmp_path / name
    path.write_text("\n".join([HEADER, *lines]) + "\n", encoding="utf-8")
    return path


def test_valid_rows_are_stored_and_bad_rows_are_reported(tmp_path):
    store = tmp_path / "batches"
    result = import_batch(_csv(tmp_path, GOOD + BAD), directory=store)
    assert result["status"] == "imported"
    assert (result["rows"], result["accepted"]) == (4, 2)
    assert [error["line"] for error in result["errors"]] == [4, 5]
    assert "thiếu title" in result["errors"][0]["reasons"]
    assert any("salary_text" in reason for reason in result["errors"][1]["reasons"])
    assert any("posted_date" in reason for reason in result["errors"][1]["reasons"])
    (manifest,) = stored_batches(store)
    assert manifest["rows"] == 2 and manifest["sources"] == ["Lô thử (TopCV)"]
    assert load_batch(manifest, store)["title"].tolist() == [
        "Backend Developer Java",
        "Data Engineer",
    ]


def test_importing_the_same_file_twice_does_not_create_a_new_batch(tmp_path):
    store = tmp_path / "batches"
    path = _csv(tmp_path, GOOD)
    first = import_batch(path, directory=store)
    second = import_batch(path, directory=store)
    assert (first["status"], second["status"]) == ("imported", "duplicate")
    assert second["batch"]["id"] == first["batch"]["id"]
    assert len(stored_batches(store)) == 1


def test_stored_batch_is_never_overwritten_and_tampering_is_detected(tmp_path):
    store = tmp_path / "batches"
    manifest = import_batch(_csv(tmp_path, GOOD), directory=store)["batch"]
    stored = store / manifest["id"] / "batch.csv"
    stored.write_text(stored.read_text().replace("Công ty A", "Công ty Z"), encoding="utf-8")
    with pytest.raises(BatchError):
        load_batch(manifest, store)


def test_source_option_fills_files_without_source_column(tmp_path):
    lines = [line.split(",", 1)[1] for line in GOOD]
    path = tmp_path / "no_source.csv"
    path.write_text("\n".join([HEADER.split(",", 1)[1], *lines]) + "\n", encoding="utf-8")
    with pytest.raises(BatchError, match="source"):
        import_batch(path, directory=tmp_path / "b")
    result = import_batch(path, source="Lô quản trị", directory=tmp_path / "b")
    assert result["batch"]["sources"] == ["Lô quản trị"]


def test_cli_imports_batch_and_fails_when_nothing_is_accepted(tmp_path):
    src = Path(__file__).parents[1] / "src"
    env = {"PYTHONPATH": str(src), "PATH": "/usr/bin:/bin"}

    def run(path):
        command = [sys.executable, "-m", "career_market", "import-batch", str(path)]
        command += ["--batches-dir", str(tmp_path / "b")]
        return subprocess.run(command, capture_output=True, text=True, env=env, check=False)

    ok = run(_csv(tmp_path, GOOD))
    assert ok.returncode == 0, ok.stderr
    assert json.loads(ok.stdout)["accepted"] == 2
    bad = run(_csv(tmp_path, BAD, "bad.csv"))
    assert bad.returncode == 1
    assert json.loads(bad.stdout)["status"] == "rejected"
