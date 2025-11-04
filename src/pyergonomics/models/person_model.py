from PySide6.QtCore import QAbstractListModel, QModelIndex, QObject, Qt, Slot


class PersonModel(QAbstractListModel):
    # Define roles that QML can access
    PersonIdRole = Qt.UserRole + 1
    EventsRole = Qt.UserRole + 2
    IsVisibleRole = Qt.UserRole + 3
    BoundingBoxesRole = Qt.UserRole + 4
    Keypoints3dRole = Qt.UserRole + 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._people = []  # This will store our data, e.g., [{'id': 1, 'events': [...], 'visible': True}, ...]

    def rowCount(self, parent=QModelIndex()):
        return len(self._people)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        person = self._people[index.row()]

        if role == self.PersonIdRole:
            return person["id"]
        elif role == self.EventsRole:
            return person["events"]  # QML will get this as a list of lists
        elif role == self.IsVisibleRole:
            return person["visible"]
        elif role == self.BoundingBoxesRole:
            return person["bounding_boxes"]
        elif role == self.Keypoints3dRole:
            return person["keypoints_3d"]

        return None

    def roleNames(self):
        # This makes the roles available by name in QML
        return {
            self.PersonIdRole: b"personId",
            self.EventsRole: b"events",
            self.IsVisibleRole: b"isVisible",
            self.BoundingBoxesRole: b"boundingBoxes",
            self.Keypoints3dRole: b"keypoints3d",
        }

    @Slot(list)
    def remove_persons(self, person_ids):
        # Find all indices to remove first to avoid issues with changing list size
        indices_to_remove = []
        for i, person in enumerate(self._people):
            if person["id"] in person_ids:
                indices_to_remove.append(i)

        # Remove rows from bottom to top to keep indices valid
        for i in sorted(indices_to_remove, reverse=True):
            self.beginRemoveRows(QModelIndex(), i, i)
            self._people.pop(i)
            self.endRemoveRows()

    @Slot(int, bool)
    def setPersonVisible(self, person_id, visible):
        # Find the person and update their visibility
        for i, person in enumerate(self._people):
            if person["id"] == person_id:
                if person["visible"] != visible:
                    person["visible"] = visible
                    # Crucially, emit the dataChanged signal so the UI updates!
                    model_index = self.index(i)
                    self.dataChanged.emit(
                        model_index, model_index, [self.IsVisibleRole]
                    )
                break

    def populate_from_tracker(self, tracker):
        if tracker is None or tracker.df is None:
            self.beginResetModel()
            self._people = []
            self.endResetModel()
            return

        self.beginResetModel()
        self._people = tracker.get_persons_data()
        self.endResetModel()
