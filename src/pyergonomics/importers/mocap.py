import numpy as np
from bvhtoolbox import Bvh, BvhNode, BvhTree, get_affines
import transforms3d as t3d
import toml
import os
from pathlib import Path
import polars as pl

def world_joint_positions(bvh_tree, scale=1.0, end_sites=False):   
    time_col = np.arange(0, (bvh_tree.nframes - 0.5) * bvh_tree.frame_time, bvh_tree.frame_time)[:, None]
    data_list = [time_col]
    header = ['time']
    root = next(bvh_tree.root.filter('ROOT'))

    # print(time_col)

    bvh_dict = {}
    
    def get_world_positions(joint):
        if joint.value[0] == 'End':
            joint.world_transforms = np.tile(t3d.affines.compose(np.zeros(3), np.eye(3), np.ones(3)),
                                             (bvh_tree.nframes, 1, 1))
        else:
            channels = bvh_tree.joint_channels(joint.name)
            axes_order = ''.join([ch[:1] for ch in channels if ch[1:] == 'rotation']).lower()  # FixMe: This isn't going to work when not all rotation channels are present
            axes_order = 's' + axes_order[::-1]
            joint.world_transforms = get_affines(bvh_tree, joint.name, axes=axes_order)
            
        if joint != root:
            # For joints substitute position for offsets.
            offset = [float(o) for o in joint['OFFSET']]
            joint.world_transforms[:, :3, 3] = offset
            joint.world_transforms = np.matmul(joint.parent.world_transforms, joint.world_transforms)
        if scale != 1.0:
            joint.world_transforms[:, :3, 3] *= scale
            
        header.extend(['{}.{}'.format(joint.name, channel) for channel in 'xyz'])
        pos = joint.world_transforms[:, :3, 3]
        # data_list.append(pos)
        data_list.append(pos)

        print(joint.name)

        bvh_dict[joint.name] = pos
                
        if end_sites:
            end = list(joint.filter('End'))
            if end:
                get_world_positions(end[0])  # There can be only one End Site per joint.
        for child in joint.filter('JOINT'):
            get_world_positions(child)
    
    get_world_positions(root)

    data = np.concatenate(data_list, axis=1)

    return bvh_dict


def init_from_bvh(destination_folder, bvh_file=None):
    from ..project_settings import ProjectSettings

    output_dir = Path(destination_folder)

    if not output_dir.exists():
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    config_path = output_dir / "project.toml"
    config = ProjectSettings(config_path)

    if bvh_file:
        bvh_path = Path(bvh_file).resolve()
        if not bvh_path.is_file():
            print(f"Error: BVH file not found at {bvh_file}")
            return

        with open(bvh_path) as f:
            bvh = BvhTree(f.read())

        world_coordinates = world_joint_positions(bvh)

        fps = 1.0 / bvh.frame_time
        frame_count = bvh.nframes

        # Prepare data for DataFrame
        joint_names = list(world_coordinates.keys())
        keypoints_3d_per_frame = []
        for i in range(frame_count):
            frame_keypoints = []
            for joint_name in joint_names:
                frame_keypoints.append(world_coordinates[joint_name][i].tolist())
            keypoints_3d_per_frame.append(frame_keypoints)

        df = pl.DataFrame(
            {
                "person": [1] * frame_count,
                "frame": range(frame_count),
                "keypoints_3d": keypoints_3d_per_frame,
            }
        )

        tracking_filename = "tracking.parquet"
        tracking_filepath = output_dir / tracking_filename
        df.write_parquet(tracking_filepath)
        print(f"Tracking data saved to {tracking_filepath}")

        config.number_of_frames = frame_count
        config.frames_per_second = fps
        config.data["source_mocap"] = {"bvh_file": str(bvh_path)}
        config.set_tracking_file(tracking_filename)
    else:
        config.number_of_frames = 0
        config.frames_per_second = 120.0
        config.data["source_mocap"] = {}

    config.save()

    print(f"Configuration file created at {config_path}")
