import os
import numpy as np
import pandas as pd

from .base_parser import BaseParser


class TUMParser(BaseParser):

    def __init__(self, src_dir, gt_txt_path=None, depth_txt_path=None, rgb_txt_path=None):
        super(TUMParser, self).__init__(src_dir)

        self.name = 'TUMParser'

        self.gt_txt_path = gt_txt_path if gt_txt_path else os.path.join(self.src_dir, 'groundtruth.txt')
        if not os.path.exists(self.gt_txt_path):
            raise RuntimeError(f'Could not find groundtruth.txt: {self.gt_txt_path}')

        self.depth_txt_path = depth_txt_path if depth_txt_path else os.path.join(self.src_dir, 'depth.txt')
        if not os.path.exists(self.depth_txt_path):
            raise RuntimeError(f'Could not find depth.txt: {self.depth_txt_path}')

        self.rgb_txt_path = rgb_txt_path if rgb_txt_path else os.path.join(self.src_dir, 'rgb.txt')
        if not os.path.exists(self.rgb_txt_path):
            raise RuntimeError(f'Could not find rgb.txt: {self.rgb_txt_path}')

        self.skiprows = 3

    @staticmethod
    def associate_timestamps(timestamps, other_timestamps, max_difference=0.02):
        timestamps = list(timestamps)
        other_timestamps = list(other_timestamps)
        potential_matches = [(timestamp, other_timestamp)
                             for timestamp in timestamps
                             for other_timestamp in other_timestamps
                             if abs(timestamp - other_timestamp) < max_difference]
        potential_matches.sort(key=lambda x: abs(x[0] - x[1]))

        matches = []
        for timestamp, other_timestamp in potential_matches:
            if timestamp in timestamps and other_timestamp in other_timestamps:
                timestamps.remove(timestamp)
                other_timestamps.remove(other_timestamp)
                matches.append((timestamp, other_timestamp))

        matches.sort()
        return list(zip(*matches))

    @staticmethod
    def associate_dataframes(dataframes, timestamp_cols):
        df = dataframes[0]
        timestamp_col = timestamp_cols[0]
        df = df.drop_duplicates(timestamp_col)
        for other_df, other_timestamp_col in zip(dataframes[1:], timestamp_cols[1:]):

            other_df = other_df.drop_duplicates(other_timestamp_col)

            timestamps, other_timestamps = \
                TUMParser.associate_timestamps(df[timestamp_col].values, other_df[other_timestamp_col].values)
            df = df[df[timestamp_col].isin(timestamps)]
            df.index = np.arange(len(df))
            other_df = other_df[other_df[other_timestamp_col].isin(other_timestamps)]
            other_df.index = timestamps

            assert len(df) == len(other_df)
            df = df.join(other_df, on=timestamp_col)
        return df

    def _load_txt(self, txt_path, columns):
        df = pd.read_csv(txt_path, skiprows=self.skiprows, sep=' ', index_col=False, names=columns)
        df.columns = columns
        timestamp_col = columns[0]
        df[timestamp_col] = df[timestamp_col].apply(float)
        return df

    def _load_gt_txt(self):
        return self._load_txt(self.gt_txt_path,
                              columns=['timestamp_gt', 't_x', 't_y', 't_z', 'q_x', 'q_y', 'q_z', 'q_w'])

    def _load_rgb_txt(self):
        return self._load_txt(self.rgb_txt_path, columns=['timestamp_rgb', 'path_to_rgb'])

    def _load_depth_txt(self):
        return self._load_txt(self.depth_txt_path, columns=['timestamp_depth', 'path_to_depth'])

    def _load_data(self):
        self.dataframes = [self._load_depth_txt(), self._load_rgb_txt(), self._load_gt_txt()]
        self.timestamp_cols = ['timestamp_depth', 'timestamp_rgb', 'timestamp_gt']

    def _create_dataframe(self):
        self.df = self.associate_dataframes(self.dataframes, self.timestamp_cols)
