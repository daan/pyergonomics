"""ZED body tracking worker that runs in a separate thread."""

import math
from PySide6.QtCore import QObject, QThread, Signal
import pyzed.sl as sl
import numpy as np


def create_floor_transform(floor_plane_eq):
    """Create rotation and translation to transform camera coords to world coords.

    World frame: z-up (floor normal), y-forward (camera direction projected on floor).

    Args:
        floor_plane_eq: [a, b, c, d] where ax + by + cz + d = 0

    Returns:
        R: 3x3 rotation matrix
        t: 3-element translation vector
    """
    a, b, c, d = floor_plane_eq
    n = np.array([a, b, c])
    n = n / np.linalg.norm(n)  # floor normal in camera coords

    # z_world is the floor normal
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

    # Rotation matrix: rows are world basis vectors in camera coords
    # p_world = R @ p_camera
    R = np.vstack([x_world, y_world, z_world])

    # After rotation, floor points have z = n · p = -d
    # Translate by +d to shift floor to z=0
    t = np.array([0, 0, d])

    return R, t


def transform_keypoints(keypoints, R, t):
    """Transform keypoints from camera to world coordinates."""
    return (R @ keypoints.T).T + t


def rotation_matrix_to_quaternion(R):
    """Convert 3x3 rotation matrix to quaternion [w, x, y, z]."""
    # Using Shepperd's method for numerical stability
    trace = R[0, 0] + R[1, 1] + R[2, 2]

    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (R[2, 1] - R[1, 2]) * s
        y = (R[0, 2] - R[2, 0]) * s
        z = (R[1, 0] - R[0, 1]) * s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s

    return [float(w), float(x), float(y), float(z)]


def get_bones(body_format):
    """Get bone connections for a body format."""
    if body_format == sl.BODY_FORMAT.BODY_34:
        return [
            (0, 1), (1, 2), (2, 3), (3, 26),
            (2, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (7, 10),
            (2, 11), (11, 12), (12, 13), (13, 14), (14, 15), (15, 16), (14, 17),
            (0, 18), (18, 19), (19, 20), (20, 21), (20, 32),
            (0, 22), (22, 23), (23, 24), (24, 25), (24, 33),
            (26, 27), (26, 28), (26, 30), (28, 29), (30, 31),
        ]
    else:
        # BODY_18
        return [
            (0, 1), (0, 14), (0, 15), (14, 16), (15, 17),
            (1, 2), (1, 5), (2, 8), (5, 11), (8, 11),
            (2, 3), (3, 4),
            (5, 6), (6, 7),
            (8, 9), (9, 10),
            (11, 12), (12, 13),
        ]


class ZedBodyTracker(QObject):
    """Worker object that runs ZED body tracking in a thread."""

    # Emitted on errors
    error = Signal(str)

    # Emitted when playback finishes (SVO only)
    finished = Signal()

    def __init__(self,
                 skeleton_provider,
                 frame_provider=None,
                 svo_path: str = None,
                 body_format=sl.BODY_FORMAT.BODY_34,
                 enable_body_fitting: bool = True,
                 skeleton_smoothing: float = 0.5,
                 parent=None):
        super().__init__(parent)
        self.skeleton_provider = skeleton_provider
        self.frame_provider = frame_provider
        self.svo_path = svo_path
        self.body_format = body_format
        self.enable_body_fitting = enable_body_fitting
        self.skeleton_smoothing = skeleton_smoothing
        self._running = False

    def run(self):
        """Main tracking loop - call this from a thread."""
        zed = sl.Camera()

        # Initialize
        init_params = sl.InitParameters()
        if self.svo_path:
            init_params.set_from_svo_file(self.svo_path)
        init_params.coordinate_units = sl.UNIT.METER
        init_params.depth_mode = sl.DEPTH_MODE.NEURAL
        init_params.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Z_UP

        err = zed.open(init_params)
        if err != sl.ERROR_CODE.SUCCESS:
            self.error.emit(f"Failed to open camera: {err}")
            return

        try:
            # Enable positional tracking
            positional_tracking_params = sl.PositionalTrackingParameters()
            positional_tracking_params.set_as_static = True
            positional_tracking_params.set_floor_as_origin = True
            zed.enable_positional_tracking(positional_tracking_params)

            # Enable body tracking
            body_param = sl.BodyTrackingParameters()
            body_param.enable_tracking = True
            body_param.detection_model = sl.BODY_TRACKING_MODEL.HUMAN_BODY_ACCURATE
            body_param.body_format = self.body_format
            body_param.enable_body_fitting = self.enable_body_fitting
            zed.enable_body_tracking(body_param)

            body_runtime_param = sl.BodyTrackingRuntimeParameters()
            body_runtime_param.detection_confidence_threshold = 40
            body_runtime_param.skeleton_smoothing = self.skeleton_smoothing

            # Detect floor plane for coordinate transform
            # Need to grab a few frames first for floor detection
            for _ in range(30):
                if zed.grab() != sl.ERROR_CODE.SUCCESS:
                    break

            floor_transform = None
            plane = sl.Plane()
            reset_transform = sl.Transform()
            if zed.find_floor_plane(plane, reset_transform) == sl.ERROR_CODE.SUCCESS:
                floor_plane_eq = plane.get_plane_equation()
                R, t = create_floor_transform(floor_plane_eq)
                floor_transform = (R, t)
                print(f"Floor plane detected: normal=({floor_plane_eq[0]:.3f}, {floor_plane_eq[1]:.3f}, {floor_plane_eq[2]:.3f}), d={floor_plane_eq[3]:.3f}")
            else:
                print("Floor plane NOT detected, using camera coordinates")

            # Reset to start after floor detection
            if self.svo_path:
                zed.set_svo_position(0)

            # Set bone connections
            bones = get_bones(self.body_format)
            self.skeleton_provider.setBoneConnections(bones)

            # Get camera intrinsics and compute FOV
            camera_info = zed.get_camera_information()
            calib = camera_info.camera_configuration.calibration_parameters
            left_cam = calib.left_cam

            # Compute vertical FOV from fy and image height
            # fov = 2 * atan(height / (2 * fy))
            img_height = left_cam.image_size.height
            img_width = left_cam.image_size.width
            fy = left_cam.fy
            fov_v = 2 * math.degrees(math.atan(img_height / (2 * fy)))
            aspect = img_width / img_height

            # Get camera position and orientation in world coordinates
            # Camera is at origin in camera coordinates, transform to world
            if floor_transform is not None:
                R, t = floor_transform
                # Camera origin (0,0,0) in camera coords -> world coords
                camera_pos_world = t  # R @ [0,0,0] + t = t
                camera_position = [float(camera_pos_world[0]), float(camera_pos_world[1]), float(camera_pos_world[2])]
                # Convert rotation matrix to quaternion for QML
                floor_quat = rotation_matrix_to_quaternion(R)
                self.skeleton_provider.setFloorRotation(floor_quat)
                print(f"Floor rotation quaternion: {floor_quat}")
            else:
                # Fallback: get from positional tracking
                camera_pose = sl.Pose()
                camera_position = [0.0, 0.0, 1.0]  # Default: 1m height
                self.skeleton_provider.setFloorRotation([1.0, 0.0, 0.0, 0.0])  # Identity
                if zed.grab() == sl.ERROR_CODE.SUCCESS:
                    zed.get_position(camera_pose, sl.REFERENCE_FRAME.WORLD)
                    translation = camera_pose.get_translation().get()
                    camera_position = [float(translation[0]), float(translation[1]), float(translation[2])]
                    if self.svo_path:
                        zed.set_svo_position(0)

            # Send full intrinsics and camera info
            self.skeleton_provider.setCameraIntrinsics(
                left_cam.fx, left_cam.fy,
                left_cam.cx, left_cam.cy,
                img_width, img_height
            )
            self.skeleton_provider.setCameraInfo(fov_v, aspect, camera_position)

            # Debug: print intrinsics and verify they're reasonable
            print(f"Camera FOV: {fov_v:.1f}°, Aspect: {aspect:.2f}, Position: {camera_position}")
            print(f"Camera intrinsics: fx={left_cam.fx:.1f}, fy={left_cam.fy:.1f}, cx={left_cam.cx:.1f}, cy={left_cam.cy:.1f}")
            print(f"Image size: {img_width}x{img_height}")
            print(f"Principal point offset from center: dx={left_cam.cx - img_width/2:.1f}, dy={left_cam.cy - img_height/2:.1f}")
            print(f"Distortion coeffs: {left_cam.disto[:5]}")

            bodies = sl.Bodies()
            image = sl.Mat()
            self._running = True

            while self._running:
                # Check if paused
                if self.skeleton_provider.paused:
                    import time
                    time.sleep(0.03)  # ~30fps check rate
                    continue

                grab_status = zed.grab()

                if grab_status == sl.ERROR_CODE.SUCCESS:
                    zed.retrieve_bodies(bodies, body_runtime_param)

                    # Capture video frame for QML
                    if self.frame_provider is not None:
                        zed.retrieve_image(image, sl.VIEW.LEFT, sl.MEM.CPU)
                        self.frame_provider.setFrame(image.get_data())

                    skeletons = []
                    for body in bodies.body_list:
                        if body.tracking_state == sl.OBJECT_TRACKING_STATE.OK:
                            keypoints = body.keypoint
                            # Transform to world coordinates if floor was detected
                            if floor_transform is not None:
                                R, t = floor_transform
                                keypoints = transform_keypoints(keypoints, R, t)
                            # Convert to list of lists for QML compatibility
                            # Include 2D keypoints for debug overlay comparison
                            skeletons.append({
                                "personId": int(body.id),
                                "keypoints_3d": keypoints.tolist(),
                                "keypoints_2d": body.keypoint_2d.tolist()
                            })

                    # Update provider directly (thread-safe)
                    self.skeleton_provider.setSkeletons(skeletons)

                elif grab_status == sl.ERROR_CODE.END_OF_SVOFILE_REACHED:
                    self.finished.emit()
                    break

        finally:
            zed.close()

    def stop(self):
        """Stop the tracking loop."""
        self._running = False


class ZedThread(QThread):
    """Thread wrapper for ZedBodyTracker."""

    def __init__(self, tracker: ZedBodyTracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker

    def run(self):
        self.tracker.run()
