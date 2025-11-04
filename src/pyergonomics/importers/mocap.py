import numpy as np
from bvhtoolbox import Bvh, BvhNode, BvhTree, get_affines
import transforms3d as t3d
import toml
import os
from pathlib import Path

from ..configuration import Configuration

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
        data_list.append( r.apply(pos)  )

        print(joint.name)

        bvh_dict[joint.name] = r.apply(pos) 
                
        if end_sites:
            end = list(joint.filter('End'))
            if end:
                get_world_positions(end[0])  # There can be only one End Site per joint.
        for child in joint.filter('JOINT'):
            get_world_positions(child)
    
    get_world_positions(root)

    data = np.concatenate(data_list, axis=1)

    return bvh_dict


def init_from_bvh(bvh_file):
    bvh_path = Path(bvh_file)
    if not bvh_path.is_file():
        print(f"Error: BVH file not found at {bvh_file}")
        return

    output_dir = Path(bvh_path.stem)

    if output_dir.exists():
        print(
            f"Error: Directory '{output_dir}' already exists. Please remove it or choose a different BVH file."
        )
        return

    with open(bvh_path) as f:
        bvh = BvhTree(f.read())

    world_coordinates = world_joint_positions(bvh)

    fps = 1.0 / bvh.frame_time
    frame_count = bvh.nframes




    config_path = output_dir / "project.toml"
    config = Configuration(config_path)
    config.number_of_frames = count
    config.frames_per_second = fps
    config.source_bvh = str(bvh_path)
    config.save()

    print(f"Configuration file created at {config_path}")
