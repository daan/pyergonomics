import argparse
import toml
import tomllib
from pathlib import Path

from .tracker import Tracker


class ProjectNotFoundError(Exception):
    """Raised when a project folder or project.toml file is not found."""
    pass


class ProjectSettings:
    def __init__(self, config_path=None):
        self._in_memory = config_path is None

        if self._in_memory:
            self.config_path = None
            self.data = {"project": {}}
            self._tracker = None
            self._skeleton_cache = None
            return

        self.config_path = Path(config_path)

        if self.config_path.is_dir():
            self.config_path = self.config_path / "project.toml"

        if not self.config_path.parent.exists():
            raise ProjectNotFoundError(f"Project folder not found: {self.config_path.parent}")

        if not self.config_path.is_file():
            raise ProjectNotFoundError(f"Project file not found: {self.config_path}")

        with open(self.config_path, "rb") as f:
            self.data = tomllib.load(f)

        self._tracker = None
        self._skeleton_cache = None

    def persist(self, project_dir):
        """Save an in-memory project to disk."""
        project_dir = Path(project_dir)
        project_dir.mkdir(parents=True, exist_ok=True)

        self.config_path = project_dir / "project.toml"

        # Save tracker if present
        if self._tracker is not None and self._tracker.df is not None:
            tracking_filename = "tracking.parquet"
            self._tracker.save(project_dir / tracking_filename)
            self.set_tracking_file(tracking_filename)

        self.save()
        self._in_memory = False
        print(f"Project saved to {project_dir}")

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
    def pose_skeleton_name(self):
        """The skeleton name as stored in config."""
        return self.data.get("project", {}).get("pose_skeleton")

    @pose_skeleton_name.setter
    def pose_skeleton_name(self, value: str):
        if "project" not in self.data:
            self.data["project"] = {}
        self.data["project"]["pose_skeleton"] = value
        self._skeleton_cache = None

    @property
    def pose_skeleton(self):
        """The skeleton object (cached)."""
        if self._skeleton_cache is None:
            name = self.pose_skeleton_name
            if name:
                from pose_skeletons import get_skeleton_def
                self._skeleton_cache = get_skeleton_def(name)
        return self._skeleton_cache

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
        if save_path is None:
            raise ValueError("No path specified for in-memory project. Use persist() instead.")
        with open(save_path, "w") as f:
            toml.dump(self.data, f)

    def __str__(self):
        if self._in_memory:
            header = "Project Settings (in-memory):"
        else:
            header = f"Project Settings from {self.config_path}:"

        lines = [
            header,
            f"  - Number of frames: {self.number_of_frames}",
            f"  - FPS: {self.frames_per_second}",
        ]
        if self.pose_skeleton_name:
            lines.append(f"  - Pose skeleton: {self.pose_skeleton_name}")
        if self.width and self.height:
            lines.append(f"  - Dimensions: {self.width}x{self.height}")
        if self.source_video:
            lines.append(f"  - Video source: {self.source_video}")
        if not self._in_memory and self.frames_folder:
            lines.append(f"  - Frames folder: {self.frames_folder}")
        if self.tracker and self.tracker.df is not None:
            if self.tracker.tracking_file_path:
                lines.append(f"  - Tracking file: {self.tracker.tracking_file_path}")
            else:
                lines.append(f"  - Tracking: in-memory ({len(self.tracker.df)} rows)")
        return "\n".join(lines)

    def __repr__(self):
        if self._in_memory:
            return "ProjectSettings(in_memory=True)"
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
        from .importers.bvh import from_bvh
        settings = from_bvh(args.bvh)
        settings.persist(destination)
    else:
        # Create empty project
        destination.mkdir(parents=True, exist_ok=True)
        config_path = destination / "project.toml"
        data = {
            "project": {
                "number_of_frames": 0,
                "frames_per_second": 120.0,
            },
        }
        with open(config_path, "w") as f:
            toml.dump(data, f)
        print(f"Empty project created at {config_path}")


if __name__ == "__main__":
    init_project()

