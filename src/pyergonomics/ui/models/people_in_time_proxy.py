from PySide6.QtCore import QSortFilterProxyModel, Qt
from .person_model import PersonModel


class PeopleInTimeProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def roleNames(self):
        if not self.sourceModel():
            return {}
        return self.sourceModel().roleNames()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        source_index = self.mapToSource(index)
        if not source_index.isValid():
            return None
        return self.sourceModel().data(source_index, role)

    def filterAcceptsRow(self, source_row, source_parent):
        # We no longer filter by visibility; we want to show all people.
        # The view will handle the visual state.
        return True
