import os
import sys

import warnings

import glob
import cv2
import numpy as np

from io_utils import PostprocessUtils
from io_utils import LabelFilter

class AnnotationWriter():
    def __init__(self, cfg):
        self.base_path = cfg.BASE_PATH 
        self.data_def = cfg.DATA_DEF[0]

        self.batch_glob = cfg.BATCH_GLOB

        self.sensors = cfg.SENSORS

        self.channel_def = self._generate_channel_def()

        self.out_path = os.path.join(self.base_path, cfg.OUT_FILE)

        self.background = cfg.BACKGROUND

        self.filters = cfg.FILTER[0]

        self.data = {}

        self.data_size = None

        self.n_remaining_labels = 0
        self.n_filtered_labels = 0

    def run(self):
        self._gather_sample_info()

        print("Write Data ...")
        self._write_data()

        print(f"In total {self.data_size} samples processed. {self.n_remaining_labels} Labels remain while {self.n_filtered_labels} labels are filtered")

    def _generate_channel_def(self):
        channel_def = {}
        
        for s in self.sensors:
            _def = {**self.data_def["common"], **self.data_def[s]}
            channel_def[s] = _def

        return channel_def

    def _gather_sample_info(self):
        """ gathers all filenames of rendered images together """

        print("searching for relevant files...")

        b_dir = os.path.join(self.base_path, self.batch_glob)
        batches = glob.glob(b_dir)

        for sensor, s_def in self.channel_def.items():                
            sen_dict = {}
            for channel, d in s_def.items():
                ch_files = []
                for b_path in batches:
                    #define path
                    g_str = d['glob']
                    in_dir = os.path.join(b_path, sensor, g_str) # assumption of path structure: base_path/[sensor]/[channel_glob]

                    _files = glob.glob(in_dir)
                    assert len(_files) != 0, "no files found here: " + in_dir

                    ch_files.extend(_files)

                if not self.data_size:
                    self.data_size = len(ch_files)
                else:
                    assert len(ch_files) == self.data_size, "different number of samples for: " + g_str

                ch_files.sort() # ensure same ordering for all modalities
                sen_dict[channel] = ch_files

            self.data[sensor] = sen_dict 
            print(f"For sensor {sensor}, {self.data_size} data samples with following modalities found: {s_def.keys()}")

        return 

    def _filter_data(self, data, label_key="inst_label"):
        "applies label filter on data"

        labels_orig = data[label_key]

        # for statistical reasons
        n_fil = 0
        n_orig = np.unique(labels_orig).shape[0]

        for _l in np.unique(labels_orig):
            if _l != self.background:
                binary_mask = np.where(labels_orig == _l, 1, 0).astype(np.bool)

                for _method_key, filter_cfg in self.filters.items():
                    filter_method = eval("LabelFilter."+_method_key)
                    is_filtered = filter_method(binary_mask, filter_cfg, data=data)
                    if is_filtered:
                        # if one method filters current binary mask, no need for further filters
                        labels_orig[binary_mask] = self.background 
                        n_fil += 1
                        break

        n_rem = np.unique(data[label_key]).shape[0]
        assert n_orig == n_rem + n_fil
        
        return data, n_rem, n_fil

    def _write_data(self):
        """ writes dictionary of data channels into file
        """
        raise NotImplementedError("Please Implement this method")
        return

    def _load_image(self, image_path):
        """Load one image
    
        Args:
            image_path: path to image
            width: desired width of returned image
            height: desired heigt of returned image
            chanels:
    
        Returns:
            image (np.array)
    
        """
        image = cv2.imread(image_path, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
        return image

