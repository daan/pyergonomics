import polars as pl
from pathlib import Path


class Tracker:
    def __init__(self, tracking_file_path):
        self.tracking_file_path = Path(tracking_file_path)
        self.df = None
        if self.tracking_file_path.is_file():
            self.df = pl.read_parquet(self.tracking_file_path)
        else:
            print(f"Warning: Tracking file not found at '{self.tracking_file_path}'")

    @property
    def has_data(self):
        """Returns True if tracking data was loaded successfully."""
        return self.df is not None

    def get_keypoints_at_frame(self, frame: int):
        '''Returns a dictionary mapping person IDs to their 3D keypoints at the specified frame.'''
        if self.df is None or "keypoints_3d" not in self.df.columns:
            return {}
        frame_df = self.df.filter(pl.col("frame") == frame)
        if frame_df.is_empty():
            return {}

        result = {}
        for row in frame_df.select(["person", "keypoints_3d"]).to_dicts():
            if row["keypoints_3d"] is not None:
                result[row["person"]] = row["keypoints_3d"]
        return result

    def get_person_ids(self):
        """Returns a list of unique person IDs found in the tracking data."""
        if self.df is None:
            return []
        # Sort to ensure consistent order
        return self.df["person"].unique().sort().to_list()

    def get_persons_data(self):
        if self.df is None:
            return []

        events_data = {}
        bboxes_data = {}
        keypoints_3d_data = {}

        for person_id_key, person_df in self.df.group_by("person"):
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

        people = []
        for person_id, events in sorted(events_data.items()):
            people.append(
                {
                    "id": person_id,
                    "events": events,
                    "visible": True,
                    "bounding_boxes": bboxes_data.get(person_id, {}),
                    "keypoints_3d": keypoints_3d_data.get(person_id, {}),
                }
            )
        return people

    def get_bounding_boxes(self, frame: int):
        if self.df is None:
            return {}

        frame_df = self.df.filter(pl.col("frame") == frame)
        if frame_df.is_empty():
            return {}

        result = {}
        for row in frame_df.select(["person", "x", "y", "w", "h"]).to_dicts():
            person_id = row.pop("person")
            result[person_id] = row
        return result

    def get_keypoints(self, frame: int):
        if self.df is None or "keypoints_3d" not in self.df.columns:
            return {}

        frame_df = self.df.filter(pl.col("frame") == frame)
        if frame_df.is_empty():
            return {}

        result = {}
        for row in frame_df.select(["person", "keypoints_3d"]).to_dicts():
            if row["keypoints_3d"] is not None:
                result[row["person"]] = row["keypoints_3d"]
        return result
