"""
Stereolabs ZED camera importer.

Assumes a static camera. Detects the floor plane and transforms 3D keypoints
into world coordinates (z-up, floor at z=0). Stores the rectified left camera
image, camera intrinsics, and extrinsics for 3D-to-2D projection.

Requires the pyzed wheel which must be downloaded from Stereolabs website.
See docs/zed.md for installation instructions.
"""

import numpy as np
import polars as pl
from pathlib import Path
from tqdm import tqdm

try:
    import pyzed.sl as sl
    HAS_PYZED = True
except ImportError:
    HAS_PYZED = False


class BodyFormat:
    """Available ZED body tracking formats."""
    BODY_18 = "body_18"
    BODY_34 = "body_34"


def _create_floor_transform(floor_plane_eq):
    """Create rotation and translation to transform camera coords to world coords.

    World frame: z-up (floor normal), y-forward (camera direction projected
    on floor), x-right. Floor is at z=0.

    Args:
        floor_plane_eq: [a, b, c, d] where ax + by + cz + d = 0

    Returns:
        R: 3x3 rotation matrix (p_world = R @ p_camera + t)
        t: 3-element translation vector
    """
    a, b, c, d = floor_plane_eq
    n = np.array([a, b, c])
    n = n / np.linalg.norm(n)

    z_world = n

    # Camera forward in ZED RIGHT_HANDED_Z_UP is (0, 1, 0)
    cam_forward = np.array([0, 1, 0])

    # y_world: camera forward projected onto floor plane, normalized
    y_world = cam_forward - np.dot(cam_forward, z_world) * z_world
    y_norm = np.linalg.norm(y_world)

    if y_norm < 1e-6:
        # Camera looking straight up/down, use camera right as fallback
        cam_right = np.array([1, 0, 0])
        x_world = cam_right - np.dot(cam_right, z_world) * z_world
        x_world = x_world / np.linalg.norm(x_world)
        y_world = np.cross(z_world, x_world)
    else:
        y_world = y_world / y_norm
        x_world = np.cross(y_world, z_world)

    R = np.vstack([x_world, y_world, z_world])
    t = np.array([0, 0, d])

    return R, t


def _transform_keypoints(keypoints, R, t):
    """Transform keypoints from camera to world coordinates."""
    return (R @ keypoints.T).T + t


def from_zed(
    svo_file,
    body_format=BodyFormat.BODY_34,
    detection_confidence=40,
    extract_frames=True,
    output_dir=None,
):
    """
    Create a ProjectSettings from a ZED SVO2 file with body tracking.

    Assumes a static camera. Detects the floor plane to establish world
    coordinates (z-up, floor at z=0). Extracts rectified left camera frames.

    Args:
        svo_file: Path to the SVO2 file.
        body_format: Body format to use (BodyFormat.BODY_18 or BodyFormat.BODY_34).
        detection_confidence: Detection confidence threshold (0-100). Default 40.
        extract_frames: If True, extract video frames to output_dir/frames/.
        output_dir: Directory for extracted frames. Required if extract_frames=True.

    Returns:
        ProjectSettings: In-memory project with tracking data loaded.

    Raises:
        ImportError: If pyzed is not installed.
        FileNotFoundError: If SVO file doesn't exist.
        RuntimeError: If ZED SDK fails to open the file.
    """
    if not HAS_PYZED:
        raise ImportError(
            "pyzed is required for ZED import. "
            "Download the wheel from https://www.stereolabs.com/developers/release "
            "and install it with: pip install pyzed-*.whl"
        )

    from ..project_settings import ProjectSettings
    from ..tracker import Tracker

    svo_path = Path(svo_file).resolve()
    if not svo_path.is_file():
        raise FileNotFoundError(f"SVO file not found: {svo_file}")

    if extract_frames:
        if output_dir is None:
            raise ValueError("output_dir is required when extract_frames=True")
        import cv2
        import os
        frames_dir = Path(output_dir) / "frames"
        os.makedirs(frames_dir, exist_ok=True)

    # Initialize ZED camera
    zed = sl.Camera()

    init_params = sl.InitParameters()
    init_params.set_from_svo_file(str(svo_path))
    init_params.coordinate_units = sl.UNIT.METER
    init_params.depth_mode = sl.DEPTH_MODE.NEURAL
    init_params.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Z_UP

    err = zed.open(init_params)
    if err != sl.ERROR_CODE.SUCCESS:
        zed.close()
        raise RuntimeError(f"Failed to open SVO file: {err}")

    try:
        camera_info = zed.get_camera_information()
        svo_frame_count = zed.get_svo_number_of_frames()
        fps = camera_info.camera_configuration.fps
        calib = camera_info.camera_configuration.calibration_parameters
        left_cam = calib.left_cam
        img_width = left_cam.image_size.width
        img_height = left_cam.image_size.height

        # Camera intrinsics (rectified left camera)
        fx, fy = float(left_cam.fx), float(left_cam.fy)
        cx, cy = float(left_cam.cx), float(left_cam.cy)

        # Enable positional tracking (required for body tracking)
        positional_tracking_params = sl.PositionalTrackingParameters()
        positional_tracking_params.set_as_static = True
        positional_tracking_params.set_floor_as_origin = True
        zed.enable_positional_tracking(positional_tracking_params)

        # Configure body tracking
        body_param = sl.BodyTrackingParameters()
        body_param.enable_tracking = True
        body_param.detection_model = sl.BODY_TRACKING_MODEL.HUMAN_BODY_ACCURATE

        if body_format == BodyFormat.BODY_18:
            body_param.body_format = sl.BODY_FORMAT.BODY_18
            skeleton_name = "coco17"  # BODY_18 is COCO-compatible
        else:
            body_param.body_format = sl.BODY_FORMAT.BODY_34
            skeleton_name = "stereolabs_body34"

        zed.enable_body_tracking(body_param)

        body_runtime_param = sl.BodyTrackingRuntimeParameters()
        body_runtime_param.detection_confidence_threshold = detection_confidence

        # Detect floor plane for world coordinate transform
        # Need to grab a few frames first for reliable floor detection
        for _ in range(30):
            if zed.grab() != sl.ERROR_CODE.SUCCESS:
                break

        floor_transform = None
        floor_plane_eq = None
        plane = sl.Plane()
        reset_transform = sl.Transform()
        if zed.find_floor_plane(plane, reset_transform) == sl.ERROR_CODE.SUCCESS:
            floor_plane_eq = [float(v) for v in plane.get_plane_equation()]
            R, t = _create_floor_transform(floor_plane_eq)
            floor_transform = (R, t)
            print(f"Floor plane detected: normal=({floor_plane_eq[0]:.3f}, "
                  f"{floor_plane_eq[1]:.3f}, {floor_plane_eq[2]:.3f}), "
                  f"d={floor_plane_eq[3]:.3f}")
        else:
            print("WARNING: Floor plane not detected, keypoints stored in camera coordinates")

        # Reset to start after floor detection
        zed.set_svo_position(0)

        # Data collection
        data = {
            "frame": [],
            "person": [],
            "x": [],
            "y": [],
            "w": [],
            "h": [],
            "keypoints_3d": [],
            "keypoints_2d": [],
            "keypoint_confidence": [],
        }

        image = sl.Mat()
        bodies = sl.Bodies()
        frame_idx = 0

        with tqdm(total=svo_frame_count, desc="Processing ZED SVO") as pbar:
            while zed.grab() == sl.ERROR_CODE.SUCCESS:
                zed.retrieve_bodies(bodies, body_runtime_param)

                if extract_frames:
                    zed.retrieve_image(image, sl.VIEW.LEFT, sl.MEM.CPU)
                    img_data = image.get_data()
                    cv2.imwrite(str(frames_dir / f"{frame_idx:06d}.png"), img_data)

                for body in bodies.body_list:
                    if body.tracking_state == sl.OBJECT_TRACKING_STATE.OK:
                        data["frame"].append(frame_idx)
                        data["person"].append(int(body.id))

                        bb = body.bounding_box_2d
                        data["x"].append(float(bb[0][0]))
                        data["y"].append(float(bb[0][1]))
                        data["w"].append(float(bb[1][0] - bb[0][0]))
                        data["h"].append(float(bb[3][1] - bb[0][1]))

                        # Transform 3D keypoints to world coordinates
                        keypoints_3d = body.keypoint
                        if floor_transform is not None:
                            R, t_vec = floor_transform
                            keypoints_3d = _transform_keypoints(keypoints_3d, R, t_vec)
                        data["keypoints_3d"].append(keypoints_3d.tolist())

                        data["keypoints_2d"].append(body.keypoint_2d.tolist())
                        data["keypoint_confidence"].append(body.keypoint_confidence.tolist())

                frame_idx += 1
                pbar.update(1)

            # Update progress bar if we finished early
            if pbar.n < pbar.total:
                pbar.total = pbar.n

    finally:
        zed.close()

    # Create DataFrame
    df = pl.DataFrame(data)

    # Create in-memory ProjectSettings
    settings = ProjectSettings()
    settings.number_of_frames = frame_idx
    settings.frames_per_second = fps
    settings.pose_skeleton_name = skeleton_name
    settings._tracker = Tracker.from_dataframe(df)

    # Camera intrinsics (rectified left camera)
    settings.data["camera"] = {
        "fx": fx,
        "fy": fy,
        "cx": cx,
        "cy": cy,
        "image_width": img_width,
        "image_height": img_height,
    }

    # Camera extrinsics (floor transform: camera → world)
    if floor_transform is not None:
        R, t_vec = floor_transform
        settings.data["camera"]["extrinsics"] = {
            "rotation": R.tolist(),
            "translation": t_vec.tolist(),
            "floor_plane": floor_plane_eq,
        }

    return settings
