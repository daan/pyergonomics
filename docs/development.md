# Development

This document describes development procedures for working on `pyergonomics`.

## Cleaning Notebooks Before Committing

Jupyter notebooks contain output cells and metadata that can clutter git history and cause merge conflicts. Before committing notebooks to git, clean them using `nb-clean`.

### Install Development Dependencies

Make sure you have the dev dependencies installed:

```bash
uv sync
```

### Clean a Notebook

To clean a single notebook before committing:

```bash
nb-clean clean path/to/notebook.ipynb
```

This removes:
- Cell outputs
- Cell execution counts
- Cell metadata

### Clean All Notebooks

To clean all notebooks in the repository:

```bash
nb-clean clean .
```

### Set Up Git Filter (Recommended)

For automatic cleaning on commit, set up a git filter:

```bash
nb-clean add-filter
```

This configures git to automatically clean notebooks when staging them for commit. The filter is added to your local `.git/config`.

To remove the filter:

```bash
nb-clean remove-filter
```

### Verify a Notebook is Clean

To check if a notebook is clean without modifying it:

```bash
nb-clean check path/to/notebook.ipynb
```

This exits with a non-zero status if the notebook contains outputs or metadata that should be cleaned.
