import cv2
import toml
import os
from pathlib import Path

from ..configuration import Configuration


def init_from_video(destination_folder, video_file=None):
    output_dir = Path(destination_folder)
    frames_dir = output_dir / "frames"

    if output_dir.exists():
        print(
            f"Error: Directory '{output_dir}' already exists. Please remove it or choose a different video."
        )
        return

    os.makedirs(frames_dir)
    print(f"Created directory: {frames_dir}")

    config_path = output_dir / "project.toml"
    config = Configuration(config_path)

    if video_file:
        video_path = Path(video_file).resolve()
        if not video_path.is_file():
            print(f"Error: Video file not found at {video_file}")
            return

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

        config.number_of_frames = count
        config.frames_per_second = fps
        config.source_video = str(video_path)
        config.width = width
        config.height = height
    else:
        config.number_of_frames = 0
        config.frames_per_second = 25.0
        config.source_video = ""
        config.width = 0
        config.height = 0

    config.save()

    print(f"Configuration file created at {config_path}")
