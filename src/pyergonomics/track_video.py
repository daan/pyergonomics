import argparse
import sys
from pathlib import Path
import polars as pl
from tqdm import tqdm


# Handle imports depending on execution context
if __name__ == "__main__" and __package__ is None:
    # When run as a script, add the source root to path and import as package
    # This ensures relative imports in project_settings work correctly
    file_path = Path(__file__).resolve()
    src_path = file_path.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from pyergonomics.project_settings import ProjectSettings
else:
    # When imported as a module
    from .project_settings import ProjectSettings

def track_video(project_path, model_name='yolo11x-pose.pt'):
    """
    Process the video defined in the project settings using YOLO11 and BoT-SORT,
    extract bounding boxes, and save them to a parquet file.
    """
    from ultralytics import YOLO
    import cv2

    # Initialize project settings
    project_path = Path(project_path)
    if not project_path.exists():
        print(f"Error: Project path '{project_path}' does not exist.")
        return

    settings = ProjectSettings(project_path)
    
    # Get video path
    video_rel_path = settings.source_video
    if not video_rel_path:
        print("Error: No source video defined in project settings.")
        return

    # Resolve video path (assuming it's relative to project folder if not absolute)
    video_path = Path(video_rel_path)
    if not video_path.is_absolute():
        # If project_path is a file (project.toml), use its parent
        base_dir = project_path if project_path.is_dir() else project_path.parent
        video_path = base_dir / video_rel_path

    if not video_path.exists():
        print(f"Error: Video file '{video_path}' not found.")
        return

    print(f"Loading model: {model_name}")
    model = YOLO(model_name)

    print(f"Opening video: {video_path}")
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    data = []

    print("Starting tracking...")
    # Process video frame by frame
    for frame_idx in tqdm(range(total_frames), unit="frame"):
        success, frame = cap.read()
        if not success:
            break

        # Run YOLO11 tracking
        # persist=True: maintain tracks between frames
        # tracker="botsort.yaml": explicitly use BoT-SORT
        results = model.track(frame, persist=True, tracker="botsort.yaml", verbose=False)

        if results:
            result = results[0]
            # Check if we have boxes and IDs (IDs are needed for tracking)
            if result.boxes is not None and result.boxes.id is not None:
                # Get boxes in xyxy format (top-left, bottom-right)
                boxes_xyxy = result.boxes.xyxy.cpu().numpy()
                track_ids = result.boxes.id.int().cpu().numpy()

                for i, track_id in enumerate(track_ids):
                    x1, y1, x2, y2 = boxes_xyxy[i]
                    
                    # Convert to x, y, w, h (top-left x, top-left y, width, height)
                    w = x2 - x1
                    h = y2 - y1
                    x = x1
                    y = y1

                    data.append({
                        "frame": frame_idx,
                        "person": track_id,
                        "x": float(x),
                        "y": float(y),
                        "w": float(w),
                        "h": float(h)
                    })

    cap.release()

    if not data:
        print("No tracking data collected.")
        return

    # Create Polars DataFrame
    df = pl.DataFrame(data)

    # Determine output path
    # Check if a tracking file is already configured
    tracking_config = settings.data.get("tracking", {})
    tracking_filename = tracking_config.get("tracking_file")

    if not tracking_filename:
        tracking_filename = "tracking.parquet"
        print(f"No tracking file configured. Setting to '{tracking_filename}'")
        settings.set_tracking_file(tracking_filename)
        settings.save()

    # Save DataFrame
    # Ensure we write to the project directory
    project_dir = project_path if project_path.is_dir() else project_path.parent
    output_path = project_dir / tracking_filename
    
    df.write_parquet(output_path)
    print(f"Tracking data saved to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track people in video using YOLO11 and BoT-SORT.")
    parser.add_argument("project_path", type=str, help="Path to the project folder or project.toml")
    parser.add_argument("--model", type=str, default="yolo11x-pose.pt", help="YOLO model to use (default: yolo11x-pose.pt)")
    
    args = parser.parse_args()
    
    track_video(args.project_path, args.model)
