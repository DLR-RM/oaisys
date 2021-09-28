from yacs.config import CfgNode as CN

_C = CN(new_allowed=True)

###############
# General
###############
_C.FORMAT = "" # this defines the data format. it is recommended to leave this blank and define it via the cmd-line; ["coco", "hdf5"]
_C.BASE_PATH="" # absolute path to the rendered image batches
_C.BATCH_GLOB="batch_*" # common pattern of the batch folders; normally this is parameter does not have to be changed

_C.OUT_FILE = "annotations" # output file name without ending, since the file extension depends on the FORMAT

_C.SENSORS = ["sensor_1", "sensor_2"] # name of sensors which should be considered; if FORMAT=coco only one SENSOR is possible (still defined as list)

# channel definitions
# the "common" dict defines channels which are considered for every element, 
# while the e.g. "rgbLeft" (note the key-name has to match the SENSOR name) have special channel definitions
#
# possible entries for data definitions
# e.g. "rgbLeft" :{
#    [channel_name]: {
#    "glob": [common pattern of related channel], # required for finding channel files 
#    "post_process": [post_processing name], # this is mainly for labels but can also be used to trim the depth maps; see also PostprocessUtils in io_utils.py, there also new post_processing methods can be defined;
#        currently for label-channels: "post_process":"denoise_label" and for depth-channels: "post_process":"trim_channels"
#    "num_classes": post_processing(denoise label) required parameter; please see cfg parameters maxInstanceLabelPerChannel(for instance labels) and num_labels_per_channel (for semantic labels)
#   }
#}
_C.DATA_DEF = [{
    'common': { # channels which are considered for every element in SENSOR list
        "rgb":{"glob":"*rgb_00.png"}, 
    },
    'sensor_1':{ # specific channel definitions for SENSOR member rgbLeft
        #"inst_label":{"post_process":"denoise_label", "num_classes": 51, "glob":"*instance_label*"},
        #"sem_label":{"post_process":"denoise_label", "num_classes": 15, "glob":"*semantic_label*"},
        #"pinhole_depth":{"glob":"*pinhole_depth_00.exr", "post_process":"trim_channels"},
        #"euclidean_depth":{"glob":"*depth_euclidean.exr", "post_process":"trim_channels"},
    },
    'sensor_2':{}
}
]

_C.BACKGROUND = 0 # label ID which is considered as background

# FILTER definitions for the instance labels: key[method_name]:[method parameters]
# see also FilterLabels in io_utils.py
_C.FILTER = [{
    "filter_by_area":{"min_area":40},
    "filter_by_depth":{"depth_key": "pinhole_depth", "max_depth": 35, "thres_type":"avg"},
    }]

def get_cfg_defaults():
  """Get a yacs CfgNode object with default values for my_project."""
  # Return a clone so that the defaults will not be altered
  # This is for the "local variable" use pattern
  return _C.clone()


