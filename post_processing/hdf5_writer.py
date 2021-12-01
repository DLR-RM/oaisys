import os

import h5py
import numpy as np
import glob

from annotation_writer import AnnotationWriter
from io_utils import PostprocessUtils

class HDF5Processor(AnnotationWriter):
    def __init__(self,cfg):
        super(HDF5Processor, self).__init__(cfg)

        self.keep_existing_files = cfg.HDF5.KEEP_EXISTING_FILES

        self.frame_cnt = 0 


    def _update_frame_count(self):
        """ Checks if in existing output dir hdf5 exists and sets the frame count to highest id
        """
        _files = glob.glob(os.path.join(self.base_path,"*hdf5"))
        if len(_files) == 0:
            return
        
        _bns = np.array([int(os.path.splitext(os.path.basename(item))[0]) for item in _files])

        self.frame_cnt = np.amax(_bns) + 1
        return

    def _write_data_multiple(self, compression= "gzip"):
        print("Hdf5 annotations are written to: " + self.base_path)

        for _i in range(0,self.data_size):
            _out_file = os.path.join(self.base_path, str(self.frame_cnt)) + ".hdf5"

            data_to_save = {}
            for sen, channels in self.data.items():
                _sen_data = {}
                for key, val in channels.items():
                    _map = self._load_image(val[_i]) 

                    _data_def = self.channel_def[sen][key]

                    if _data_def.get('post_process',False): 
                        _map = PostprocessUtils.apply_postprocessing(_map, _data_def)

                    _sen_data[key] = _map
            
                # TODO make this more general that not every sensor has to be filtered
                # TODO make this more general that also semantic labels can be filtered
                if "inst_label" in channels.keys():
                    _sen_data, n_rem, n_fil = self._filter_data(_sen_data)

                    self.n_remaining_labels += n_rem
                    self.n_filtered_labels += n_fil

                data_to_save[sen] = _sen_data

            # due to the filtering there have to be two separate for-loops going over the same data
            with h5py.File(_out_file, 'w') as f:
                for sen, channels in data_to_save.items():
                    for key, val in channels.items():
                        dset = f.create_dataset(sen + '_' + key, data=val, compression=compression)

            self.frame_cnt += 1
        return

    def _write_data(self):
        if self.keep_existing_files:
            self._update_frame_count()

        self._write_data_multiple()
        return
