from PySide6.QtCore import QObject, Signal, Property, QUrl, Slot, QTimer, QItemSelectionModel, QItemSelection
from PySide6.QtWidgets import QMessageBox
from pathlib import Path
import polars as pl

from ..project_settings import ProjectSettings
from ..tracker import MergeOverlapError
from .models.person_model import PersonModel


class AppState(QObject):
    currentFrameChanged = Signal()
    selectedPersonIdsChanged = Signal()
    isPlayingChanged = Signal()
    viewPositionChanged = Signal()
    pixelsPerFrameChanged = Signal()
    projectLoaded = Signal()
    projectPathChanged = Signal()

    def __init__(self, project_path, parent=None):
        super().__init__(parent)
        self.person_model = None
        self.selection_model = None
        self._selected_person_ids_cache = [] # Cache for QML property
        self._load_project_data(project_path)

    def _load_project_data(self, project_path):
        self.project_path = Path(project_path)
        self.projectPathChanged.emit()

        self.config = ProjectSettings(self.project_path)
        # Use tracker object instead of direct dataframe access where possible
        self.tracker = self.config.tracker

        self._current_frame = 0
        self.currentFrameChanged.emit()

        self._selected_person_ids_cache = []
        self.selectedPersonIdsChanged.emit()

        self._all_person_ids = []
        if self.tracker.has_data:
            self._all_person_ids = self.tracker.get_person_ids()
            
        # Base path to your image sequence.
        # Use file:/// prefix for local files in QML.
        self._image_sequence_path = "file:///path/to/your/images/"

        self._is_playing = False
        self.isPlayingChanged.emit()
        self._was_playing_before_scrub = False
        self._frame_rate = self.config.frames_per_second or 24.0
        self._total_frames = self.config.number_of_frames or 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_frame)
        if self._frame_rate > 0:
            self._timer.setInterval(int(1000 / self._frame_rate))

        self._view_position = 0.0
        self.viewPositionChanged.emit()
        self._pixels_per_frame = 2.0
        self.pixelsPerFrameChanged.emit()
        self.projectLoaded.emit()

    def set_person_model(self, model):
        self.person_model = model
        # Initialize Selection Model
        self.selection_model = QItemSelectionModel(self.person_model)
        self.selection_model.selectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self, selected, deselected):
        """Updates the cached list of IDs when the internal selection model changes."""
        if not self.person_model:
            return
        
        # Rebuild the list of selected IDs
        # We use selectedRows() to avoid duplicates if multiple columns existed (though here it's 1 col)
        indexes = self.selection_model.selectedRows()
        self._selected_person_ids_cache = [
            idx.data(PersonModel.PersonIdRole) for idx in indexes
        ]
        self._selected_person_ids_cache.sort()
        self.selectedPersonIdsChanged.emit()

    @Property(str, notify=projectPathChanged)
    def projectPath(self):
        return str(self.project_path)

    @Property(bool, notify=isPlayingChanged)
    def isPlaying(self):
        return self._is_playing

    def _set_is_playing(self, playing):
        if self._is_playing != playing:
            self._is_playing = playing
            self.isPlayingChanged.emit()
            if self._is_playing:
                if self._total_frames > 0:
                    self._timer.start()
            else:
                self._timer.stop()

    @Slot()
    def togglePlayPause(self):
        self._set_is_playing(not self._is_playing)

    @Slot()
    def play(self):
        self._set_is_playing(True)

    @Slot()
    def pause(self):
        self._set_is_playing(False)

    @Slot()
    def startScrubbing(self):
        self._was_playing_before_scrub = self.isPlaying
        self.pause()

    @Slot()
    def stopScrubbing(self):
        if self._was_playing_before_scrub:
            self.play()

    @Property(float, notify=viewPositionChanged)
    def viewPosition(self):
        return self._view_position

    @viewPosition.setter
    def viewPosition(self, value):
        if self._view_position != value:
            self._view_position = value
            self.viewPositionChanged.emit()

    @Property(float, notify=pixelsPerFrameChanged)
    def pixelsPerFrame(self):
        return self._pixels_per_frame

    @pixelsPerFrame.setter
    def pixelsPerFrame(self, value):
        if self._pixels_per_frame != value:
            self._pixels_per_frame = value
            self.pixelsPerFrameChanged.emit()

    @Slot(float)
    def pan(self, frame_delta):
        self.viewPosition += frame_delta

    @Slot(float, float)
    def zoom(self, new_pixels_per_frame, frame_at_mouse):
        if self.pixelsPerFrame > 0:
            mouse_x = (frame_at_mouse - self.viewPosition) * self.pixelsPerFrame
            self.pixelsPerFrame = new_pixels_per_frame
            if self.pixelsPerFrame > 0:
                self.viewPosition = frame_at_mouse - mouse_x / self.pixelsPerFrame

    def _advance_frame(self):
        if self._total_frames > 0:
            next_frame = (self.currentFrame + 1) % self._total_frames
            self.currentFrame = next_frame

    @Property(int, notify=currentFrameChanged)
    def currentFrame(self):
        return self._current_frame

    @currentFrame.setter
    def currentFrame(self, value):
        if self._current_frame != value:
            self._current_frame = value
            # When this signal is emitted, QML knows to re-evaluate
            # ANY property that depends on it, including our new source property.
            self.currentFrameChanged.emit()

    @Property(int, notify=projectLoaded)
    def totalFrames(self):
        return self._total_frames

    @Property(int, notify=projectLoaded)
    def sourceWidth(self):
        return self.config.width or 1

    @Property(int, notify=projectLoaded)
    def sourceHeight(self):
        return self.config.height or 1

    # ✨ NEW PROPERTY HERE ✨
    @Property(QUrl, notify=currentFrameChanged)
    def currentFrameSource(self):
        # Constructs the full path to the image for the current frame.
        # We'll format the frame number to match the file naming convention.
        image_filename = f"frame_{self._current_frame:04d}.png"
        return QUrl(self._image_sequence_path + image_filename)

    @Property("QVariantList", notify=selectedPersonIdsChanged)
    def selectedPersonIds(self):
        return self._selected_person_ids_cache

    @Slot(str)
    def load_project(self, project_url):
        toml_path = Path(QUrl(project_url).toLocalFile())
        self._load_project_data(toml_path)
        if self.person_model:
            self.person_model.populate_from_tracker(self.tracker)
            # Clear selection on reload
            if self.selection_model:
                self.selection_model.clear()

    @Slot()
    def save_project(self):
        if not self.tracker.has_data:
            print("Warning: No tracking data to save.")
            return

        tracking_data = self.config.data.get("tracking", {})
        tracking_file = tracking_data.get("tracking_file")
        if not tracking_file:
            print("Warning: No tracking file specified in config. Use 'Save As'.")
            return

        tracking_file_path = self.project_path.parent / tracking_file
        self.tracker.save(tracking_file_path)
        self.config.save()
        print(f"Project saved to {self.project_path}")

    @Slot(str)
    def save_project_as(self, new_toml_url):
        new_toml_path = Path(QUrl(new_toml_url).toLocalFile())
        if new_toml_path.suffix != ".toml":
            new_toml_path = new_toml_path.with_suffix(".toml")

        new_project_dir = new_toml_path.parent
        new_project_name = new_toml_path.stem
        new_parquet_filename = f"{new_project_name}.parquet"
        new_parquet_path = new_project_dir / new_parquet_filename

        if self.tracker.has_data:
            self.tracker.save(new_parquet_path)

        self.config.set_tracking_file(new_parquet_filename)
        self.config.save(new_toml_path)

        # Update app state to reflect the new project path
        self.project_path = new_toml_path
        self.config.config_path = new_toml_path
        self.projectPathChanged.emit()
        print(f"Project saved as {self.project_path}")

    @Slot()
    def delete_selected_persons(self):
        if not self._selected_person_ids_cache or self.person_model is None:
            return

        ids_to_delete = self._selected_person_ids_cache[:]
        self.tracker.remove_persons(ids_to_delete)

        self.person_model.remove_persons(ids_to_delete)

        self._all_person_ids = [pid for pid in self._all_person_ids if pid not in ids_to_delete]
        
        # Selection model handles clearing automatically when rows are removed,
        # but we ensure cache is updated via the signal.

    @Slot()
    def merge_selected_persons(self):
        if len(self._selected_person_ids_cache) < 2 or self.person_model is None:
            return

        selected_ids = sorted(self._selected_person_ids_cache)
        target_id = selected_ids[0]
        source_ids = selected_ids[1:]

        try:
            # Update the DataFrame by re-assigning person IDs
            self.tracker.merge_persons(target_id, source_ids)
        except MergeOverlapError as e:
            QMessageBox.critical(None, "Merge failed because of overlap", str(e))
            return

        # The model's structure will change significantly, so a full reset is best.
        self.person_model.populate_from_tracker(self.tracker)

        # Update internal state
        self._all_person_ids = [pid for pid in self._all_person_ids if pid not in source_ids]

        # Select the merged person
        if self.selection_model:
            self.selection_model.clear()
            target_index = self.person_model.getIndexForPersonId(target_id)
            if target_index.isValid():
                self.selection_model.select(target_index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                self.selection_model.setCurrentIndex(target_index, QItemSelectionModel.Current)

    @Slot()
    def clearSelection(self):
        if self.selection_model:
            self.selection_model.clear()

    @Slot(int, str)
    def updateSelection(self, person_id, mode):
        if not self.person_model or not self.selection_model:
            return

        index = self.person_model.getIndexForPersonId(person_id)
        if not index.isValid():
            return

        command = QItemSelectionModel.NoUpdate

        if mode == 'single':
            # Clear existing and select this one
            command = QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows
            self.selection_model.select(index, command)
            self.selection_model.setCurrentIndex(index, QItemSelectionModel.Current)
            
        elif mode == 'toggle':
            # Toggle this one, keep others
            command = QItemSelectionModel.Toggle | QItemSelectionModel.Rows
            self.selection_model.select(index, command)
            self.selection_model.setCurrentIndex(index, QItemSelectionModel.Current)
            
        elif mode == 'range':
            # Select range from anchor (currentIndex) to this one
            anchor = self.selection_model.currentIndex()
            if not anchor.isValid():
                # Fallback to single select if no anchor
                command = QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows
                self.selection_model.select(index, command)
            else:
                # Create a selection range
                selection = QItemSelection(anchor, index)
                # Standard behavior: Clear existing, select the range
                command = QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows
                self.selection_model.select(selection, command)
            
            # Update current index to the new click
            self.selection_model.setCurrentIndex(index, QItemSelectionModel.Current)
