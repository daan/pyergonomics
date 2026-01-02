import sys
import argparse
from pathlib import Path
import importlib.resources

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
import pyergonomics.ui as pye_ui

# Simple palette for the example
DARK2_PALETTE = [
    "#1b9e77", "#d95f02", "#7570b3", "#e7298a", 
    "#66a61e", "#e6ab02", "#a6761d", "#666666"
]

class FrameSource(QQuickImageProvider):
    def __init__(self, settings):
        super().__init__(QQuickImageProvider.Image)
        self.settings = settings

    def requestImage(self, id, size, requestedSize):
        try:
            frame_num = int(id)
            filepath = self.settings.frame_path(frame_num)
            
            image = QImage(str(filepath))
            
            if not image.isNull():
                size.setWidth(image.width())
                size.setHeight(image.height())
            
            return image
        except Exception as e:
            print(f"Error loading frame {id}: {e}")
            return QImage()

def main():
    parser = argparse.ArgumentParser(description="Track View Example")
    parser.add_argument("project_path", help="Path to project folder")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    try:
        app_state = AppState(args.project_path)
    except FileNotFoundError as e:
        print(e)
        sys.exit(-1)

    if app_state.totalFrames == 0:
        print(f"No frames configured in project.toml.")
        sys.exit(-1)

    # Register PyeHelpers
    pye_ui.register_types()
    with importlib.resources.as_file(
        importlib.resources.files("pyergonomics.ui") / "qml"
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
    frame_source = FrameSource(app_state.config)
    engine.addImageProvider("frame_source", frame_source)

    # Skeleton Provider
    skeleton_provider = SkeletonProvider(app_state)

    # Context Properties
    engine.rootContext().setContextProperty("appState", app_state)
    engine.rootContext().setContextProperty("peopleFrameModel", proxy_model)
    engine.rootContext().setContextProperty("peopleModel", timeline_proxy_model)
    engine.rootContext().setContextProperty("skeletonProvider", skeleton_provider)
    engine.rootContext().setContextProperty("dark2palette", DARK2_PALETTE)

    qml_file = Path(__file__).parent / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
