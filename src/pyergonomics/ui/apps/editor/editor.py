import sys
import argparse
import warnings
from pathlib import Path
import importlib.resources

# Suppress pkg_resources deprecation warning from bvhtoolbox (loaded via pose_skeletons)
warnings.filterwarnings("ignore", message="pkg_resources is deprecated", category=UserWarning)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtCore import QUrl

from pyergonomics.ui.app_state import AppState
from pyergonomics.ui.models.person_model import PersonModel
from pyergonomics.ui.models.people_in_frame_proxy import PeopleInFrameProxyModel
from pyergonomics.ui.models.people_in_time_proxy import PeopleInTimeProxyModel
from pyergonomics.ui.skeleton_provider import SkeletonProvider
from pyergonomics.ui.skeleton_geometry import SkeletonGeometry
from pyergonomics.ui.graph_painter import GraphPainter
import pyergonomics.ui as pye_ui
import qtquick3d_opencv_helpers

# Simple palette for the example
DARK2_PALETTE = [
    "#1b9e77", "#d95f02", "#7570b3", "#e7298a", 
    "#66a61e", "#e6ab02", "#a6761d", "#666666"
]

class FrameSource(QQuickImageProvider):
    def __init__(self, app_state):
        super().__init__(QQuickImageProvider.Image)
        self.app_state = app_state

    def requestImage(self, id, size, requestedSize):
        try:
            if not self.app_state.config:
                return QImage()

            # Strip query parameters (e.g., "0?v=1" -> "0")
            frame_id = id.split("?")[0]
            frame_num = int(frame_id)
            filepath = self.app_state.config.frame_path(frame_num)
            
            image = QImage(str(filepath))
            
            if not image.isNull():
                size.setWidth(image.width())
                size.setHeight(image.height())
            
            return image
        except Exception as e:
            print(f"Error loading frame {id}: {e}")
            return QImage()

def main():
    parser = argparse.ArgumentParser(description="Editor")
    parser.add_argument("project_path", nargs="?", help="Path to project folder")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    try:
        app_state = AppState(args.project_path)
    except FileNotFoundError as e:
        print(e)
        # If project path was provided but invalid, we might want to exit or just start empty.
        # For now, let's start empty if it fails, or maybe just print error.
        # But AppState handles None now, so this catch might be for when a path IS provided but bad.
        if args.project_path:
             print(f"Could not load project at {args.project_path}. Starting with empty state.")
             app_state = AppState(None)
        else:
             app_state = AppState(None)

    # Register PyeHelpers
    pye_ui.register_types()
    
    # Register GraphPainter
    qmlRegisterType(GraphPainter, "PyeHelpers", 0, 1, "GraphPainter")

    # Register SkeletonGeometry for 3D view
    qmlRegisterType(SkeletonGeometry, "PyeHelpers", 1, 0, "SkeletonGeometry")
    
    with importlib.resources.as_file(
        importlib.resources.files("pyergonomics.ui") / "qml"
    ) as qml_path:
        engine.addImportPath(str(qml_path))

    # Register CvHelpers for 3D view
    qtquick3d_opencv_helpers.register_qml_types()
    with importlib.resources.as_file(
        importlib.resources.files("qtquick3d_opencv_helpers") / "qml"
    ) as qml_path:
        engine.addImportPath(str(qml_path))

    # Models
    person_model = PersonModel()
    if app_state.tracker:
        person_model.populate_from_tracker(app_state.tracker)
    app_state.set_person_model(person_model)

    proxy_model = PeopleInFrameProxyModel()
    proxy_model.setSourceModel(person_model)

    timeline_proxy_model = PeopleInTimeProxyModel()
    timeline_proxy_model.setSourceModel(person_model)

    # Connect current frame changes to proxy model
    app_state.currentFrameChanged.connect(
        lambda: proxy_model.setCurrentFrame(app_state.currentFrame)
    )
    proxy_model.setCurrentFrame(app_state.currentFrame)

    # Frame Source
    # Pass app_state instead of config directly, as config might be None initially
    frame_source = FrameSource(app_state)
    engine.addImageProvider("frame_source", frame_source)

    # Skeleton Provider
    skeleton_provider = SkeletonProvider(app_state)

    # Context Properties
    engine.rootContext().setContextProperty("appState", app_state)
    engine.rootContext().setContextProperty("personModel", person_model)
    engine.rootContext().setContextProperty("peopleFrameModel", proxy_model)
    engine.rootContext().setContextProperty("peopleModel", timeline_proxy_model)
    engine.rootContext().setContextProperty("skeletonProvider", skeleton_provider)
    engine.rootContext().setContextProperty("dark2palette", DARK2_PALETTE)

    qml_file = Path(__file__).parent / "editor.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
