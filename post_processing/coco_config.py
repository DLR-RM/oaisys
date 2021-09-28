from yacs.config import CfgNode as CN

_C = CN(new_allowed=True)

###############
# COCO SPECIFIC
###############
_C.COCO = CN()

# coco format related parameters; for detailed explanation also see https://patrickwasp.com/create-your-own-coco-style-dataset/
_C.COCO.DESCRIPTION = "example" # description of the dataset
_C.COCO.SUPERCATEGORY = "test"
_C.COCO.TOLERANCE = 2 # defines how precise contours are defined for individual objects. The higher the number, the lower the quality of annotation, but it also means a lower file size. 2 is usually a good value to start with.

# channel name of the  SENSOR in DATA_DEF which contains the instance labels (default: inst_label)
_C.COCO.ANNOTATION_KEY = "inst_label"

# besides instances coco also requires categories; a map with categories has to be defined (has to be a channel of the processed SENSOR in DATA_DEF if not important use same key as for annotation_key -> every instance gets assigned own category
_C.COCO.INST2CAT = "inst_label" # /"sem_label"

# yaml file which contains the category definitions; please check coco_category_definitions.yaml
_C.COCO.CAT_DEFINITIONS_FILE = "coco_category_definitions.yaml"

# modality definition: defines the modality for which the paths are listed in the coco file
_C.COCO.REF_MODALITY = "rgb"


def get_cfg_coco():
  """Get a yacs CfgNode object with default values for my_project."""
  # Return a clone so that the defaults will not be altered
  # This is for the "local variable" use pattern
  return _C.clone()


