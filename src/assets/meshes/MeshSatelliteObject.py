# blender imports
import bpy

# utility imports
import os
from mathutils import Matrix, Vector, Quaternion
import copy as cp

# OAISYS imports
from src.assets.meshes.MeshSingle import MeshSingle
from src.tools.orbit_sampler import sample_orbit_parameters


class MeshSatelliteObject(MeshSingle):
    """docstring for MeshSatelliteObject"""

    def __init__(self):
        super(MeshSatelliteObject, self).__init__()

        self.orbit = None
        self.parent_mesh = None

    def create_circular_orbit(self, orbit_cfg):
        # create
        bpy.ops.curve.primitive_bezier_circle_add(enter_editmode=False, align='WORLD', location=(0, 0, 0),
                                                  scale=(1, 1, 1))

        # get handle to cube
        orbit = bpy.context.selected_objects[0]

        # build up full mesh name
        orbit.name = 'mesh_MeshSatellite_Orbit_' + self._cfg["name"]

        # rotate orbit
        MeshSingle.translate_oaisys_object(mesh=orbit, cfg=orbit_cfg)

        # update scene
        bpy.context.view_layer.update()

        return orbit

    def create_orbit(self, orbit_cfg):
        if orbit_cfg["type"] == "circular":
            return self.create_circular_orbit(orbit_cfg=orbit_cfg)
        elif orbit_cfg["type"] == "orbit_database":
            orbit = sample_orbit_parameters(orbit_cfg["orbit_type"])
            orbit_cfg["scale"] = orbit["scale_xyz"]
            orbit_cfg["rotation"] = orbit["rotation_rpy"]
            print(orbit_cfg)
            return self.create_circular_orbit(orbit_cfg=orbit_cfg)
        else:
            return None

    def get_pose_for_step_in_future(self, step=1):
        # save current values
        current_offset = cp.deepcopy(self.orbit_constraint.offset)

        # project into future
        self.orbit_constraint.offset += step * float(self._cfg['orbit_params']['v_step'])
        bpy.context.view_layer.update()

        # retrieve future values
        loc_m, rot_m, _ = self.mesh.matrix_world.decompose()

        # reset value
        self.orbit_constraint.offset = current_offset
        bpy.context.view_layer.update()

        # return
        return loc_m, rot_m

    def step(self, keyframe):
        """ stepping function
        Args:
            None
        Returns:
            None
        """
        if not self.module_active:
            return

        self._stepping_counter += 1

        if keyframe > -1:
            loc_m, rot_m, sca_m = self.parent_mesh.matrix_world.decompose()
            MeshSingle.translate_object(mesh=self.orbit, loc=loc_m)
            self.orbit.keyframe_insert('location', frame=keyframe)

            self.orbit_constraint.offset += float(self._cfg['orbit_params']['v_step'])
            self.orbit_constraint.keyframe_insert('offset', frame=keyframe)

            loc_m, rot_m, sca_m = self.mesh.matrix_world.decompose()

            _fcurves = self.mesh.animation_data.action.fcurves
            for fcurve in _fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'CONSTANT'

            _fcurves = self.orbit.animation_data.action.fcurves
            for fcurve in _fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'CONSTANT'

            if (self._stepping_counter % self._trigger_interval) == 0:
                self.step_oasys_material_drivers(keyframe=keyframe)

        bpy.context.view_layer.update()
        mx = self.mesh.matrix_world
        loc_m, _, _ = mx.decompose()

    @staticmethod
    def attach_mesh_to_curve(mesh, orbit_curve, orbit_start=0.0):
        curve_constraint = mesh.constraints.new(type='FOLLOW_PATH')
        curve_constraint.target = orbit_curve
        curve_constraint.offset = orbit_start
        curve_constraint.use_curve_follow = True

        return curve_constraint

    def update_after_initial_mesh_creation(self, mesh_dict):
        for m, m_v in mesh_dict.items():
            if self._cfg['orbit_params']['parent'] == m:
                print(m_v["main"].location)
                MeshSingle.translate_object(mesh=self.orbit, loc=m_v["main"].location)
                self.parent_mesh = m_v["main"]
                break

    def add_material_node_group(self, mesh, material_slot, node_group):
        print("Hallo Welt!")
        for m_ID, m_s in enumerate(mesh.material_slots):
            print(m_s.name)
            print(f"OAISYS_{material_slot}_mat")
            if m_s.name == f"OAISYS_{material_slot}_mat":
                print(f"OVERRIDE!")
                material_slot = node_group

    def add_material_override(self, mesh, mesh_settings_cfg, materials):
        print(f"materials: {materials}")
        if "material_override" in mesh_settings_cfg:
            for k, v in mesh_settings_cfg["material_override"].items():
                for m in v['materials']:
                    self.add_material_node_group(mesh, k, materials[m].setup_material_instance())

    def create_satellite(self, instance_id_offset, materials):
        self._mesh_file_path = self._cfg['meshFilePath']
        mesh_settings_cfg = self._cfg
        mesh_settings_cfg["location"] = [0, 0, 0]

        # create mesh and apply transformations
        _mesh_object_file_name = os.path.basename(os.path.normpath(os.path.splitext(self._mesh_file_path)[0]))
        if 'meshInstanceName' in self._cfg:
            if not self._cfg['meshInstanceName'] == "":
                _mesh_object_file_name = self._cfg['meshInstanceName']

        # build up full mesh name
        _local_mesh_name = 'mesh_MeshSingle_' + self._cfg["name"]
        _mesh = None

        if not _mesh:
            # load file
            _mesh = self.create_mesh(0, self._mesh_file_path, _mesh_object_file_name)
            self.mesh = _mesh
            print(f"self.mesh: {self.mesh}")
            _mesh.name = _local_mesh_name
            self.current_mesh_q = MeshSingle.translate_oaisys_object(mesh=self.mesh, cfg=self._cfg)

        # apply deformation
        if "assetDisplacementParams" in self._cfg:
            _disp_cfg = self._cfg['assetDisplacementParams']
            if _disp_cfg['assetDisplacementActive']:
                self.add_displacement_to_mesh(mesh=self.mesh, disp_cfg=_disp_cfg)

        # create spline object
        self.orbit = self.create_orbit(orbit_cfg=self._cfg['orbit_params'])

        # apply object to spline following object
        self.orbit_constraint = MeshSatelliteObject.attach_mesh_to_curve(mesh=self.mesh, orbit_curve=self.orbit,
                                                                         orbit_start=self._cfg['orbit_params'][
                                                                             'orbit_start'])

        if "oaisys_drivers" in self._cfg:
            if "material_drivers" in self._cfg["oaisys_drivers"]:
                self.add_oaisys_material_drivers(mesh=self.mesh,
                                                 drivers=self._cfg["oaisys_drivers"]["material_drivers"])

        # apply render channels
        self.create_render_pass_nodes(mesh=self.mesh,
                                      mesh_settings_cfg=mesh_settings_cfg,
                                      instance_id_offset=instance_id_offset)

    def create(self, instance_id_offset=0, materials=None):
        """ create function
        Args:
            instance_id_offset:                                     instance offset ID [int]

        """
        self.module_active = True

        self.create_satellite(instance_id_offset=instance_id_offset, materials=materials)

        # TODO: it is not always 1,1!!!!
        return 1, 1
