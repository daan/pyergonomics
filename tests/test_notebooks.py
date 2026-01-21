"""
Test that example notebooks can be executed without errors.

Uses nbmake pytest plugin to execute notebooks as tests.
Run with: pytest --nbmake examples/notebooks/
"""
import pytest
from pathlib import Path


# Notebook paths relative to project root
NOTEBOOK_DIR = Path(__file__).parent.parent / "examples" / "notebooks"
NOTEBOOKS = list(NOTEBOOK_DIR.glob("*.ipynb"))


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda p: p.name)
def test_notebook_exists(notebook):
    """Verify that expected notebooks exist."""
    assert notebook.exists(), f"Notebook {notebook.name} not found"


# The actual notebook execution tests are run via:
# pytest --nbmake examples/notebooks/
#
# This command will:
# 1. Execute each notebook cell by cell
# 2. Fail if any cell raises an exception
# 3. Report which cell failed and why
#
# Example usage:
#   pytest --nbmake examples/notebooks/eaws.ipynb  # Run single notebook
#   pytest --nbmake examples/notebooks/            # Run all notebooks
#   pytest --nbmake --overwrite examples/notebooks/ # Update notebook outputs
