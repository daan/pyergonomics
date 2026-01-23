# Importing from Stereolabs ZED Camera

The ZED importer allows you to extract body tracking data from Stereolabs ZED camera recordings (SVO2 files).

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
| `extract_frames` | bool | True | Extract video frames to disk |
| `output_dir` | str | None | Output directory for extracted frames (required if extract_frames=True) |

## Output

The importer returns a `ProjectSettings` object with:
- Frame count and FPS from the recording
- Video dimensions (width, height)
- Skeleton type matching the body format
- Tracker with per-frame body tracking data including:
  - 3D keypoints (in meters, Z-up coordinate system)
  - 2D keypoints (pixel coordinates)
  - Bounding boxes
  - Person IDs for multi-person tracking
