import pytest
import numpy as np

from pyergonomics import make_pose_assessment


class TestMakePoseAssessment:
    @pytest.fixture
    def skeleton(self):
        """Get Xsens skeleton definition."""
        from pose_skeletons import get_skeleton_def
        return get_skeleton_def("xsens")

    @pytest.fixture
    def standing_pose(self, skeleton):
        """Create a standing pose with arms down for Xsens skeleton."""
        # Create array large enough for all Xsens joints (at least 20)
        joints = np.zeros((23, 3))

        # Head and neck
        joints[skeleton.head] = [0.0, 0.0, 1.7]
        joints[skeleton.neck] = [0.0, 0.0, 1.5]

        # Shoulders
        joints[skeleton.l_shoulder] = [0.2, 0.0, 1.45]
        joints[skeleton.r_shoulder] = [-0.2, 0.0, 1.45]

        # Elbows
        joints[skeleton.l_elbow] = [0.35, 0.0, 1.2]
        joints[skeleton.r_elbow] = [-0.35, 0.0, 1.2]

        # Wrists
        joints[skeleton.l_wrist] = [0.45, 0.0, 0.95]
        joints[skeleton.r_wrist] = [-0.45, 0.0, 0.95]

        # Hips
        joints[skeleton.l_hip] = [0.1, 0.0, 1.0]
        joints[skeleton.r_hip] = [-0.1, 0.0, 1.0]

        return joints

    def test_returns_dict(self, skeleton, standing_pose):
        result = make_pose_assessment(skeleton, standing_pose)
        assert isinstance(result, dict)

    def test_contains_trunk_metrics(self, skeleton, standing_pose):
        result = make_pose_assessment(skeleton, standing_pose)
        assert "trunk_bending" in result
        assert "trunk_side_bending" in result
        assert "trunk_twist" in result

    def test_contains_arm_metrics(self, skeleton, standing_pose):
        result = make_pose_assessment(skeleton, standing_pose)
        assert "left_elbow_above_shoulder" in result
        assert "right_elbow_above_shoulder" in result
        assert "left_hand_above_head_level" in result
        assert "right_hand_above_head_level" in result
        assert "left_far_reach" in result
        assert "right_far_reach" in result

    def test_contains_planes(self, skeleton, standing_pose):
        result = make_pose_assessment(skeleton, standing_pose)
        assert "transverse_plane" in result
        assert "coronal_plane" in result
        assert "sagittal_plane" in result
        assert "ground_plane" in result

    def test_standing_pose_minimal_bending(self, skeleton, standing_pose):
        result = make_pose_assessment(skeleton, standing_pose)
        # Standing upright should have near-zero bending
        assert abs(result["trunk_bending"]) < 10  # Less than 10 degrees

    def test_elbow_below_shoulder_negative(self, skeleton, standing_pose):
        result = make_pose_assessment(skeleton, standing_pose)
        # With arms down, elbows should be below shoulders
        assert result["left_elbow_above_shoulder"] < 0
        assert result["right_elbow_above_shoulder"] < 0

    def test_hands_below_head(self, skeleton, standing_pose):
        result = make_pose_assessment(skeleton, standing_pose)
        # With arms down, hands should be below head
        assert result["left_hand_above_head_level"] < 0
        assert result["right_hand_above_head_level"] < 0
