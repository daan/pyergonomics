"""
CLI script for importing Stereolabs ZED SVO2 files into pyergonomics projects.
"""

import argparse
from pathlib import Path

from . import validate_destination, persist_project


def main():
    parser = argparse.ArgumentParser(
        description="Import a Stereolabs ZED SVO2 file into a pyergonomics project."
    )
    parser.add_argument(
        "svo_file",
        type=str,
        help="Path to the SVO2 file."
    )
    parser.add_argument(
        "destination",
        type=str,
        help="Destination folder for the project."
    )
    parser.add_argument(
        "--body-format",
        type=str,
        choices=["body_18", "body_34"],
        default="body_34",
        help="Body tracking format (default: body_34)."
    )
    parser.add_argument(
        "--detection-confidence",
        type=int,
        default=40,
        help="Detection confidence threshold 0-100 (default: 40)."
    )
    parser.add_argument(
        "--no-extract-frames",
        action="store_true",
        help="Skip extracting video frames (default: frames are extracted)."
    )

    args = parser.parse_args()
    destination = Path(args.destination)

    # Validate destination
    error = validate_destination(destination)
    if error:
        print(error)
        return 1

    # Import
    from ..importers.zed import from_zed, BodyFormat

    body_format = BodyFormat.BODY_34 if args.body_format == "body_34" else BodyFormat.BODY_18

    extract_frames = not args.no_extract_frames

    settings = from_zed(
        args.svo_file,
        body_format=body_format,
        detection_confidence=args.detection_confidence,
        extract_frames=extract_frames,
        output_dir=destination if extract_frames else None,
    )
    persist_project(settings, destination)

    return 0


if __name__ == "__main__":
    exit(main())
