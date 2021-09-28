## Post-Processing 

Main task is to decode the rendered color values into discrete labels as well as filter instance labels depending on distance or object size.

For applying the post-processing please run: `python3 apply_post_processing.py FORMAT [coco/hdf5] BASE_PATH [path to rendered images]`; additionally all parameters defined in the cfg-files can also be overwritten via the comand-line

For the parameter configuration, please have a look at `default_config.py` and `coco_writer.py/hdf5_config.py` (depending on which FORMAT is chosen)
