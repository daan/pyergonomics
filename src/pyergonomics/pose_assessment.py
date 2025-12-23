import numpy as np

from skspatial.objects import Plane, Vector 

from pose_skeletons import SkeletonDefinition

def make_pose_assessment(skeleton: SkeletonDefinition, joints: np.ndarray):    
    a = {}
    # upper body planes
    #
    # transverse plane
    vhc = (joints[skeleton.r_hip] + joints[skeleton.l_hip]) / 2.0
    vu = joints[skeleton.neck] - vhc 
    a["transverse_plane"] = Plane(vhc, vu)

    # coronal plane
    vf = np.cross(vu, (joints[skeleton.r_hip] - joints[skeleton.l_hip]))
    a["coronal_plane"] = Plane(vhc, vf/np.linalg.norm(vf))

    # sagittal plane
    vl = np.cross(vu, vf)
    a["sagittal_plane"] = Plane(vhc, vl)

    #
    # lower body part
    #
    # ground plane
    vgo = np.array([vhc[0],vhc[1],0]) # origin, assuming z=0 is ground 
    vgu = np.array([0,0,1]) # up vector Z
    a["ground_plane"] = Plane(vgo, vgu)

    # front plane
    vgf = np.cross(vgu, (joints[skeleton.r_hip] - joints[skeleton.l_hip]))
    a["ground_coronal_plane"] = Plane( vhc, vgf )

    # left plane
    vgl = np.cross(vgu, vgf)
    a["ground_sagittal_plane"] = Plane(vhc, vgl)

    # trunk bend
    gsp_vu = a["ground_sagittal_plane"].project_vector(vu)
    a["trunk_bending"] = gsp_vu.angle_signed_3d(vgu, direction_positive=-vgl)/(np.pi*2) * 360

    # side bend
    gcp_vu = a["ground_coronal_plane"].project_vector(vu)
    a["trunk_side_bending"] = gcp_vu.angle_between(vgu)/(np.pi*2) * 360 

    gp13_10 = a["ground_plane"].project_vector(  (joints[skeleton.r_hip] - joints[skeleton.l_hip]))
    gp6_3 = a["ground_plane"].project_vector( joints[skeleton.l_shoulder] - joints[skeleton.r_shoulder] )
    a["trunk_twist"] = gp13_10.angle_between(gp6_3)/(np.pi*2) * 360 - 180

    return a


