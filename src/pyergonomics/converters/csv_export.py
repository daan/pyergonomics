import argparse
from pathlib import Path
import polars as pl
import sys

# This allows the script to be run directly for development/testing.
if __name__ == "__main__" and __package__ is None:
    # Add the project's 'src' directory to the Python path.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pyergonomics.project_settings import ProjectSettings
from pose_skeletons import get_skeleton_def


def export_to_csv(project_folder, csv_filename):
    settings = ProjectSettings(project_folder)
    if not settings.tracker or settings.tracker.df is None:
        print(f"Error: No tracking data found for project in '{project_folder}'")
        return

    tracker_df = settings.tracker.df
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

    person_ids = tracker_df["person_id"].unique().to_list()
    if not person_ids:
        print("No persons found in tracking data.")
        return

    output_path = Path(csv_filename)
    output_stem = output_path.stem
    output_suffix = output_path.suffix or ".csv"

    for person_id in person_ids:
        person_df = tracker_df.filter(pl.col("person_id") == person_id).sort("frame")
        person_df = person_df.with_columns((pl.col("frame") / fps).alias("Time"))

        joint_names = [kp.name for kp in skeleton_def.keypoints]
        coord_col_names = [
            f"{name}_{coord}" for name in joint_names for coord in ["x", "y", "z"]
        ]

        flat_kps_df = person_df.select(pl.col("keypoints").list.flatten())
        struct_df = flat_kps_df.select(pl.col("keypoints").list.to_struct())
        unpacked_df = struct_df.unnest("keypoints")

        if len(unpacked_df.columns) != len(coord_col_names):
            print(
                f"Error: Mismatch between skeleton definition '{skeleton_name}' "
                f"({len(coord_col_names) // 3} joints) and tracking data "
                f"({len(unpacked_df.columns) // 3} joints)."
            )
            return

        rename_map = {f"field_{i}": name for i, name in enumerate(coord_col_names)}
        renamed_df = unpacked_df.rename(rename_map)

        final_df = pl.concat(
            [person_df.select(pl.col("frame").alias("Frame#"), "Time"), renamed_df],
            how="horizontal",
        )

        if len(person_ids) > 1:
            current_output_path = output_path.with_name(
                f"{output_stem}_{person_id}{output_suffix}"
            )
        else:
            current_output_path = output_path.with_suffix(output_suffix)

        final_df.write_csv(current_output_path)
        print(f"Successfully wrote data for person {person_id} to {current_output_path}")


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
