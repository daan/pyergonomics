import numpy as np
from bvhtoolbox import BvhTree
import transforms3d as t3d
from pathlib import Path
import polars as pl
from tqdm import tqdm


def _compute_local_transform(bvh_tree, joint_name, frame):
    """Compute local transform for a joint at a given frame."""
    channels = bvh_tree.joint_channels(joint_name)
    values = bvh_tree.frame_joint_channels(frame, joint_name, channels)

    pos = np.zeros(3)
    rot = np.eye(3)

    for ch, val in zip(channels, values):
        rad = np.radians(val)
        if ch == 'Xposition': pos[0] = val
        elif ch == 'Yposition': pos[1] = val
        elif ch == 'Zposition': pos[2] = val
        elif ch == 'Xrotation': rot = rot @ t3d.euler.euler2mat(rad, 0, 0, 'sxyz')
        elif ch == 'Yrotation': rot = rot @ t3d.euler.euler2mat(0, rad, 0, 'sxyz')
        elif ch == 'Zrotation': rot = rot @ t3d.euler.euler2mat(0, 0, rad, 'sxyz')

    return t3d.affines.compose(pos, rot, np.ones(3))


def _world_joint_positions(bvh_tree, scale=1.0):
    """Compute world positions for all joints across all frames."""
    joints = list(bvh_tree.get_joints())
    nframes = bvh_tree.nframes

    bvh_dict = {}

    for frame in tqdm(range(nframes), desc="Loading BVH"):
        transforms = {}  # joint_name -> 4x4 matrix

        for joint in joints:
            local = _compute_local_transform(bvh_tree, joint.name, frame)

            # Get parent name safely
            parent = joint.parent
            parent_name = parent.value[1] if parent and len(parent.value) > 1 else None

            if parent_name and parent_name in transforms:
                # Child joint: use offset as translation
                offset = [float(o) for o in joint['OFFSET']]
                local[:3, 3] = offset
                world = transforms[parent_name] @ local
            else:
                # Root joint: use position from channels
                world = local

            transforms[joint.name] = world

            # Store position (will accumulate across frames)
            if joint.name not in bvh_dict:
                bvh_dict[joint.name] = []

            # Convert Y-up to Z-up: (x, y, z) -> (x, -z, y), and scale
            p = world[:3, 3] * scale
            bvh_dict[joint.name].append([p[0], -p[2], p[1]])

    # Convert lists to numpy arrays
    for joint_name in bvh_dict:
        bvh_dict[joint_name] = np.array(bvh_dict[joint_name])

    return bvh_dict


def from_bvh(bvh_file, unit=None, ignore_first_frame=False):
    """
    Create an in-memory ProjectSettings from a BVH file.

    Args:
        bvh_file: Path to the BVH file.
        unit: Unit of the BVH position data (Unit.M, Unit.CM, etc.). Defaults to Unit.M.
        ignore_first_frame: Skip the first frame (useful for files with T-pose at origin).

    Returns:
        ProjectSettings: In-memory project with tracking data loaded.
    """
    from . import Unit
    from ..project_settings import ProjectSettings
    from ..tracker import Tracker

    if unit is None:
        unit = Unit.M

    scale = unit.value

    bvh_path = Path(bvh_file).resolve()
    if not bvh_path.is_file():
        raise FileNotFoundError(f"BVH file not found: {bvh_file}")

    with open(bvh_path) as f:
        bvh = BvhTree(f.read())

    world_coordinates = _world_joint_positions(bvh, scale=scale)

    fps = 1.0 / bvh.frame_time
    frame_count = bvh.nframes

    if ignore_first_frame:
        for joint_name in world_coordinates:
            world_coordinates[joint_name] = world_coordinates[joint_name][1:]
        frame_count -= 1

    # Prepare data for DataFrame
    joint_names = list(world_coordinates.keys())
    keypoints_3d_per_frame = []
    for i in range(frame_count):
        frame_keypoints = []
        for joint_name in joint_names:
            frame_keypoints.append(world_coordinates[joint_name][i].tolist())
        keypoints_3d_per_frame.append(frame_keypoints)

    df = pl.DataFrame(
        {
            "person": [1] * frame_count,
            "frame": range(frame_count),
            "keypoints_3d": keypoints_3d_per_frame,
        }
    )

    # Auto-detect skeleton type from joint names
    from pose_skeletons import detect_skeleton
    joint_names = list(world_coordinates.keys())
    skeleton_name = detect_skeleton(joint_names)
    if skeleton_name is None:
        raise ValueError(f"Could not auto-detect skeleton type from joints: {joint_names}")

    # Create in-memory ProjectSettings and use setters
    settings = ProjectSettings()
    settings.number_of_frames = frame_count
    settings.frames_per_second = fps
    settings.pose_skeleton_name = skeleton_name
    settings._tracker = Tracker.from_dataframe(df)

    return settings


