import pytest
import numpy as np
import polars as pl
from pathlib import Path


@pytest.fixture
def sample_keypoints_3d():
    """Generate sample 3D keypoints for testing (17 joints, typical pose)."""
    # Standing pose with arms down, approximate COCO-like skeleton
    return np.array([
        [0.0, 0.0, 1.7],    # 0: nose/head
        [0.0, 0.0, 1.6],    # 1: neck
        [-0.2, 0.0, 1.5],   # 2: right shoulder
        [-0.4, 0.0, 1.3],   # 3: right elbow
        [-0.5, 0.0, 1.1],   # 4: right wrist
        [0.2, 0.0, 1.5],    # 5: left shoulder
        [0.4, 0.0, 1.3],    # 6: left elbow
        [0.5, 0.0, 1.1],    # 7: left wrist
        [-0.1, 0.0, 1.0],   # 8: right hip
        [-0.1, 0.0, 0.5],   # 9: right knee
        [-0.1, 0.0, 0.0],   # 10: right ankle
        [0.1, 0.0, 1.0],    # 11: left hip
        [0.1, 0.0, 0.5],    # 12: left knee
        [0.1, 0.0, 0.0],    # 13: left ankle
        [0.0, 0.0, 1.65],   # 14: right eye
        [0.0, 0.0, 1.65],   # 15: left eye
        [0.0, 0.0, 1.6],    # 16: right ear
    ])


@pytest.fixture
def sample_tracking_df(sample_keypoints_3d):
    """Create a sample tracking DataFrame with multiple frames and persons."""
    frames = []
    for person_id in [1, 2]:
        for frame in range(10):
            # Slightly modify keypoints per frame for variation
            kp = sample_keypoints_3d.copy()
            kp[:, 0] += person_id * 2  # Offset by person
            frames.append({
                "person": person_id,
                "frame": frame,
                "keypoints_3d": kp.tolist(),
            })
    return pl.DataFrame(frames)


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def examples_dir(project_root):
    """Return the examples directory."""
    return project_root / "examples"


@pytest.fixture
def notebooks_dir(examples_dir):
    """Return the notebooks directory."""
    return examples_dir / "notebooks"
