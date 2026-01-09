# pyergonomics



## install

```bash
# Jupyter notebook users
uv sync --extra notebook

# Qt editor users
uv sync --extra qt

# Motion data import (ultralytics, bvh)
uv sync --extra sources

# Development
uv sync --extra dev

# Multiple extras
uv sync --extra qt --extra dev

# Everything
uv sync --all-extras
```


## getting started

Initialize a project using a bvh file

```
init-project --bvh <path to bvh file> new_project
```

note that the bvh file is not copied into the project
