from PySide6.QtCore import QAbstractListModel, QModelIndex, QObject, Qt, Slot
import polars as pl


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

    def populate_from_data(self, df):
        if df is None:
            self.beginResetModel()
            self._people = []
            self.endResetModel()
            return

        events_data = {}
        bboxes_data = {}
        keypoints_3d_data = {}

        for person_id_key, person_df in df.group_by("person"):
            # Unpack person_id, which can be a tuple when grouping
            person_id = (
                person_id_key[0] if isinstance(person_id_key, tuple) else person_id_key
            )

            # Bounding boxes for this person
            bboxes_data[person_id] = {
                row["frame"]: {
                    "x": row["x"],
                    "y": row["y"],
                    "w": row["w"],
                    "h": row["h"],
                }
                for row in person_df.select(["frame", "x", "y", "w", "h"]).to_dicts()
            }

            # 3D keypoints for this person
            if "keypoints_3d" in person_df.columns:
                keypoints_3d_data[person_id] = {
                    row["frame"]: row["keypoints_3d"]
                    for row in person_df.select(["frame", "keypoints_3d"]).to_dicts()
                    if row["keypoints_3d"] is not None
                }

            # Calculate contiguous frame blocks (events)
            frames = sorted(person_df["frame"].to_list())
            events = []
            if frames:
                start_frame = frames[0]
                end_frame = frames[0]
                for i in range(1, len(frames)):
                    if frames[i] == end_frame + 1:
                        end_frame = frames[i]
                    else:
                        events.append([start_frame, end_frame])
                        start_frame = frames[i]
                        end_frame = frames[i]
                events.append([start_frame, end_frame])
            events_data[person_id] = events

        self.beginResetModel()
        self._people = []
        for person_id, events in sorted(events_data.items()):
            self._people.append(
                {
                    "id": person_id,
                    "events": events,
                    "visible": True,
                    "bounding_boxes": bboxes_data.get(person_id, {}),
                    "keypoints_3d": keypoints_3d_data.get(person_id, {}),
                }
            )
        self.endResetModel()
