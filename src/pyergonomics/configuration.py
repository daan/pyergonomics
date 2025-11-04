import argparse
import cv2
import toml
import os
from pathlib import Path
import polars as pl


class Configuration:
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        if not self.config_path.is_file():
            raise FileNotFoundError(
                f"Configuration file not found at {config_path} "
                f"(absolute path: {self.config_path.resolve()})"
            )

        with open(self.config_path, "r") as f:
            self.data = toml.load(f)

        project_data = self.data.get("project", {})
        self.number_of_frames = project_data.get("number_of_frames")
        self.frames_per_second = project_data.get("frames_per_second")

        video_data = self.data.get("video", {})
        self.width = video_data.get("width")
        self.height = video_data.get("height")
        self.source_video = video_data.get("source_video")
        self.frames_folder = (
            self.config_path.parent / "frames" if "video" in self.data else None
        )

        tracking_data = self.data.get("tracking", {})
        self.tracking_df = None
        tracking_file = tracking_data.get("tracking_file")
        if tracking_file:
            tracking_file_path = self.config_path.parent / tracking_file
            if tracking_file_path.is_file():
                self.tracking_df = pl.read_parquet(tracking_file_path)
            else:
                print(f"Warning: Tracking file not found at '{tracking_file_path}'")

    def set_tracking_file(self, filename: str):
        if "tracking" not in self.data:
            self.data["tracking"] = {}
        self.data["tracking"]["tracking_file"] = filename

    def save(self, path=None):
        save_path = Path(path) if path else self.config_path
        with open(save_path, "w") as f:
            toml.dump(self.data, f)

    def __str__(self):
        lines = [
            f"Configuration from {self.config_path}:",
            f"  - Number of frames: {self.number_of_frames}",
            f"  - FPS: {self.frames_per_second}",
        ]
        if self.width and self.height:
            lines.append(f"  - Dimensions: {self.width}x{self.height}")
        if self.frames_folder:
            lines.append(f"  - Frames folder: {self.frames_folder}")
        return "\n".join(lines)

    def __repr__(self):
        return f"Configuration(config_path='{self.config_path}')"


def init_project(folder):
    output_dir = Path(folder)
    if output_dir.exists() and not output_dir.is_dir():
        print(f"Error: '{output_dir}' exists and is not a directory.")
        return

    if not output_dir.exists():
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    config_path = output_dir / "project.toml"
    if config_path.exists():
        print(f"Configuration file already exists at {config_path}. No changes made.")
        return

    config_data = {
        "project": {"number_of_frames": 0, "frames_per_second": 120.0},
        "source_mocap": {},
    }

    with open(config_path, "w") as f:
        toml.dump(config_data, f)

    print(f"Default configuration file created at {config_path}")


def init_from_video(video_file):
    video_path = Path(video_file)
    if not video_path.is_file():
        print(f"Error: Video file not found at {video_file}")
        return

    output_dir = Path(video_path.stem)
    frames_dir = output_dir / "frames"

    if output_dir.exists():
        print(
            f"Error: Directory '{output_dir}' already exists. Please remove it or choose a different video."
        )
        return

    os.makedirs(frames_dir)
    print(f"Created directory: {frames_dir}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"Video properties: {frame_count} frames, {fps:.2f} FPS")

    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_filename = f"{count:06d}.png"
        cv2.imwrite(str(frames_dir / frame_filename), frame)

        count += 1
        if count > 0 and count % 100 == 0:
            print(f"Extracted {count}/{frame_count} frames...")

    cap.release()
    print(f"Finished extracting {count} frames.")

    config_data = {
        "project": {"number_of_frames": count, "frames_per_second": fps},
        "video": {
            "source_video": str(video_path),
            "width": width,
            "height": height,
        },
    }

    config_path = output_dir / "project.toml"
    with open(config_path, "w") as f:
        toml.dump(config_data, f)

    print(f"Configuration file created at {config_path}")


def main():
    parser = argparse.ArgumentParser(description="Manage image sequence configuration.")
    parser.add_argument(
        "--init_from_video", type=str, help="Initialize a project from a video file."
    )
    parser.add_argument(
        "--init",
        type=str,
        help="Create a default project.toml for a mocap project in the specified directory.",
    )

    args = parser.parse_args()

    if args.init_from_video:
        init_from_video(args.init_from_video)
    elif args.init:
        init_project(args.init)
    else:
        # Example of how to load a configuration
        try:
            # Assuming project.toml is in the current directory for loading example
            config = Configuration("project.toml")
            print(config)
        except FileNotFoundError:
            print(
                "No project.toml found. Use --init_from_video or --init to create one."
            )
            parser.print_help()


if __name__ == "__main__":
    main()

