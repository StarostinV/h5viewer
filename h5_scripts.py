import h5py
from directories import Directories
import os


def add_axes_refs(obj_with_ref, obj_x_axis, obj_y_axis):
    obj_with_ref.attrs['x_axis'] = obj_x_axis.ref
    obj_with_ref.attrs['y_axis'] = obj_y_axis.ref


def add_refs_to_all_images(filename):
    with h5py.File(filename, 'a') as f:
        group = f['q_interpolated/PEN04']
        for key in list(group.keys()):
            current_group = group[key]
            x_axis = current_group['q_xy']
            y_axis = current_group['q_z']
            for k in list(current_group.keys()):
                if k.startswith('zaptime'):
                    current_group[k].attrs['x_axis'] = x_axis.ref
                    current_group[k].attrs['y_axis'] = y_axis.ref


if __name__ == '__main__':
    filename = os.path.join(Directories.get_dir_to_save_images(), 'whole_data.h5')
    add_refs_to_all_images(filename)
