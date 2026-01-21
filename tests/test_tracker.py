import pytest
import polars as pl
import numpy as np
from pathlib import Path
import tempfile

from pyergonomics import Tracker
from pyergonomics.tracker import MergeOverlapError, AssessmentExistsError


class TestTrackerInit:
    def test_init_without_file(self):
        tracker = Tracker()
        assert tracker.df is None
        assert tracker.has_data is False

    def test_init_with_nonexistent_file(self, tmp_path):
        tracker = Tracker(tmp_path / "nonexistent.parquet")
        assert tracker.df is None
        assert tracker.has_data is False

    def test_from_dataframe(self, sample_tracking_df):
        tracker = Tracker.from_dataframe(sample_tracking_df)
        assert tracker.has_data is True
        assert tracker.df.height == sample_tracking_df.height


class TestTrackerProperties:
    def test_has_data_true(self, sample_tracking_df):
        tracker = Tracker.from_dataframe(sample_tracking_df)
        assert tracker.has_data is True

    def test_has_data_false(self):
        tracker = Tracker()
        assert tracker.has_data is False

    def test_has_pose_assessment_false(self, sample_tracking_df):
        tracker = Tracker.from_dataframe(sample_tracking_df)
        assert tracker.has_pose_assessment is False


class TestTrackerPersonOperations:
    def test_get_person_ids(self, sample_tracking_df):
        tracker = Tracker.from_dataframe(sample_tracking_df)
        person_ids = tracker.get_person_ids()
        assert person_ids == [1, 2]

    def test_get_person_ids_empty(self):
        tracker = Tracker()
        assert tracker.get_person_ids() == []

    def test_remove_persons(self, sample_tracking_df):
        tracker = Tracker.from_dataframe(sample_tracking_df)
        tracker.remove_persons([1])
        assert tracker.get_person_ids() == [2]

    def test_merge_persons(self):
        df = pl.DataFrame({
            "person": [1, 1, 2, 2],
            "frame": [0, 1, 2, 3],
            "keypoints_3d": [None, None, None, None],
        })
        tracker = Tracker.from_dataframe(df)
        tracker.merge_persons(1, [2])
        assert tracker.get_person_ids() == [1]
        assert tracker.df.height == 4

    def test_merge_persons_overlap_error(self):
        df = pl.DataFrame({
            "person": [1, 2],
            "frame": [0, 0],  # Same frame = overlap
            "keypoints_3d": [None, None],
        })
        tracker = Tracker.from_dataframe(df)
        with pytest.raises(MergeOverlapError):
            tracker.merge_persons(1, [2])


class TestTrackerFrameOperations:
    def test_get_keypoints_at_frame(self, sample_tracking_df):
        tracker = Tracker.from_dataframe(sample_tracking_df)
        keypoints = tracker.get_keypoints_at_frame(0)
        assert 1 in keypoints
        assert 2 in keypoints

    def test_get_keypoints_at_frame_empty(self, sample_tracking_df):
        tracker = Tracker.from_dataframe(sample_tracking_df)
        keypoints = tracker.get_keypoints_at_frame(999)
        assert keypoints == {}

    def test_get_events_for_person(self, sample_tracking_df):
        tracker = Tracker.from_dataframe(sample_tracking_df)
        events = tracker.get_events_for_person(1)
        assert events == [[0, 9]]  # Continuous from frame 0-9


class TestTrackerSaveLoad:
    def test_save_and_load(self, sample_tracking_df, tmp_path):
        tracker = Tracker.from_dataframe(sample_tracking_df)
        save_path = tmp_path / "test_tracking.parquet"
        tracker.save(save_path)

        loaded_tracker = Tracker(save_path)
        assert loaded_tracker.has_data is True
        assert loaded_tracker.df.height == sample_tracking_df.height

    def test_save_without_path_raises(self, sample_tracking_df):
        tracker = Tracker.from_dataframe(sample_tracking_df)
        with pytest.raises(ValueError):
            tracker.save()
