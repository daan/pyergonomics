from PySide6.QtCore import QSortFilterProxyModel, Slot, Qt
from .person_model import PersonModel


class PeopleInFrameProxyModel(QSortFilterProxyModel):
    CurrentBoundingBoxRole = Qt.UserRole + 100
    CurrentKeypoints3dRole = Qt.UserRole + 101

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_frame = 0

    def roleNames(self):
        if not self.sourceModel():
            return {}
        names = self.sourceModel().roleNames()
        names[self.CurrentBoundingBoxRole] = b"currentBoundingBox"
        names[self.CurrentKeypoints3dRole] = b"currentKeypoints3d"
        return names

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        source_index = self.mapToSource(index)
        if not source_index.isValid():
            return None

        if role == self.CurrentBoundingBoxRole:
            all_bboxes = self.sourceModel().data(
                source_index, PersonModel.BoundingBoxesRole
            )
            if all_bboxes:
                return all_bboxes.get(self._current_frame)
            return None
        elif role == self.CurrentKeypoints3dRole:
            all_keypoints = self.sourceModel().data(
                source_index, PersonModel.Keypoints3dRole
            )
            if all_keypoints:
                return all_keypoints.get(self._current_frame)
            return None

        # For all other roles, delegate to the source model.
        return self.sourceModel().data(source_index, role)

    @Slot(int)
    def setCurrentFrame(self, frame):
        if self._current_frame != frame:
            self._current_frame = frame
            # The filter will add/remove rows, but for rows that remain, we need
            # to signal that their data for our custom role has changed.
            if self.rowCount() > 0:
                top_left = self.index(0, 0)
                bottom_right = self.index(self.rowCount() - 1, 0)
                self.dataChanged.emit(
                    top_left,
                    bottom_right,
                    [self.CurrentBoundingBoxRole, self.CurrentKeypoints3dRole],
                )
            self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        source_model = self.sourceModel()
        if not source_model:
            return False

        # Get the index for the source model
        index = source_model.index(source_row, 0, source_parent)

        # Check the IsVisibleRole
        is_visible = source_model.data(index, PersonModel.IsVisibleRole)
        if not is_visible:
            return False

        # Check if the person is active in the current frame
        events = source_model.data(index, PersonModel.EventsRole)
        for start_frame, end_frame in events:
            if start_frame <= self._current_frame <= end_frame:
                return True  # Found a match, accept the row

        return False  # No active event for this person at this frame
