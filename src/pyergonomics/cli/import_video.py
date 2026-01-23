"""
CLI script for importing video files into pyergonomics projects.
"""

import argparse
from pathlib import Path

from . import validate_destination


def main():
    parser = argparse.ArgumentParser(
        description="Import a video file into a pyergonomics project."
    )
    parser.add_argument(
        "video_file",
        type=str,
        help="Path to the video file."
    )
    parser.add_argument(
        "destination",
        type=str,
        help="Destination folder for the project."
    )

    args = parser.parse_args()
    destination = Path(args.destination)

    # Validate destination
    error = validate_destination(destination)
    if error:
        print(error)
        return 1

    # Import - init_from_video handles its own saving
    from ..importers.video import init_from_video

    init_from_video(destination, args.video_file)

    return 0


if __name__ == "__main__":
    exit(main())
