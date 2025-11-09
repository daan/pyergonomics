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

    num_frames = settings.number_of_frames
    if not num_frames:
        print("Error: 'number_of_frames' not set in project.toml.")
        return

    output_path = Path(csv_filename)
    output_stem = output_path.stem
    output_suffix = output_path.suffix or ".csv"

    joint_names = [kp.name for kp in skeleton_def.keypoints]
    coord_col_names = [
        f"{name}_{coord}" for name in joint_names for coord in ["x", "y", "z"]
    ]
    header = ["Frame#", "Time"] + coord_col_names

    for person in persons:
        rows = []
        for frame_idx in tqdm(range(num_frames), desc=f"Processing person {person}"):
            kps_at_frame = settings.tracker.get_keypoints_at_frame(frame_idx)
            if person in kps_at_frame:
                keypoints = kps_at_frame[person]
                # Keypoints are expected to be a list of [x, y, z] coordinates
                flat_keypoints = [coord for point in keypoints for coord in point]

                if len(flat_keypoints) != len(coord_col_names):
                    print(
                        f"Warning: Mismatch for person {person} at frame {frame_idx}. "
                        f"Skeleton has {len(coord_col_names)//3} joints, "
                        f"data has {len(flat_keypoints)//3}."
                    )
                    continue

                time = frame_idx / fps
                rows.append([frame_idx, time] + flat_keypoints)

        if not rows:
            print(f"No valid keypoint data found for person {person}.")
            continue

        person_df = pl.DataFrame(rows, schema=header)

        if len(persons) > 1:
            current_output_path = output_path.with_name(
                f"{output_stem}_{person}{output_suffix}"
            )
        else:
            current_output_path = output_path.with_suffix(output_suffix)

        person_df.write_csv(current_output_path)
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
