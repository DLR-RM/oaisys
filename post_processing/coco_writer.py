import os
import sys
import datetime
import numpy as np

import warnings
import glob
import cv2

import json
import yaml

from io_utils import CocoUtils, PostprocessUtils

from annotation_writer import AnnotationWriter

class CocoProcessor(AnnotationWriter):
    def __init__(self, cfg):
        super(CocoProcessor, self).__init__(cfg)

        self.coco_data = None #TODO does this have to be a class member?

        self.out_path = self.out_path + ".json"

        self.tolerance = cfg.COCO.TOLERANCE 
        self.description = cfg.COCO.DESCRIPTION

        self.supercategory = cfg.COCO.SUPERCATEGORY

        self.reference_mod = cfg.COCO.REF_MODALITY

        self.annotation_key = cfg.COCO.ANNOTATION_KEY

        self.sensor_name = cfg.SENSORS
        if len(self.sensor_name) == 1:
            self.sensor_name = self.sensor_name[0]
        else:
            print("More than one sensor is specified for coco annotation")
            sys.exit()

        # is_crowd: defines if annotations describe single object(False) or a crowd/areas(True); single objects are encoded using with polygon, while crowds are encoded using column-major RLE (Run Length Encoding)
        self.category_definitions = self._parse_category_definitions(cfg.COCO.CAT_DEFINITIONS_FILE)

        self.inst2cat_key = cfg.COCO.INST2CAT if cfg.COCO.INST2CAT else self.annotation_key

        self.instance_id_cnt = 0

    def _parse_category_definitions(self, file_name):
        with open(file_name, "r") as stream:
            try:
                cat_def = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        return cat_def


    def _write_data(self):
        image_key = self.reference_mod
        annot_key = self.annotation_key

        inst2cat_maps = self.data[self.sensor_name][self.inst2cat_key]

        coco_data = self._generate_annotations(image_key, annot_key, self.category_definitions, inst2cat_key=self.inst2cat_key, dataset_description=self.description, supercategory=self.supercategory, tolerance=self.tolerance)

        print("Coco annotations are written to: " + self.out_path)
        with open(self.out_path, 'w') as fp:
            json.dump(coco_data, fp)
        return

    def _generate_annotations(self, ref_key, annotation_key, category_definitions, dataset_description, inst2cat_key=None, supercategory=None, tolerance=2):
        """ Generates coco annotations for rendered data
        Args:
            data: 
            image_paths: list of path strings pointing to the rendered images
            annotation_maps: list of annotations maps;
            category_definitions: dict(name:id) of all categories for current dataset; 
            inst2cat_key: dict mapping instance ids to category ids
            dataset_description: name of dataset
            supercategory: name of the supercategory; default description string

        Return:
            dict containing coco annotations
        """

        if not supercategory:
            supercategory = dataset_description

        # TODO read this info from file?!
        licenses = [
            {
                "id": 1,
                "name": "Attribution-NonCommercial-ShareAlike License",
                "url": "http://creativecommons.org/licenses/by-nc-sa/2.0/"
            }
        ]

        # TODO read this info from file?!
        info = {
            "description": dataset_description,
            "url": "https://github.com/waspinator/pycococreator",
            "version": "0.1.0",
            "year": 2020,
            "contributor": "Satoshi Nakamoto",
            "date_created": datetime.datetime.utcnow().isoformat(' ')
        }

        # define categories
        categories = []
        for _id, _attr in category_definitions.items():
            if _id != 0: # skip background
                cat_dict = {
                    'id': int(_id),
                    'name': _attr['name'],
                    'supercategory': supercategory
                }

                categories.append(cat_dict) # NOTE do we have to check for duplicates?

        imgs = []
        annotations = []

        for _id in range(0, self.data_size):

            consider_sample = True

            if _id % 200 == 0:
                print(f"current data_sample: {_id}")

            _data = {}
            for key, val in self.data[self.sensor_name].items():
                _map = self._load_image(val[_id]) 
                
                #_data_def = self.data_def[self.sensor_name][key]
                _data_def = self.channel_def[self.sensor_name][key]
                
                if _data_def.get('post_process',False): 
                    _map = PostprocessUtils.apply_postprocessing(_map, _data_def)

                _data[key] = _map
            
            # apply filters
            _data, n_rem, n_fil = self._filter_data(_data)

            self.n_remaining_labels += n_rem
            self.n_filtered_labels += n_fil

            _annot_map = _data[annotation_key]
            _inst2cat_map = _data[inst2cat_key]

            _ref_path = self.data[self.sensor_name][ref_key][_id] # reference path

            _instances = np.unique(_annot_map)
            tmp_annots = []
            for inst in _instances:
                if inst != 0 : # skip background
                    # binary object mask
                    inst_mask = np.where(_annot_map == inst, 1, 0).astype(np.float32)

                    if inst2cat_key: #NOTE later inst2cat might be None if only semantic labels are processed?!
                        cats = np.unique(inst_mask * _inst2cat_map)

                        if len(cats) != 2:
                            consider_sample = False
                            print(f"Something weired with the category labels is happening for {_ref_path}: cats are {len(cats)}")
                            break

                        cat_id = int(np.sort(cats)[-1])
                    else: #NOTE think about way to address this case
                        cat_id = 1
                        warnings.warn(f"No inst2cat map defined -> cat_id = 1")

                    if category_definitions.get(cat_id, True):
                        warnings.warn(f"The category with id {cat_id}, does not appear in the category-definitions -> The category is set to category_id: 1")
                        cat_id = 1

                    cat_info = {
                        'id': cat_id,
                        'is_crowd': category_definitions[cat_id]['is_crowd']
                    }

                    # coco info for instance
                    annotation = CocoUtils.create_annotation_info(self.instance_id_cnt, _id, cat_info, inst_mask, tolerance)
                    self.instance_id_cnt += 1

                    if annotation is not None:
                        tmp_annots.append(annotation)

        coco_annotations = {
            "info": info,
            "licenses": licenses,
            "categories": categories,
            "images": imgs,
            "annotations": annotations
        }

        return coco_annotations
