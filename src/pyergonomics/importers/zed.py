"""
Stereolabs ZED camera importer.

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


def from_zed(
    svo_file,
    body_format=BodyFormat.BODY_34,
    detection_confidence=40,
    extract_frames=True,
    output_dir=None,
    set_floor_as_origin=True,
):
    """
    Create a ProjectSettings from a ZED SVO2 file with body tracking.

    Args:
        svo_file: Path to the SVO2 file.
        body_format: Body format to use (BodyFormat.BODY_18 or BodyFormat.BODY_34).
        detection_confidence: Detection confidence threshold (0-100). Default 40.
        extract_frames: If True, extract video frames to output_dir/frames/.
        output_dir: Directory for extracted frames. Required if extract_frames=True.
        set_floor_as_origin: If True (default), set floor plane as coordinate origin.

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
        width = camera_info.camera_configuration.resolution.width
        height = camera_info.camera_configuration.resolution.height

        # Enable positional tracking (required for body tracking)
        positional_tracking_params = sl.PositionalTrackingParameters()
        positional_tracking_params.set_as_static = True
        if set_floor_as_origin:
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

                        data["keypoints_3d"].append(body.keypoint.tolist())
                        data["keypoints_2d"].append(body.keypoint_2d.tolist())

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

    # Only set video dimensions if frames were extracted
    if extract_frames:
        settings.width = width
        settings.height = height

    return settings
