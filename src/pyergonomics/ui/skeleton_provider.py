from PySide6.QtCore import QObject, Property, Signal


class SkeletonProvider(QObject):
    skeletonsChanged = Signal()
    boneConnectionsChanged = Signal()

    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self._app_state = app_state
        
        self._app_state.currentFrameChanged.connect(self.skeletonsChanged)
        self._app_state.projectLoaded.connect(self.boneConnectionsChanged)
        self._app_state.projectLoaded.connect(self.skeletonsChanged)

    @Property("QVariantList", notify=skeletonsChanged)
    def skeletons(self):
        if not self._app_state.config:
            return []
        tracker = self._app_state.config.tracker
        if not tracker or not tracker.has_data:
            return []

        frame_index = self._app_state.currentFrame
        # Use the tracker's method to get keypoints
        keypoints_map = tracker.get_keypoints_at_frame(frame_index)
        
        frame_skeletons = []
        for person_id, kps in keypoints_map.items():
            frame_skeletons.append({
                "personId": person_id,
                "keypoints_3d": kps
            })
            
        return frame_skeletons

    @Property("QVariantList", notify=boneConnectionsChanged)
    def boneConnections(self):
        if not self._app_state.config:
            return []
        skeleton = self._app_state.config.pose_skeleton

        if skeleton:
            # Assuming skeleton.bones is a list of [start_index, end_index]
            return list(skeleton.bones)
        return []
