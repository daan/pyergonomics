import sys
import argparse
from pathlib import Path
import importlib.resources

from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtCore import QUrl

from pyergonomics.ui.app_state import AppState
from pyergonomics.ui.models.person_model import PersonModel
from pyergonomics.ui.graph_painter import GraphPainter
import pyergonomics.ui as pye_ui

def main():
    parser = argparse.ArgumentParser(description="Assessment View Example")
    parser.add_argument("project_path", help="Path to project folder")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    try:
        app_state = AppState(args.project_path)
    except FileNotFoundError as e:
        print(e)
        sys.exit(-1)

    # Register PyeHelpers
    pye_ui.register_types()
    
    # Register GraphPainter
    qmlRegisterType(GraphPainter, "PyeHelpers", 0, 1, "GraphPainter")
    
    with importlib.resources.as_file(
        importlib.resources.files("pyergonomics.ui") / "qml"
    ) as qml_path:
        engine.addImportPath(str(qml_path))

    # Models
    person_model = PersonModel()
    if app_state.tracker:
        person_model.populate_from_tracker(app_state.tracker)
    app_state.set_person_model(person_model)

    # Context Properties
    engine.rootContext().setContextProperty("appState", app_state)
    engine.rootContext().setContextProperty("personModel", person_model)

    qml_file = Path(__file__).parent / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
