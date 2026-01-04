import argparse
import toml
import tomllib
from pathlib import Path

from .tracker import Tracker


class ProjectSettings:
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        if self.config_path.is_dir():
            self.config_path = self.config_path / "project.toml"

        if self.config_path.is_file():
            with open(self.config_path, "rb") as f:
                self.data = tomllib.load(f)
        else:
            self.data = {}
        self._tracker = None

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
    def pose_skeleton(self):
        return self.data.get("project", {}).get("pose_skeleton")

    @property
    def pose_skeleton(self):
        return self.data.get("project", {}).get("pose_skeleton")

    @pose_skeleton.setter
    def pose_skeleton(self, value):
        if "project" not in self.data:
            self.data["project"] = {}
        self.data["project"]["pose_skeleton"] = value

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
    
    def frame_path(self, frame):
        return  self.frames_folder / f"{frame:06d}.png"

    @property
    def tracker(self):
        if self._tracker is not None:
            return self._tracker
        tracking_data = self.data.get("tracking", {})
        tracking_file = tracking_data.get("tracking_file")
        if tracking_file:
            tracking_file_path = self.config_path.parent / tracking_file
            self._tracker = Tracker(tracking_file_path)
            return self._tracker
        return None

    def set_tracking_file(self, filename: str):
        if "tracking" not in self.data:
            self.data["tracking"] = {}
        self.data["tracking"]["tracking_file"] = filename
        self._tracker = None

    def save(self, path=None):
        save_path = Path(path) if path else self.config_path
        with open(save_path, "w") as f:
            toml.dump(self.data, f)

    def __str__(self):
        lines = [
            f"Project Settings from {self.config_path}:",
            f"  - Number of frames: {self.number_of_frames}",
            f"  - FPS: {self.frames_per_second}",
        ]
        if self.pose_skeleton:
            lines.append(f"  - Pose skeleton: {self.pose_skeleton}")
        if self.width and self.height:
            lines.append(f"  - Dimensions: {self.width}x{self.height}")
        if self.source_video:
            lines.append(f"  - Video source: {self.source_video}")
        if self.frames_folder:
            lines.append(f"  - Frames folder: {self.frames_folder}")
        if self.tracker and self.tracker.df is not None:
            lines.append(f"  - Tracking file: {self.tracker.tracking_file_path}")
        return "\n".join(lines)

    def __repr__(self):
        return f"ProjectSettings(config_path='{self.config_path}')"


def init_project():
    parser = argparse.ArgumentParser(description="Initialize a pyergonomics project.")
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="The directory to initialize the project in. Defaults to the current directory.",
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--video", type=str, help="Initialize project from a video file."
    )
    source_group.add_argument(
        "--bvh", type=str, help="Initialize project from a BVH file."
    )

    args = parser.parse_args()
    destination = Path(args.folder)

    # Check if target is a file
    if destination.exists() and not destination.is_dir():
        print(f"Error: '{destination}' exists and is not a directory.")
        return

    # Check if target directory exists (and is not the CWD)
    if destination.is_dir() and args.folder != ".":
        print(f"Error: Directory '{destination}' already exists.")
        return

    # Check for existing project file
    if (destination / "project.toml").exists():
        print(f"Error: A project.toml file already exists in '{destination}'.")
        return

    if args.video:
        from .importers.video import init_from_video
        init_from_video(destination, args.video)
    elif args.bvh:
        from .importers.mocap import init_from_bvh
        init_from_bvh(destination, args.bvh)
    else:
        # TODO: remove this defaulting behavior?
        # Default project is mocap if no source is specified
        from .importers.mocap import init_from_bvh
        init_from_bvh(destination, None)


if __name__ == "__main__":
    init_project()

