import sys
from pathlib import Path
import importlib.resources

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtCore import QUrl

# Updated imports to point to the new package structure
from pyergonomics.ui.app_state import AppState
from pyergonomics.ui.skeleton_geometry import SkeletonGeometry
from pyergonomics.ui.skeleton_provider import SkeletonProvider
import pyergonomics.ui as pye_ui

import qtquick3d_opencv_helpers

# From d3-scale-chromatic Dark2
DARK2_PALETTE = [
    "#1b9e77",
    "#d95f02",
    "#7570b3",
    "#e7298a",
    "#66a61e",
    "#e6ab02",
    "#a6761d",
    "#666666",
]

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <project_folder_path>")
        sys.exit(-1)

    project_path = Path(sys.argv[1])

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    qmlRegisterType(SkeletonGeometry, "PyeHelpers", 1, 0, "SkeletonGeometry")

    try:
        app_state = AppState(project_path)
    except FileNotFoundError as e:
        print(e)
        sys.exit(-1)

    if app_state.totalFrames == 0:
        print(f"No frames configured in project.toml.")
        # We continue to allow viewing the setup even if frames are 0

    pye_ui.register_types()
    
    # Add import path for PyeHelpers QML
    with importlib.resources.as_file(
        importlib.resources.files("pyergonomics.ui") / "qml"
    ) as qml_path:
        engine.addImportPath(str(qml_path))

    qtquick3d_opencv_helpers.register_qml_types()

    with importlib.resources.as_file(
        importlib.resources.files("qtquick3d_opencv_helpers") / "qml"
    ) as qml_path:
        engine.addImportPath(str(qml_path))

    # Use the shared SkeletonProvider
    skeleton_provider = SkeletonProvider(app_state)
    
    # Expose to QML
    engine.rootContext().setContextProperty("skeletonProvider", skeleton_provider)
    engine.rootContext().setContextProperty("appState", app_state)
    engine.rootContext().setContextProperty("dark2palette", DARK2_PALETTE)

    qml_file = Path(__file__).parent / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
