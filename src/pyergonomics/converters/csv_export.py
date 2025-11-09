import argparse
from pathlib import Path
import polars as pl
import sys
from tqdm import tqdm

# This allows the script to be run directly for development/testing.
if __name__ == "__main__" and __package__ is None:
    # Add the project's 'src' directory to the Python path.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pyergonomics.project_settings import ProjectSettings
from pose_skeletons import get_skeleton_def


def export_to_csv(project_folder, csv_filename):
    settings = ProjectSettings(project_folder)
    if not settings.tracker or not settings.tracker.has_data:
        print(f"Error: No tracking data found for project in '{project_folder}'")
        return

    fps = settings.frames_per_second
    if not fps:
        print("Error: 'frames_per_second' not set in project.toml")
        return

    skeleton_name = settings.pose_skeleton
    if not skeleton_name:
        print("Error: 'pose_skeleton' not set in project.toml")
        return

    try:
        skeleton_def = get_skeleton_def(skeleton_name)
    except ValueError as e:
        print(f"Error: {e}")
        return

    persons = settings.tracker.get_person_ids()
    if not persons:
        print("No persons found in tracking data.")
        return

    output_path = Path(csv_filename)
    output_stem = output_path.stem
    output_suffix = output_path.suffix or ".csv"

    joint_names = [kp.name for kp in skeleton_def.keypoints]
    coord_col_names = [
        f"{name}_{coord}" for name in joint_names for coord in ["x", "y", "z"]
    ]

    for person in tqdm(persons, desc="Processing persons"):
        person_df = settings.tracker.get_keypoints_for_person(person)

        if person_df.is_empty() or "keypoints_3d" not in person_df.columns:
            print(f"Warning: No valid keypoint data for person {person}.")
            continue

        # Filter out rows where keypoints are null, which can occur
        person_df = person_df.filter(pl.col("keypoints_3d").is_not_null())
        if person_df.is_empty():
            print(f"Warning: No valid keypoint data for person {person}.")
            continue

        # Use Polars expressions for bulk processing
        person_df = person_df.with_columns((pl.col("frame") / fps).alias("Time"))

        # Check for data integrity on the first row
        first_row_kps = person_df.select(pl.col("keypoints_3d").first()).item()
        if len(first_row_kps) * 3 != len(coord_col_names):
            num_data_joints = len(first_row_kps)
            num_skel_joints = len(coord_col_names) // 3
            print(
                f"Warning: Mismatch for person {person}. "
                f"Skeleton has {num_skel_joints} joints, "
                f"but data has {num_data_joints}."
            )
            continue

        # Flatten the keypoints in Python for maximum compatibility
        rows = []
        for row_dict in person_df.select(["frame", "Time", "keypoints_3d"]).to_dicts():
            flat_keypoints = [
                coord for point in row_dict["keypoints_3d"] for coord in point
            ]
            rows.append([row_dict["frame"], row_dict["Time"]] + flat_keypoints)

        header = ["Frame#", "Time"] + coord_col_names
        final_df = pl.DataFrame(rows, schema=header).sort("Frame#")

        if len(persons) > 1:
            current_output_path = output_path.with_name(
                f"{output_stem}_{person}{output_suffix}"
            )
        else:
            current_output_path = output_path.with_suffix(output_suffix)

        final_df.write_csv(current_output_path)
        print(f"Successfully wrote data for person {person} to {current_output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Export pyergonomics tracking data to a CSV file."
    )
    parser.add_argument(
        "--project",
        required=True,
        help="The directory of the pyergonomics project.",
    )
    parser.add_argument(
        "csv_filename",
        help="The path to the output CSV file.",
    )
    args = parser.parse_args()

    export_to_csv(args.project, args.csv_filename)


if __name__ == "__main__":
    main()
