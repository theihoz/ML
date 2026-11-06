"""Các notebook tính năng phải sạch output và chạy hết từ đầu đến cuối."""

from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient

NOTEBOOKS = sorted((Path(__file__).parents[1] / "notebooks").glob("tinh_nang_*.ipynb"))


def test_all_six_feature_notebooks_exist():
    assert len(NOTEBOOKS) == 6
    assert {path.name.split("_")[2] for path in NOTEBOOKS} == set("123456")


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda path: path.stem)
def test_feature_notebook_is_committed_without_outputs(path):
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    code = [cell for cell in notebook.cells if cell.cell_type == "code"]
    assert code
    assert all(not cell.outputs and cell.execution_count is None for cell in code)


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda path: path.stem)
def test_feature_notebook_runs_end_to_end(path):
    notebook = nbformat.read(path, as_version=4)
    NotebookClient(
        notebook,
        timeout=600,
        kernel_name="python3",
        resources={"metadata": {"path": str(path.parent)}},
    ).execute()
    outputs = [
        output for cell in notebook.cells if cell.cell_type == "code" for output in cell.outputs
    ]
    assert not [output for output in outputs if output.output_type == "error"]
    assert any("image/png" in output.get("data", {}) for output in outputs)
