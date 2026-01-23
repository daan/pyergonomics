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

Import a BVH file:

```bash
pye-import-bvh <bvh_file> <destination>

# Specify unit (m, cm, mm, inch) - default is m
pye-import-bvh motion.bvh myproject --unit cm

# Skip first frame (useful for BVH files with T-pose at origin)
pye-import-bvh xsens.bvh myproject --unit cm --ignore-first-frame
```

Import a video file:

```bash
pye-import-video <video_file> <destination>
```

Import a Stereolabs ZED SVO2 file (requires pyzed, see [docs/zed.md](docs/zed.md)):

```bash
pye-import-zed <svo_file> <destination>

# Skip frame extraction (frames extracted by default)
pye-import-zed recording.svo2 myproject --no-extract-frames

# Use BODY_18 format instead of BODY_34
pye-import-zed recording.svo2 myproject --body-format body_18
```

Open the editor:

```bash
pye-editor <project_folder>
```

### Python API

```python
from pyergonomics import ProjectSettings, add_pose_assessment_columns
from pyergonomics.importers import from_bvh, Unit

# Option A: Load from BVH file (in-memory, no disk writes)
settings = from_bvh("path/to/motion.bvh", unit=Unit.MM)

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