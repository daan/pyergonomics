# ZED Body Tracking Viewer

Qt/QML application for real-time visualization of ZED body tracking data.

## Usage

```bash
# Live camera
python main.py

# SVO2 file playback
python main.py path/to/recording.svo2

# Options
python main.py recording.svo2 --body-format 18  # Use BODY_18 (default: 34)
python main.py recording.svo2 --no-fitting       # Disable body fitting
python main.py recording.svo2 --smoothing 0.0    # No smoothing (default: 0.5)
```

## Controls

- **Mouse drag**: Orbit camera
- **Scroll**: Zoom
- **Zoom to Fit**: Button to frame all skeletons
