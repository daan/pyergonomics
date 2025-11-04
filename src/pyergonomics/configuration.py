import argparse
import toml
import os
from pathlib import Path

from .importers.video import init_from_video
from .importers.mocap import init_from_bvh
from .tracker import Tracker


class Configuration:
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        if self.config_path.is_file():
            with open(self.config_path, "r") as f:
                self.data = toml.load(f)
        else:
            self.data = {}

    @property
    def number_of_frames(self):
        return self.data.get("project", {}).get("number_of_frames")

    @number_of_frames.setter
    def number_of_frames(self, value):
        if "project" not in self.data:
            self.data["project"] = {}
        self.data["project"]["number_of_frames"] = value

    @property
    def frames_per_second(self):
        return self.data.get("project", {}).get("frames_per_second")

    @frames_per_second.setter
    def frames_per_second(self, value):
        if "project" not in self.data:
            self.data["project"] = {}
        self.data["project"]["frames_per_second"] = value

    @property
    def width(self):
        return self.data.get("video", {}).get("width")

    @width.setter
    def width(self, value):
        if "video" not in self.data:
            self.data["video"] = {}
        self.data["video"]["width"] = value

    @property
    def height(self):
        return self.data.get("video", {}).get("height")

    @height.setter
    def height(self, value):
        if "video" not in self.data:
            self.data["video"] = {}
        self.data["video"]["height"] = value

    @property
    def source_video(self):
        return self.data.get("video", {}).get("source_video")

    @source_video.setter
    def source_video(self, value):
        if "video" not in self.data:
            self.data["video"] = {}
        self.data["video"]["source_video"] = value

    @property
    def frames_folder(self):
        return (
            self.config_path.parent / "frames" if "video" in self.data else None
        )

    @property
    def tracker(self):
        tracking_data = self.data.get("tracking", {})
        tracking_file = tracking_data.get("tracking_file")
        if tracking_file:
            tracking_file_path = self.config_path.parent / tracking_file
            return Tracker(tracking_file_path)
        return None

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

    config = Configuration(config_path)
    config.number_of_frames = 0
    config.frames_per_second = 120.0
    config.data["source_mocap"] = {}
    config.save()

    print(f"Default configuration file created at {config_path}")


def main():
    parser = argparse.ArgumentParser(description="Manage image sequence configuration.")
    parser.add_argument(
        "--init_from_video", type=str, help="Initialize a project from a video file."
    )
    parser.add_argument(
        "--init_from_bvh", type=str, help="Initialize a project from a BVH file."
    )
    parser.add_argument(
        "--init",
        type=str,
        help="Create a default project.toml for a mocap project in the specified directory.",
    )

    args = parser.parse_args()

    if args.init_from_video:
        init_from_video(args.init_from_video)
    elif args.init_from_bvh:
        init_from_bvh(args.init_from_bvh)
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

