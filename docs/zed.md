# Importing from Stereolabs ZED Camera

The ZED importer extracts body tracking data from Stereolabs ZED camera recordings (SVO2 files). It assumes a **static camera**.

The importer detects the floor plane and transforms all 3D keypoints into world coordinates (z-up, floor at z=0). Camera intrinsics and extrinsics are saved so that 3D content can be projected back onto the video frames. Video frames (rectified left camera) can optionally be extracted to disk.

## Requirements

The ZED SDK's Python bindings (`pyzed`) are required but not included as a dependency because the wheel must be downloaded manually from Stereolabs.

### Installing pyzed

1. Go to the [Stereolabs Developers Portal](https://www.stereolabs.com/developers/release)
2. Download the appropriate wheel for your platform and Python version (e.g., `pyzed-5.0-cp312-cp312-linux_x86_64.whl`)
3. Install the wheel:

```bash
pip install pyzed-5.0-cp312-cp312-linux_x86_64.whl
```

Note: The ZED SDK must also be installed on your system. See the [ZED SDK installation guide](https://www.stereolabs.com/docs/installation/).

## Usage

```python
from pyergonomics.importers import from_zed, BodyFormat

# Basic usage with BODY_34 format (default, extracts frames)
project = from_zed("recording.svo2", output_dir="./output")

# Use BODY_18 format (COCO-compatible)
project = from_zed("recording.svo2", output_dir="./output", body_format=BodyFormat.BODY_18)

# Skip frame extraction (tracking data only)
project = from_zed("recording.svo2", extract_frames=False)

# Adjust detection confidence (0-100)
project = from_zed("recording.svo2", output_dir="./output", detection_confidence=60)
```

## Body Formats

- **BODY_34** (default): 34-joint skeleton with detailed hand and foot tracking. Uses the `stereolabs_body34` skeleton definition.
- **BODY_18**: 18-joint skeleton compatible with COCO format. Uses the `coco17` skeleton definition.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `svo_file` | str | required | Path to the SVO2 file |
| `body_format` | BodyFormat | `BODY_34` | Body tracking format |
| `detection_confidence` | int | 40 | Detection confidence threshold (0-100) |
| `extract_frames` | bool | True | Extract rectified left camera frames to disk (can use significant disk space) |
| `output_dir` | str | None | Output directory for extracted frames (required if extract_frames=True) |

## World Coordinates

The importer detects the floor plane using the ZED SDK's `find_floor_plane()` (after grabbing 30 initial frames for reliable detection). A rotation matrix and translation vector are computed to transform body tracking keypoints from camera coordinates into world coordinates:

- **Z-axis**: Floor normal (up)
- **Y-axis**: Camera forward direction projected onto the floor plane
- **X-axis**: Right (completes the right-handed frame)
- **Origin**: Floor directly below the camera (z=0)

If floor detection fails, keypoints are stored in camera coordinates and a warning is printed.

## Output

The importer returns a `ProjectSettings` object with:
- Frame count and FPS from the recording
- Skeleton type matching the body format
- Camera intrinsics and extrinsics (see below)
- Tracker with per-frame body tracking data including:
  - 3D keypoints in world coordinates (meters, z-up, floor at z=0)
  - 2D keypoints (pixel coordinates in rectified left image)
  - Per-keypoint confidence (0-100)
  - Bounding boxes
  - Person IDs for multi-person tracking

### Camera Data (project.toml)

The `[camera]` section stores intrinsics of the rectified left camera:

```toml
[camera]
fx = 529.28
fy = 529.28
cx = 636.71
cy = 362.42
image_width = 1280
image_height = 720
```

When floor detection succeeds, `[camera.extrinsics]` stores the camera-to-world transform:

```toml
[camera.extrinsics]
rotation = [[r00, r01, r02], [r10, r11, r12], [r20, r21, r22]]
translation = [tx, ty, tz]
floor_plane = [a, b, c, d]
```

- `rotation`: 3x3 rotation matrix (row-major). Transforms camera coordinates to world coordinates: `p_world = R @ p_camera + t`.
- `translation`: Translation vector (meters).
- `floor_plane`: Original floor plane equation `[a, b, c, d]` where `ax + by + cz + d = 0` in camera coordinates.

These can be used to build a projection matrix for overlaying 3D content on video frames (e.g., using a `CustomCamera` in Qt Quick 3D).
