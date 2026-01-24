"""ZED body tracking worker that runs in a separate thread."""

from PySide6.QtCore import QObject, QThread, Signal
import pyzed.sl as sl


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
                 svo_path: str = None,
                 body_format=sl.BODY_FORMAT.BODY_34,
                 enable_body_fitting: bool = True,
                 skeleton_smoothing: float = 0.5,
                 parent=None):
        super().__init__(parent)
        self.skeleton_provider = skeleton_provider
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

            # Set bone connections
            bones = get_bones(self.body_format)
            self.skeleton_provider.setBoneConnections(bones)

            bodies = sl.Bodies()
            self._running = True

            while self._running:
                grab_status = zed.grab()

                if grab_status == sl.ERROR_CODE.SUCCESS:
                    zed.retrieve_bodies(bodies, body_runtime_param)

                    skeletons = []
                    for body in bodies.body_list:
                        if body.tracking_state == sl.OBJECT_TRACKING_STATE.OK:
                            # Convert to list of lists for QML compatibility
                            keypoints = body.keypoint.tolist()
                            skeletons.append({
                                "personId": int(body.id),
                                "keypoints_3d": keypoints
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
