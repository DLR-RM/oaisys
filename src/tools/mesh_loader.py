# blender imports
import bpy

# utility imports
import pathlib
import os


def load_mesh(path, obj_name=None):
    ext = pathlib.Path(path).suffix

    if ext.lower() == '.obj':
        load_obj(path)

    elif ext.lower() == '.blend':
        load_blend(path, obj_name)

    else:
        NotImplementedError("No loader is yet implemented for the data type you try to load!")

    return [o.name for o in bpy.context.selected_objects]


def load_obj(path):
    bpy.ops.import_scene.obj(filepath=path)


def load_blend(path, obj_name):
    bpy.ops.wm.append(directory=os.path.join(path, "Object"),
                      link=False,
                      filename=obj_name)
