import os
import shutil
import copy
import numpy as np

from odometry.preprocessing.estimators.base_estimator import BaseEstimator
from odometry.linalg import (form_se3,
                             split_se3,
                             get_relative_se3_matrix,
                             convert_euler_angles_to_rotation_matrix,
                             convert_rotation_matrix_to_euler_angles)


class Global2RelativeEstimator(BaseEstimator):

    def __init__(self, *args, **kwargs):
        super(Global2RelativeEstimator, self).__init__(*args, **kwargs)
        self.name = 'Global2Relative'

    def run(self, row, dataset_root=None):

        if not set(self.input_col) <= set(dict(row).keys()):
            return row

        dof = row[self.input_col[:6]].values
        next_dof = row[self.input_col[6:]].values

        euler_angles, translation = dof[:3], dof[3:]
        next_euler_angles, next_translation = next_dof[:3], next_dof[3:]

        rotation_matrix = convert_euler_angles_to_rotation_matrix(euler_angles)
        next_rotation_matrix = convert_euler_angles_to_rotation_matrix(next_euler_angles)

        global_se3_matrix = form_se3(rotation_matrix, translation)
        next_global_se3_matrix = form_se3(next_rotation_matrix, next_translation)
        relative_se3_matrix = get_relative_se3_matrix(global_se3_matrix, next_global_se3_matrix)
        relative_rotation_matrix, relative_translation = split_se3(relative_se3_matrix)
        relative_euler_angles = convert_rotation_matrix_to_euler_angles(relative_rotation_matrix)

        relative_dof = np.concatenate([relative_euler_angles, relative_translation])
        row = self._drop_input(row)
        return self._add_output(row, relative_dof)
