"""
CLI script for importing BVH files into pyergonomics projects.
"""

import argparse
from pathlib import Path

from . import validate_destination, persist_project


def main():
    parser = argparse.ArgumentParser(
        description="Import a BVH file into a pyergonomics project."
    )
    parser.add_argument(
        "bvh_file",
        type=str,
        help="Path to the BVH file."
    )
    parser.add_argument(
        "destination",
        type=str,
        help="Destination folder for the project."
    )
    parser.add_argument(
        "--unit",
        type=str,
        choices=["m", "cm", "mm", "inch"],
        default="m",
        help="Unit of the BVH position data (default: m)."
    )
    parser.add_argument(
        "--ignore-first-frame",
        action="store_true",
        help="Skip the first frame (useful for BVH files with T-pose at origin)."
    )

    args = parser.parse_args()
    destination = Path(args.destination)

    # Validate destination
    error = validate_destination(destination)
    if error:
        print(error)
        return 1

    # Import
    from ..importers.bvh import from_bvh
    from ..importers import Unit

    unit_map = {"m": Unit.M, "cm": Unit.CM, "mm": Unit.MM, "inch": Unit.INCH}
    unit = unit_map[args.unit]

    settings = from_bvh(args.bvh_file, unit=unit, ignore_first_frame=args.ignore_first_frame)
    persist_project(settings, destination)

    return 0


if __name__ == "__main__":
    exit(main())
