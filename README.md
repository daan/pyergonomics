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

### Command line

Initialize a project using a bvh file:

```bash
init-project --bvh <path to bvh file> new_project
```

Note that the bvh file is not copied into the project.

### Python API

```python
from pyergonomics import ProjectSettings, add_pose_assessment_columns
from pyergonomics.importers import from_bvh

# Option A: Load from BVH file (in-memory, no disk writes)
settings = from_bvh("path/to/motion.bvh", unit="mm")

# Option B: Load from existing project folder
settings = ProjectSettings("path/to/project")

# Access tracker and skeleton
tracker = settings.tracker
skeleton = settings.pose_skeleton

# Run pose assessment
add_pose_assessment_columns(tracker, skeleton)

# Get metrics for a person
person_id = tracker.get_person_ids()[0]
metrics = tracker.get_pose_metrics_for_person(person_id)

# Optionally persist in-memory project to disk
settings.persist("path/to/save")
```

## units

Pyergonomics uses a right-handed z-up coordinate system and works with meters.