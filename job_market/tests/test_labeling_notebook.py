"""Notebook gán nhãn phải chạy hết từ đầu đến cuối và được commit không kèm output (#80)."""

from pathlib import Path

import nbformat
from nbclient import NotebookClient

NOTEBOOK = Path(__file__).parents[1] / "notebooks/gan_nhan_du_lieu.ipynb"


def test_notebook_is_committed_without_outputs():
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    code = [cell for cell in notebook.cells if cell.cell_type == "code"]
    assert code
    assert all(not cell.outputs and cell.execution_count is None for cell in code)


def test_notebook_runs_end_to_end():
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    NotebookClient(
        notebook,
        timeout=600,
        kernel_name="python3",
        resources={"metadata": {"path": str(NOTEBOOK.parent)}},
    ).execute()
    errors = [
        output
        for cell in notebook.cells
        if cell.cell_type == "code"
        for output in cell.outputs
        if output.output_type == "error"
    ]
    assert not errors
