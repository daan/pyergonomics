import sys
from pathlib import Path
import importlib.resources

from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtCore import QUrl

from pyergonomics.ui.app_state import AppState
import pyergonomics.ui as pye_ui

class FrameSource(QQuickImageProvider):
    def __init__(self, settings):
        super().__init__(QQuickImageProvider.Image)
        self.settings = settings

    def requestImage(self, id, size, requestedSize):
        try:
            # Strip query parameters (e.g., "0?v=1" -> "0")
            frame_id = id.split("?")[0]
            frame_num = int(frame_id)
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
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <project_folder_path>")
        sys.exit(-1)

    project_path = Path(sys.argv[1])

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    try:
        app_state = AppState(project_path)
    except FileNotFoundError as e:
        print(e)
        sys.exit(-1)

    # Register Image Provider
    frame_source = FrameSource(app_state.config)
    engine.addImageProvider("frame_source", frame_source)

    # Register PyeHelpers
    pye_ui.register_types()
    with importlib.resources.as_file(
        importlib.resources.files("pyergonomics.ui") / "qml"
    ) as qml_path:
        engine.addImportPath(str(qml_path))

    engine.rootContext().setContextProperty("appState", app_state)

    qml_file = Path(__file__).parent / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
