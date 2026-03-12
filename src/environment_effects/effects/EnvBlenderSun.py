# blender imports
import bpy

# internal OAISYS
from src.environment_effects.TSSEnvironmentEffects import TSSEnvironmentEffects
from src.tools.utils import get_random_value

class EnvBlenderSun(TSSEnvironmentEffects):
    """docstring for EnvBlenderSun"""
    def __init__(self):
        super(EnvBlenderSun, self).__init__()

        self.sun = None

    def reset(self):
        self.sun = None


    @staticmethod
    def set_sun_params(sun, params, keyframe=-1):
        """ fn to set sun parameters
            Args:
                sun:                sun blender object [blObject]
                params:             sun parameters [dict]
                keyframe:           current frame number; if value > -1, this should enable also the setting of a
                                    keyframe [int]
            Returns:
                None
        """

        # set intensity value
        sun.data.energy = get_random_value(params["energy"])

        # set rotation value
        rot_x = get_random_value(params["rotation_rad"][0])
        rot_y = get_random_value(params["rotation_rad"][1])
        rot_z = get_random_value(params["rotation_rad"][2])
        sun.rotation_euler = rot_x, rot_y, rot_z

        # set keyframe if requested
        if keyframe > -1:

            # insert keyframe for all params
            sun.data.keyframe_insert('energy', frame=keyframe)
            sun.keyframe_insert('rotation_euler', frame=keyframe)

            # set interpolation to constant
            fc = sun.animation_data.action.fcurves
            for sfc in fc:
                for kf in sfc.keyframe_points:
                    kf.interpolation = 'CONSTANT'


    def create(self, last_element=None):
        """ create function
            Args:
                last_element:           current last element in node tree [blObject]
            Returns:
                return new last element [blObject]
        """

        # create basic sun model
        bpy.ops.object.light_add(type='SUN', radius=1, align='WORLD', location=(0, 0, 0), rotation=(0, 0, 0),
                                 scale=(1, 1, 1))

        # get handle to cube
        self.sun = bpy.context.selected_objects[0]

        # build up full mesh name
        self.sun.name = 'env_sun_' + self._cfg["name"]

        # set params
        self.set_sun_params(self.sun, self._cfg, keyframe=0)

        return last_element

    def step(self, keyframe):
        """ step function
        Args:
            keyframe:       current frame number; if value > -1, this should enable also the setting of a keyframe [int]
        Returns:
            None
        """
        self.set_sun_params(sun=self.sun, params=self._cfg)