from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Slot, QPointF


class PersonModel(QAbstractListModel):
    # Define roles that QML can access
    PersonIdRole = Qt.UserRole + 1
    EventsRole = Qt.UserRole + 2
    IsVisibleRole = Qt.UserRole + 3
    BoundingBoxesRole = Qt.UserRole + 4
    Keypoints3dRole = Qt.UserRole + 5
    PoseMetricsRole = Qt.UserRole + 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracker = None
        self._person_ids = []
        self._visibility = {}  # person_id -> bool

    def rowCount(self, parent=QModelIndex()):
        return len(self._person_ids)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        person_id = self._person_ids[index.row()]

        if role == self.PersonIdRole:
            return person_id
        elif role == self.EventsRole:
            return self._tracker.get_events_for_person(person_id)
        elif role == self.IsVisibleRole:
            return self._visibility.get(person_id, True)
        elif role == self.BoundingBoxesRole:
            return self._tracker.get_bounding_boxes_for_person(person_id)
        elif role == self.Keypoints3dRole:
            return self._tracker.get_keypoints_3d_dict(person_id)
        elif role == self.PoseMetricsRole:
            metrics = self._tracker.get_pose_metrics_for_person(person_id)
            if not metrics or 'frame' not in metrics or len(metrics['frame']) == 0:
                return {}
            
            frames = metrics['frame']
            result = {}
            # Convert numpy arrays to list of QPointF for QML LineSeries
            for key in ['trunk_bending', 'trunk_side_bending', 'trunk_twist']:
                if key in metrics and len(metrics[key]) > 0:
                    points = [QPointF(float(f), float(v)) for f, v in zip(frames, metrics[key])]
                    result[key] = points
            return result

        return None

    def roleNames(self):
        # This makes the roles available by name in QML
        return {
            self.PersonIdRole: b"personId",
            self.EventsRole: b"events",
            self.IsVisibleRole: b"isVisible",
            self.BoundingBoxesRole: b"boundingBoxes",
            self.Keypoints3dRole: b"keypoints3d",
            self.PoseMetricsRole: b"poseMetrics",
        }

    @Slot(list)
    def remove_persons(self, person_ids):
        if self._tracker:
            self._tracker.remove_persons(person_ids)
            self.refresh()

    @Slot(int, bool)
    def setPersonVisible(self, person_id, visible):
        # Find the person and update their visibility
        if person_id in self._person_ids:
            if self._visibility.get(person_id, True) != visible:
                self._visibility[person_id] = visible
                # Crucially, emit the dataChanged signal so the UI updates!
                try:
                    row = self._person_ids.index(person_id)
                    model_index = self.index(row)
                    self.dataChanged.emit(
                        model_index, model_index, [self.IsVisibleRole]
                    )
                except ValueError:
                    pass

    def populate_from_tracker(self, tracker):
        self._tracker = tracker
        self.refresh()

    def refresh(self):
        self.beginResetModel()
        if self._tracker:
            self._person_ids = self._tracker.get_person_ids()
        else:
            self._person_ids = []

        # Clean up visibility dict
        current_ids_set = set(self._person_ids)
        # Remove stale entries
        self._visibility = {
            pid: vis for pid, vis in self._visibility.items() if pid in current_ids_set
        }
        # Ensure new IDs have default visibility (True) if not present
        # (Not strictly necessary as .get(id, True) handles it, but keeps dict clean)

        self.endResetModel()

    @Slot(int, result=int)
    def getPersonId(self, row):
        if 0 <= row < len(self._person_ids):
            return self._person_ids[row]
        return -1

    @Slot(int, result="QVariantMap")
    def getMetrics(self, row):
        if 0 <= row < len(self._person_ids):
            idx = self.index(row)
            return self.data(idx, self.PoseMetricsRole)
        return {}

    def getIndexForPersonId(self, person_id):
        """Helper to find QModelIndex for a given person ID."""
        try:
            row = self._person_ids.index(person_id)
            return self.index(row, 0)
        except ValueError:
            return QModelIndex()
