import polars as pl
import numpy as np
from pathlib import Path

from .pose_assessment import make_pose_assessment

class MergeOverlapError(Exception):
    pass

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

    def save(self, path=None):
        """Saves the current dataframe to parquet."""
        if self.df is None:
            return
        
        save_path = Path(path) if path else self.tracking_file_path
        # Ensure directory exists
        if save_path.parent:
            save_path.parent.mkdir(parents=True, exist_ok=True)
        self.df.write_parquet(save_path)

    def remove_persons(self, person_ids):
        """Removes specific person IDs from the data."""
        if self.df is None:
            return
        self.df = self.df.filter(~pl.col("person").is_in(person_ids))

    def merge_persons(self, target_id, source_ids):
        """Merges source_ids into target_id."""
        if self.df is None:
            return

        # Check for overlap
        involved_ids = [target_id] + list(source_ids)
        subset = self.df.filter(pl.col("person").is_in(involved_ids))
        
        # Check if any frame appears more than once
        overlap = subset.group_by("frame").len().filter(pl.col("len") > 1)
        
        if not overlap.is_empty():
            raise MergeOverlapError("Cannot merge persons because their timelines overlap.")

        self.df = self.df.with_columns(
            pl.when(pl.col("person").is_in(source_ids))
            .then(pl.lit(target_id))
            .otherwise(pl.col("person"))
            .alias("person")
        )

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

    def get_quaternions_at_frame(self, frame: int):
        '''Returns a dictionary mapping person IDs to their quaternions wxyz at the specified frame.'''
        if self.df is None or "keypoints_quat" not in self.df.columns:
            return {}
        frame_df = self.df.filter(pl.col("frame") == frame)
        if frame_df.is_empty():
            return {}

        result = {}
        for row in frame_df.select(["person", "keypoints_quat"]).to_dicts():
            if row["keypoints_quat"] is not None:
                result[row["person"]] = row["keypoints_quat"]
        return result

    def get_person_ids(self):
        """Returns a list of unique person IDs found in the tracking data."""
        if self.df is None:
            return []
        # Sort to ensure consistent order
        return self.df["person"].unique().sort().to_list()

    def get_keypoints_for_person(self, person_id, frame=None):
        if self.df is None:
            return [] # Or None, depending on your preference
        
        qs = self.df.filter(pl.col("person") == person_id)
        
        if frame is not None:
            qs = qs.filter(pl.col("frame") == frame)
            
        # Check if we found data
        if qs.height == 0:
            return None
        if frame is not None:
            return np.array(qs["keypoints_3d"].to_list())
        return [np.array(val) for val in qs["keypoints_3d"].to_list()]

    def get_quaternions_for_person(self, person_id):
        """Returns a dictionary mapping frame numbers to quaternions for a specific person."""
        if self.df is None or "keypoints_quat" not in self.df.columns:
            return {}
        person_df = self.df.filter(pl.col("person") == person_id)

        return {
            row["frame"]: row["keypoints_quat"]
            for row in person_df.select(["frame", "keypoints_quat"]).to_dicts()
            if row["keypoints_quat"] is not None
        }

    def get_events_for_person(self, person_id):
        """Returns a list of [start, end] frame ranges where the person is present."""
        if self.df is None:
            return []
        
        # Get sorted frames for this person
        frames = self.df.filter(pl.col("person") == person_id)["frame"].sort().to_list()
        
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
        return events

    def get_bounding_boxes_for_person(self, person_id):
        """Returns a dictionary of frame -> {x, y, w, h} for the person."""
        if self.df is None:
            return {}

        # Check if bounding box columns exist
        bbox_cols = ["x", "y", "w", "h"]
        if not all(col in self.df.columns for col in bbox_cols):
            return {}

        person_df = self.df.filter(pl.col("person") == person_id)
        return {
            row["frame"]: {
                "x": row["x"],
                "y": row["y"],
                "w": row["w"],
                "h": row["h"],
            }
            for row in person_df.select(["frame", "x", "y", "w", "h"]).to_dicts()
        }

    def get_keypoints_3d_dict(self, person_id):
        """Returns a dictionary of frame -> keypoints_3d for the person."""
        if self.df is None or "keypoints_3d" not in self.df.columns:
            return {}
            
        person_df = self.df.filter(pl.col("person") == person_id)
        return {
            row["frame"]: row["keypoints_3d"]
            for row in person_df.select(["frame", "keypoints_3d"]).to_dicts()
            if row["keypoints_3d"] is not None
        }

    def get_persons_data(self):
        if self.df is None:
            return []

        events_data = {}
        bboxes_data = {}
        keypoints_3d_data = {}

        # Check if bounding box columns exist
        bbox_cols = ["x", "y", "w", "h"]
        has_bbox = all(col in self.df.columns for col in bbox_cols)

        for person_id_key, person_df in self.df.group_by("person"):
            # Unpack person_id, which can be a tuple when grouping
            person_id = (
                person_id_key[0] if isinstance(person_id_key, tuple) else person_id_key
            )

            # Bounding boxes for this person (only if columns exist)
            if has_bbox:
                bboxes_data[person_id] = {
                    row["frame"]: {
                        "x": row["x"],
                        "y": row["y"],
                        "w": row["w"],
                        "h": row["h"],
                    }
                    for row in person_df.select(["frame", "x", "y", "w", "h"]).to_dicts()
                }
            else:
                bboxes_data[person_id] = {}

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

        # Check if bounding box columns exist
        bbox_cols = ["x", "y", "w", "h"]
        if not all(col in self.df.columns for col in bbox_cols):
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


    def get_pose_metrics_for_person(self, person_id, frame=None):
        """
        Returns a dictionary of numpy arrays including 'frame' and angles.
        This handles gaps in data by ensuring every angle is paired with its specific frame number.
        """
        # We now extract 'frame' explicitly
        target_columns = [
            "frame",
            "trunk_bending", "trunk_side_bending", "trunk_twist",
            "left_elbow_above_shoulder", "right_elbow_above_shoulder",
            "left_hand_above_head_level", "right_hand_above_head_level",
            "left_far_reach", "right_far_reach",
        ]

        if self.df is None:
            return {}

        # Check if assessment columns exist (only check trunk columns for backwards compatibility)
        if not all(col in self.df.columns for col in ["trunk_bending", "trunk_side_bending", "trunk_twist"]):
             print("Warning: Assessment columns not found.")
             return {}

        # Filter by person
        q = self.df.filter(pl.col("person") == person_id)

        # Filter by frame or sort
        if frame is not None:
            q = q.filter(pl.col("frame") == frame)
        else:
            q = q.sort("frame")

        # Extract columns (only those that exist in the dataframe)
        result = {}
        for col in target_columns:
            if col not in self.df.columns:
                continue
            if not q.is_empty():
                result[col] = q.get_column(col).to_numpy()
            else:
                result[col] = np.array([])

        return result

    # def get_pose_metrics_for_person(self, person_id, frame=None):
    #     """
    #     Returns a dictionary of numpy arrays for trunk angles (bending, side_bending, twist).
        
    #     Args:
    #         person_id: The ID of the person to retrieve data for.
    #         frame: (Optional) If provided, returns data for that specific frame.
    #                If None, returns data for all frames sorted by time.
    #     """
    #     metrics = ["trunk_bending", "trunk_side_bending", "trunk_twist"]
        
    #     # Validation
    #     if self.df is None:
    #         return {}
        
    #     # Return empty if the assessment hasn't been run yet
    #     if not all(m in self.df.columns for m in metrics):
    #         print(f"Warning: Columns {metrics} not found. Run 'add_pose_assessment_columns' first.")
    #         return {}

    #     # 1. Filter by person
    #     # We start with a lazy query or direct filter
    #     q = self.df.filter(pl.col("person") == person_id)

    #     # 2. Filter by frame (if specified) or Sort (if getting full history)
    #     if frame is not None:
    #         q = q.filter(pl.col("frame") == frame)
    #     else:
    #         q = q.sort("frame")

    #     # 3. Extract as Dictionary of NumPy Arrays
    #     result = {}
    #     for m in metrics:
    #         # Extract the column as a Polars Series, then convert to NumPy
    #         if not q.is_empty():
    #             result[m] = q.get_column(m).to_numpy()
    #         else:
    #             result[m] = np.array([])
                
    #     return result


def add_pose_assessment_columns(tracker, skeleton):
    """
    Calculates pose assessment metrics for all frames and persons in the project's tracker
    and updates the DataFrame with trunk and arm assessment columns:
    - trunk_bending, trunk_side_bending, trunk_twist
    - left_elbow_above_shoulder, right_elbow_above_shoulder
    - left_hand_above_head_level, right_hand_above_head_level
    - left_far_reach, right_far_reach
    """
    if tracker.df is None or "keypoints_3d" not in tracker.df.columns:
        print("Tracker has no data or missing 'keypoints_3d' column.")
        return

    # Define a helper to bridge Polars and the existing assessment function
    def _compute_row_metrics(keypoints):
        if keypoints is None:
            return None

        # Ensure input is a numpy array
        kp_array = np.array(keypoints)

        # Run the existing assessment logic
        # Note: We wrap this to strictly extract only the float values we want,
        # discarding the 'Plane' objects which would cause Polars to fail.
        results = make_pose_assessment(skeleton, kp_array)

        return {
            "trunk_bending": results.get("trunk_bending"),
            "trunk_side_bending": results.get("trunk_side_bending"),
            "trunk_twist": results.get("trunk_twist"),
            "left_elbow_above_shoulder": results.get("left_elbow_above_shoulder"),
            "right_elbow_above_shoulder": results.get("right_elbow_above_shoulder"),
            "left_hand_above_head_level": results.get("left_hand_above_head_level"),
            "right_hand_above_head_level": results.get("right_hand_above_head_level"),
            "left_far_reach": results.get("left_far_reach"),
            "right_far_reach": results.get("right_far_reach"),
        }

    # Define the output schema for Polars
    metrics_dtype = pl.Struct({
        "trunk_bending": pl.Float64,
        "trunk_side_bending": pl.Float64,
        "trunk_twist": pl.Float64,
        "left_elbow_above_shoulder": pl.Float64,
        "right_elbow_above_shoulder": pl.Float64,
        "left_hand_above_head_level": pl.Float64,
        "right_hand_above_head_level": pl.Float64,
        "left_far_reach": pl.Float64,
        "right_far_reach": pl.Float64,
    })

    # Apply the function and unnest the results into new columns
    # map_elements executes the python function on every row
    updated_df = tracker.df.with_columns(
        pl.col("keypoints_3d")
        .map_elements(_compute_row_metrics, return_dtype=metrics_dtype)
        .alias("temp_metrics")
    ).unnest("temp_metrics")

    # Update the tracker's dataframe in-place
    tracker.df = updated_df
