"""
CLI script for anonymizing video frames in a pyergonomics project.

Uses deface (https://github.com/ORB-HD/deface) to blur faces in extracted
frames. The original frames are preserved in a frames-org/ folder.
"""

import argparse
from pathlib import Path

import cv2
from tqdm import tqdm


def main():
    parser = argparse.ArgumentParser(
        description="Anonymize video frames in a pyergonomics project by blurring faces."
    )
    parser.add_argument(
        "project",
        type=str,
        help="Path to the project folder (containing frames/)."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.2,
        help="Detection confidence threshold (default: 0.2)."
    )
    parser.add_argument(
        "--replacewith",
        type=str,
        choices=["blur", "solid", "mosaic", "none"],
        default="blur",
        help="Anonymization method (default: blur)."
    )
    parser.add_argument(
        "--mask-scale",
        type=float,
        default=1.3,
        help="Scale factor for the face mask (default: 1.3)."
    )
    parser.add_argument(
        "--ellipse",
        action="store_true",
        help="Use elliptical mask instead of rectangular."
    )

    args = parser.parse_args()

    try:
        from deface.centerface import CenterFace
        from deface.deface import anonymize_frame
    except ImportError:
        print(
            "Error: deface is required for anonymization.\n"
            "Install it with: pip install deface"
        )
        return 1

    project_dir = Path(args.project)
    frames_dir = project_dir / "frames"
    frames_org_dir = project_dir / "frames-org"

    if not project_dir.is_dir():
        print(f"Error: Project folder not found: {project_dir}")
        return 1

    if not frames_dir.is_dir():
        print(f"Error: No frames/ folder in {project_dir}")
        return 1

    if frames_org_dir.exists():
        print(f"Error: {frames_org_dir} already exists. Already anonymized?")
        return 1

    # Collect frame files
    frame_files = sorted(frames_dir.glob("*.png"))
    if not frame_files:
        print(f"Error: No PNG files found in {frames_dir}")
        return 1

    # Rename frames/ to frames-org/
    frames_dir.rename(frames_org_dir)
    frames_dir.mkdir()

    # Initialize face detector once
    centerface = CenterFace(in_shape=None, backend="auto")

    print(f"Anonymizing {len(frame_files)} frames...")

    for frame_file in tqdm(frame_files, desc="Anonymizing"):
        frame = cv2.imread(str(frames_org_dir / frame_file.name))
        if frame is None:
            continue

        dets, _ = centerface(frame, threshold=args.threshold)
        anonymize_frame(
            dets, frame,
            mask_scale=args.mask_scale,
            replacewith=args.replacewith,
            ellipse=args.ellipse,
            draw_scores=False,
            replaceimg=None,
            mosaicsize=20,
        )

        cv2.imwrite(str(frames_dir / frame_file.name), frame)

    print(f"Done. Original frames preserved in {frames_org_dir}")
    return 0


if __name__ == "__main__":
    exit(main())
