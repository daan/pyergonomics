#!/usr/bin/env python3
"""ZED Body Tracking Viewer - Qt/QML application for viewing ZED skeleton data."""

import sys
import argparse
from pathlib import Path
import importlib.resources

from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtCore import QUrl, QObject, Property, Signal
import pyzed.sl as sl

from zed_body_tracker import ZedBodyTracker, ZedThread
from zed_skeleton_provider import ZedSkeletonProvider

# Import pyergonomics UI components
from pyergonomics.ui.skeleton_geometry import SkeletonGeometry
import pyergonomics.ui as pye_ui
import qtquick3d_opencv_helpers

# Color palette
DARK2_PALETTE = [
    "#1b9e77", "#d95f02", "#7570b3", "#e7298a",
    "#66a61e", "#e6ab02", "#a6761d", "#666666"
]


class AppState(QObject):
    """Simple app state for the ZED viewer."""

    selectedPersonIdsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_person_ids = []

    @Property("QVariantList", notify=selectedPersonIdsChanged)
    def selectedPersonIds(self):
        return self._selected_person_ids


def main():
    parser = argparse.ArgumentParser(description="ZED Body Tracking Viewer")
    parser.add_argument("svo_path", nargs="?", help="Path to SVO2 file (omit for live camera)")
    parser.add_argument("--body-format", choices=["18", "34"], default="34",
                        help="Body format: 18 or 34 joints (default: 34)")
    parser.add_argument("--no-fitting", action="store_true",
                        help="Disable body fitting")
    parser.add_argument("--smoothing", type=float, default=0.5,
                        help="Skeleton smoothing (0.0-1.0, default: 0.5)")
    args = parser.parse_args()

    # Validate SVO path if provided
    if args.svo_path and not Path(args.svo_path).exists():
        print(f"Error: SVO file not found: {args.svo_path}")
        sys.exit(1)

    body_format = sl.BODY_FORMAT.BODY_34 if args.body_format == "34" else sl.BODY_FORMAT.BODY_18

    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    # Register PyeHelpers types
    pye_ui.register_types()
    qmlRegisterType(SkeletonGeometry, "PyeHelpers", 1, 0, "SkeletonGeometry")

    # Add PyeHelpers QML import path
    with importlib.resources.as_file(
        importlib.resources.files("pyergonomics.ui") / "qml"
    ) as qml_path:
        engine.addImportPath(str(qml_path))

    # Register CvHelpers for Grid
    qtquick3d_opencv_helpers.register_qml_types()
    with importlib.resources.as_file(
        importlib.resources.files("qtquick3d_opencv_helpers") / "qml"
    ) as qml_path:
        engine.addImportPath(str(qml_path))

    # Create app state and skeleton provider
    app_state = AppState()
    skeleton_provider = ZedSkeletonProvider()

    # Create ZED tracker (pass skeleton_provider for direct updates)
    tracker = ZedBodyTracker(
        skeleton_provider=skeleton_provider,
        svo_path=args.svo_path,
        body_format=body_format,
        enable_body_fitting=not args.no_fitting,
        skeleton_smoothing=args.smoothing,
    )

    # Connect tracker signals
    tracker.error.connect(lambda msg: print(f"Error: {msg}"))
    tracker.finished.connect(lambda: print("Playback finished"))

    # Create thread for tracker
    tracker_thread = ZedThread(tracker)

    # Set context properties
    engine.rootContext().setContextProperty("appState", app_state)
    engine.rootContext().setContextProperty("skeletonProvider", skeleton_provider)
    engine.rootContext().setContextProperty("dark2palette", DARK2_PALETTE)

    # Load QML
    qml_file = Path(__file__).parent / "zed_viewer.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        print("Failed to load QML")
        sys.exit(-1)

    # Start tracking thread
    tracker_thread.start()

    # Run app
    ret = app.exec()

    # Cleanup
    tracker.stop()
    tracker_thread.quit()
    tracker_thread.wait()

    sys.exit(ret)


if __name__ == "__main__":
    main()
