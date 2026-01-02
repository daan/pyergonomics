from .app_state import AppState

from .timeline import TimelinePainter, AxisPainter
from PySide6.QtQml import qmlRegisterType


def register_types():
    # qmlRegisterType(PythonClass, URI, VersionMajor, VersionMinor, QMLName)
    qmlRegisterType(TimelinePainter, "PyeHelpers", 0, 1, "TimelinePainter")
    qmlRegisterType(AxisPainter, "PyeHelpers", 0, 1, "AxisPainter")
