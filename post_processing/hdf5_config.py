from yacs.config import CfgNode as CN

_C = CN(new_allowed=True)

###############
# HDF5 SPECIFIC
###############
_C.HDF5 = CN()

_C.HDF5.KEEP_EXISTING_FILES = True # if TRUE the current hdf5 files in the directory are not overwritten

def get_cfg_hdf5():
  """Get a yacs CfgNode object with default values for my_project."""
  # Return a clone so that the defaults will not be altered
  # This is for the "local variable" use pattern
  return _C.clone()


