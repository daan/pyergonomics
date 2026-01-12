from .project_settings import ProjectSettings, ProjectNotFoundError, init_project
from .tracker import Tracker, AssessmentExistsError, add_pose_assessment_columns
from .pose_assessment import make_pose_assessment

# Lazy import track_video to prevent loading torch/ultralytics when just using the UI/Tracker
def track_video(*args, **kwargs):
    from .track_video import track_video as _track_video
    return _track_video(*args, **kwargs)
