# --- File: pose_skeletons.py ---

from enum import Enum, IntEnum, auto
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Type, Set

# --- 1. Define the Keypoint Enums ---
# By defining Enums, you get type safety and auto-completion.

class CocoKeypoints(Enum):
    """Keypoints from the COCO dataset (17 points)."""
    NOSE = 0
    LEFT_EYE = 1
    RIGHT_EYE = 2
    LEFT_EAR = 3
    RIGHT_EAR = 4
    LEFT_SHOULDER = 5
    RIGHT_SHOULDER = 6
    LEFT_ELBOW = 7
    RIGHT_ELBOW = 8
    LEFT_WRIST = 9
    RIGHT_WRIST = 10
    LEFT_HIP = 11
    RIGHT_HIP = 12
    LEFT_KNEE = 13
    RIGHT_KNEE = 14
    LEFT_ANKLE = 15
    RIGHT_ANKLE = 16

class KinectAzureKeypoints(Enum):
    """Keypoints from the Kinect Azure SDK (32 points)."""
    PELVIS = 0
    SPINE_NAVAL = 1
    SPINE_CHEST = 2
    NECK = 3
    CLAVICLE_LEFT = 4
    SHOULDER_LEFT = 5
    ELBOW_LEFT = 6
    WRIST_LEFT = 7
    HAND_LEFT = 8
    HANDTIP_LEFT = 9
    THUMB_LEFT = 10
    CLAVICLE_RIGHT = 11
    SHOULDER_RIGHT = 12
    ELBOW_RIGHT = 13
    WRIST_RIGHT = 14
    HAND_RIGHT = 15
    HANDTIP_RIGHT = 16
    THUMB_RIGHT = 17
    HIP_LEFT = 18
    KNEE_LEFT = 19
    ANKLE_LEFT = 20
    FOOT_LEFT = 21
    HIP_RIGHT = 22
    KNEE_RIGHT = 23
    ANKLE_RIGHT = 24
    FOOT_RIGHT = 25
    HEAD = 26
    NOSE = 27
    EYE_LEFT = 28
    EAR_LEFT = 29
    EYE_RIGHT = 30
    EAR_RIGHT = 31


class OptitrackJoints(IntEnum):
    """
    Enum representing Mixamo character joint names as integers.
    """
    Hips = 0
    Spine = 1
    Spine1 = 2
    Neck = 3
    Head = 4
    LeftShoulder = 5
    LeftArm = 6
    LeftForeArm = 7
    LeftHand = 8
    LeftHandThumb1 = 9
    LeftHandThumb2 = 10
    LeftHandThumb3 = 11
    LeftHandIndex1 = 12
    LeftHandIndex2 = 13
    LeftHandIndex3 = 14
    LeftHandMiddle1 = 15
    LeftHandMiddle2 = 16
    LeftHandMiddle3 = 17
    LeftHandRing1 = 18
    LeftHandRing2 = 19
    LeftHandRing3 = 20
    LeftHandPinky1 = 21
    LeftHandPinky2 = 22
    LeftHandPinky3 = 23
    RightShoulder = 24
    RightArm = 25
    RightForeArm = 26
    RightHand = 27
    RightHandThumb1 = 28
    RightHandThumb2 = 29
    RightHandThumb3 = 30
    RightHandIndex1 = 31
    RightHandIndex2 = 32
    RightHandIndex3 = 33
    RightHandMiddle1 = 34
    RightHandMiddle2 = 35
    RightHandMiddle3 = 36
    RightHandRing1 = 37
    RightHandRing2 = 38
    RightHandRing3 = 39
    RightHandPinky1 = 40
    RightHandPinky2 = 41
    RightHandPinky3 = 42
    LeftUpLeg = 43
    LeftLeg = 44
    LeftFoot = 45
    LeftToeBase = 46
    RightUpLeg = 47
    RightLeg = 48
    RightFoot = 49
    RightToeBase = 50

# --- 2. Define the "Skeleton Definition" Class ---
# This is the class you asked for. It holds the definition for ONE skeleton.

@dataclass(frozen=True)
class SkeletonDef:
    """
    An immutable definition of a skeleton structure.
    
    Contains the keypoint enum and the bone hierarchy.
    """
    # The Enum class itself (e.g., CocoKeypoints)
    keypoints: Type[Enum]
    
    # The hierarchy as pairs of Enum members
    bones: Set[Tuple[Enum, Enum]]

    # We use __post_init__ to auto-generate helpful lookup tables
    # 'field(init=False)' means they aren't part of the __init__
    keypoint_to_index: Dict[Enum, int] = field(init=False)
    index_to_keypoint: Dict[int, Enum] = field(init=False)
    
    def __post_init__(self):
        # We must use object.__setattr__ because the class is frozen
        keypoint_map = {kp: kp.value for kp in self.keypoints}
        object.__setattr__(self, 'keypoint_to_index', keypoint_map)
        
        index_map = {kp.value: kp for kp in self.keypoints}
        object.__setattr__(self, 'index_to_keypoint', index_map)

    @property
    def num_keypoints(self) -> int:
        """Returns the total number of keypoints in this skeleton."""
        return len(self.keypoints)

    @property
    def bone_indices(self) -> List[Tuple[int, int]]:
        """
        Returns the bone hierarchy as a list of (start_index, end_index) pairs.
        Useful for drawing or libraries that need integer indices.
        """
        return [
            (self.keypoint_to_index[kp1], self.keypoint_to_index[kp2])
            for kp1, kp2 in self.bones
        ]

# --- 3. Define the Hierarchies (Bones) ---
# We use a set of tuples for the bones for efficient lookup
# and to ensure no duplicates.

COCO_BONES: Set[Tuple[Enum, Enum]] = {
    (CocoKeypoints.NOSE, CocoKeypoints.LEFT_EYE),
    (CocoKeypoints.NOSE, CocoKeypoints.RIGHT_EYE),
    (CocoKeypoints.LEFT_EYE, CocoKeypoints.LEFT_EAR),
    (CocoKeypoints.RIGHT_EYE, CocoKeypoints.RIGHT_EAR),
    (CocoKeypoints.LEFT_SHOULDER, CocoKeypoints.RIGHT_SHOULDER),
    (CocoKeypoints.LEFT_SHOULDER, CocoKeypoints.LEFT_ELBOW),
    (CocoKeypoints.LEFT_ELBOW, CocoKeypoints.LEFT_WRIST),
    (CocoKeypoints.RIGHT_SHOULDER, CocoKeypoints.RIGHT_ELBOW),
    (CocoKeypoints.RIGHT_ELBOW, CocoKeypoints.RIGHT_WRIST),
    (CocoKeypoints.LEFT_SHOULDER, CocoKeypoints.LEFT_HIP),
    (CocoKeypoints.RIGHT_SHOULDER, CocoKeypoints.RIGHT_HIP),
    (CocoKeypoints.LEFT_HIP, CocoKeypoints.RIGHT_HIP),
    (CocoKeypoints.LEFT_HIP, CocoKeypoints.LEFT_KNEE),
    (CocoKeypoints.LEFT_KNEE, CocoKeypoints.LEFT_ANKLE),
    (CocoKeypoints.RIGHT_HIP, CocoKeypoints.RIGHT_KNEE),
    (CocoKeypoints.RIGHT_KNEE, CocoKeypoints.RIGHT_ANKLE),
}


KINECT_AZURE_BONES: Set[Tuple[Enum, Enum]] = {
    (KinectAzureKeypoints.PELVIS, KinectAzureKeypoints.SPINE_NAVAL),
    (KinectAzureKeypoints.SPINE_NAVAL, KinectAzureKeypoints.SPINE_CHEST),
    (KinectAzureKeypoints.SPINE_CHEST, KinectAzureKeypoints.NECK),
    (KinectAzureKeypoints.NECK, KinectAzureKeypoints.HEAD),
    (KinectAzureKeypoints.HEAD, KinectAzureKeypoints.NOSE),
    (KinectAzureKeypoints.HEAD, KinectAzureKeypoints.EYE_LEFT),
    (KinectAzureKeypoints.HEAD, KinectAzureKeypoints.EYE_RIGHT),
    (KinectAzureKeypoints.HEAD, KinectAzureKeypoints.EAR_LEFT),
    (KinectAzureKeypoints.HEAD, KinectAzureKeypoints.EAR_RIGHT),
    # ... (and so on for all 31 bones)
}


OPTITRACK_BONES: Set[Tuple[Enum, Enum]] = {
    # Spine
    (OptitrackJoints.Hips, OptitrackJoints.Spine),
    (OptitrackJoints.Spine, OptitrackJoints.Spine1),
    (OptitrackJoints.Spine1, OptitrackJoints.Neck),
    (OptitrackJoints.Neck, OptitrackJoints.Head),

    # Left Arm
    (OptitrackJoints.Spine1, OptitrackJoints.LeftShoulder),
    (OptitrackJoints.LeftShoulder, OptitrackJoints.LeftArm),
    (OptitrackJoints.LeftArm, OptitrackJoints.LeftForeArm),
    (OptitrackJoints.LeftForeArm, OptitrackJoints.LeftHand),

    # Left Hand Fingers
    (OptitrackJoints.LeftHand, OptitrackJoints.LeftHandThumb1),
    (OptitrackJoints.LeftHandThumb1, OptitrackJoints.LeftHandThumb2),
    (OptitrackJoints.LeftHandThumb2, OptitrackJoints.LeftHandThumb3),
    
    (OptitrackJoints.LeftHand, OptitrackJoints.LeftHandIndex1),
    (OptitrackJoints.LeftHandIndex1, OptitrackJoints.LeftHandIndex2),
    (OptitrackJoints.LeftHandIndex2, OptitrackJoints.LeftHandIndex3),
    
    (OptitrackJoints.LeftHand, OptitrackJoints.LeftHandMiddle1),
    (OptitrackJoints.LeftHandMiddle1, OptitrackJoints.LeftHandMiddle2),
    (OptitrackJoints.LeftHandMiddle2, OptitrackJoints.LeftHandMiddle3),
    
    (OptitrackJoints.LeftHand, OptitrackJoints.LeftHandRing1),
    (OptitrackJoints.LeftHandRing1, OptitrackJoints.LeftHandRing2),
    (OptitrackJoints.LeftHandRing2, OptitrackJoints.LeftHandRing3),
    
    (OptitrackJoints.LeftHand, OptitrackJoints.LeftHandPinky1),
    (OptitrackJoints.LeftHandPinky1, OptitrackJoints.LeftHandPinky2),
    (OptitrackJoints.LeftHandPinky2, OptitrackJoints.LeftHandPinky3),

    # Right Arm
    (OptitrackJoints.Spine1, OptitrackJoints.RightShoulder),
    (OptitrackJoints.RightShoulder, OptitrackJoints.RightArm),
    (OptitrackJoints.RightArm, OptitrackJoints.RightForeArm),
    (OptitrackJoints.RightForeArm, OptitrackJoints.RightHand),

    # Right Hand Fingers
    (OptitrackJoints.RightHand, OptitrackJoints.RightHandThumb1),
    (OptitrackJoints.RightHandThumb1, OptitrackJoints.RightHandThumb2),
    (OptitrackJoints.RightHandThumb2, OptitrackJoints.RightHandThumb3),
    
    (OptitrackJoints.RightHand, OptitrackJoints.RightHandIndex1),
    (OptitrackJoints.RightHandIndex1, OptitrackJoints.RightHandIndex2),
    (OptitrackJoints.RightHandIndex2, OptitrackJoints.RightHandIndex3),
    
    (OptitrackJoints.RightHand, OptitrackJoints.RightHandMiddle1),
    (OptitrackJoints.RightHandMiddle1, OptitrackJoints.RightHandMiddle2),
    (OptitrackJoints.RightHandMiddle2, OptitrackJoints.RightHandMiddle3),
    
    (OptitrackJoints.RightHand, OptitrackJoints.RightHandRing1),
    (OptitrackJoints.RightHandRing1, OptitrackJoints.RightHandRing2),
    (OptitrackJoints.RightHandRing2, OptitrackJoints.RightHandRing3),
    
    (OptitrackJoints.RightHand, OptitrackJoints.RightHandPinky1),
    (OptitrackJoints.RightHandPinky1, OptitrackJoints.RightHandPinky2),
    (OptitrackJoints.RightHandPinky2, OptitrackJoints.RightHandPinky3),

    # Left Leg
    (OptitrackJoints.Hips, OptitrackJoints.LeftUpLeg),
    (OptitrackJoints.LeftUpLeg, OptitrackJoints.LeftLeg),
    (OptitrackJoints.LeftLeg, OptitrackJoints.LeftFoot),
    (OptitrackJoints.LeftFoot, OptitrackJoints.LeftToeBase),

    # Right Leg
    (OptitrackJoints.Hips, OptitrackJoints.RightUpLeg),
    (OptitrackJoints.RightUpLeg, OptitrackJoints.RightLeg),
    (OptitrackJoints.RightLeg, OptitrackJoints.RightFoot),
    (OptitrackJoints.RightFoot, OptitrackJoints.RightToeBase),
}


# --- 4. Create the Public Instances ---
# Your main code will import these objects directly.

COCO = SkeletonDef(
    keypoints=CocoKeypoints,
    bones=COCO_BONES
)

KINECT_AZURE = SkeletonDef(
    keypoints=KinectAzureKeypoints,
    bones=KINECT_AZURE_BONES
)

OPTITRACK = SkeletonDef(
    keypoints=OptitrackJoints,
    bones=OPTITRACK_BONES
)


# --- 5. (Optional) A helper registry ---
# This makes it easy to get a skeleton by a string name.

SKELETON_REGISTRY: Dict[str, SkeletonDef] = {
    "coco": COCO,
    "kinect_azure": KINECT_AZURE,
    "optitrack": OPTITRACK,
}

def get_skeleton_def(name: str) -> SkeletonDef:
    """
    Fetches a SkeletonDef from the registry by its common name.
    """
    normalized_name = name.lower().strip()
    if normalized_name not in SKELETON_REGISTRY:
        raise ValueError(f"Unknown skeleton definition: '{name}'. "
                         f"Available: {list(SKELETON_REGISTRY.keys())}")
    return SKELETON_REGISTRY[normalized_name]
