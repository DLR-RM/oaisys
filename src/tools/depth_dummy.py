bl_info = {
    "name": "distance_to_depth",
    "author": "Martin Wudenka",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "Compositor",
    "description": "Provides a compositor node to convert distance images to depth images",
    "category": "Compositor",
}

import bpy
from nodeitems_utils import NodeItem, register_node_categories, unregister_node_categories
from nodeitems_builtins import CompositorNodeCategory

# Build intrinsic camera parameters from Blender camera data
#
# See notes on this in
# blender.stackexchange.com/questions/15102/what-is-blenders-camera-projection-matrix-model
def get_camera_intrinsics():
    scene = bpy.context.scene
    camera = scene.camera.data

    f_in_mm = camera.lens

    resolution_x_in_px = scene.render.resolution_x
    resolution_y_in_px = scene.render.resolution_y
    scale = scene.render.resolution_percentage / 100
    sensor_width_in_mm = camera.sensor_width
    sensor_height_in_mm = camera.sensor_height
    pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
    if (camera.sensor_fit == 'VERTICAL'):
        # the sensor height is fixed (sensor fit is horizontal),
        # the sensor width is effectively changed with the pixel aspect ratio
        s_u = resolution_x_in_px * scale / sensor_width_in_mm / pixel_aspect_ratio
        s_v = resolution_y_in_px * scale / sensor_height_in_mm
    else:  # 'HORIZONTAL' and 'AUTO'
        # the sensor width is fixed (sensor fit is horizontal),
        # the sensor height is effectively changed with the pixel aspect ratio
        pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
        s_u = resolution_x_in_px * scale / sensor_width_in_mm
        s_v = resolution_y_in_px * scale * pixel_aspect_ratio / sensor_height_in_mm

    # Parameters of intrinsic calibration matrix
    f_u = f_in_mm * s_u
    f_v = f_in_mm * s_v
    c_u = resolution_x_in_px * scale / 2
    c_v = resolution_y_in_px * scale / 2

    return resolution_x_in_px * scale, resolution_y_in_px * scale, f_u, f_v, c_u, c_v

class DistanceToDepth (bpy.types.CompositorNodeCustomGroup):
    """
    Corrects blender depth maps (that are actually distance maps)
    Calculates depth = dist / sqrt(1 + (x^2/fx^2) + (y^2/fy^2)))
    """

    bl_name = 'DistanceToDepth'
    bl_label = 'Distance to Depth'

    def update_defaults(self):
        for node in self.node_tree.nodes:
            if node.label == 'x':
                node.inputs[1].default_value = self.width
            elif node.label == 'y':
                node.inputs[1].default_value = self.height
            elif node.label == 'x_to_cam':
                node.inputs[1].default_value = self.c_x
            elif node.label == 'y_to_cam':
                node.inputs[1].default_value = self.c_y
            elif node.label == 'x_over_f':
                node.inputs[1].default_value = self.f_x * self.f_x
            elif node.label == 'y_over_f':
                node.inputs[1].default_value = self.f_y * self.f_y

    def update_intrinsics(self, context):
        self.update_defaults()

    def set_intrinsics_from_blender(self, context):
        self.width, self.height, self.f_x, self.f_y, self.c_x, self.c_y = get_camera_intrinsics()
        self.update_defaults()

    def read_update_from_blender(self):
        return False

    def write_update_from_blender(self, value):
        pass

    width: bpy.props.FloatProperty(
        name="width", description="image width", update=update_intrinsics)
    height: bpy.props.FloatProperty(
        name="height", description="image height", update=update_intrinsics)
    f_x: bpy.props.FloatProperty(
        name="f_x", description="x focal length", update=update_intrinsics)
    f_y: bpy.props.FloatProperty(
        name="f_y", description="y focal length", update=update_intrinsics)
    c_x: bpy.props.FloatProperty(
        name="c_x", description="princial point x", update=update_intrinsics)
    c_y: bpy.props.FloatProperty(
        name="c_y", description="princial point y", update=update_intrinsics)

    update_from_blender: bpy.props.BoolProperty(name="update_from_blender",
                                                description="Read the parameters from Blender", update=set_intrinsics_from_blender,
                                                set=write_update_from_blender, get=read_update_from_blender)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, 'width', text='width')
        row = layout.row()
        row.prop(self, 'height', text='height')
        row = layout.row()
        row.prop(self, 'f_x', text='f_x')
        row = layout.row()
        row.prop(self, 'f_y', text='f_y')
        row = layout.row()
        row.prop(self, 'c_x', text='c_x')
        row = layout.row()
        row.prop(self, 'c_y', text='c_y')

        row = layout.row()
        row.prop(self, 'update_from_blender', text='get from blender')

    def init(self, context):
        self.node_tree = bpy.data.node_groups.new(
            self.bl_name, 'CompositorNodeTree')

        group_inputs = self.node_tree.nodes.new('NodeGroupInput')
        group_outputs = self.node_tree.nodes.new('NodeGroupOutput')

        self.node_tree.inputs.new('NodeSocketFloat', 'Distance')
        self.node_tree.outputs.new('NodeSocketFloat', 'Depth')

        # init position texture
        # Blender compositor has no default way to get the coordinates of the currently processed pixel.
        # But one can create a texture that holds the x an y coordinates in its R and G channel, respectively.
        tex = bpy.data.textures.new(name="Position", type="NONE")
        tex.use_nodes = True
        tex.node_tree.nodes.clear()
        coordinates = tex.node_tree.nodes.new("TextureNodeCoordinates")
        output = tex.node_tree.nodes.new("TextureNodeOutput")
        tex.node_tree.links.new(coordinates.outputs[0], output.inputs['Color'])

        texture_node = self.node_tree.nodes.new('CompositorNodeTexture')
        texture_node.texture = tex

        sep_rgba = self.node_tree.nodes.new('CompositorNodeSepRGBA')
        self.node_tree.links.new(texture_node.outputs[1], sep_rgba.inputs[0])

        # convert image coordinates to camera coordinates
        x = self.node_tree.nodes.new('CompositorNodeMath')
        x.label = "x"
        x.operation = 'MULTIPLY'
        self.node_tree.links.new(sep_rgba.outputs['R'], x.inputs[0])
        x.inputs[1].default_value = self.width

        y = self.node_tree.nodes.new('CompositorNodeMath')
        y.label = "y"
        y.operation = 'MULTIPLY'
        self.node_tree.links.new(sep_rgba.outputs['G'], y.inputs[0])
        y.inputs[1].default_value = self.height

        x_to_cam = self.node_tree.nodes.new('CompositorNodeMath')
        x_to_cam.label = "x_to_cam"
        x_to_cam.operation = 'SUBTRACT'
        self.node_tree.links.new(x.outputs[0], x_to_cam.inputs[0])
        x_to_cam.inputs[1].default_value = self.c_x

        y_to_cam = self.node_tree.nodes.new('CompositorNodeMath')
        y_to_cam.label = "y_to_cam"
        y_to_cam.operation = 'SUBTRACT'
        self.node_tree.links.new(y.outputs[0], y_to_cam.inputs[0])
        y_to_cam.inputs[1].default_value = self.c_y

        # calculate 1 + (x^2/fx^2) + (y^2/fy^2)
        sqr_x = self.node_tree.nodes.new('CompositorNodeMath')
        sqr_x.operation = 'MULTIPLY'
        self.node_tree.links.new(x_to_cam.outputs[0], sqr_x.inputs[0])
        self.node_tree.links.new(x_to_cam.outputs[0], sqr_x.inputs[1])

        sqr_y = self.node_tree.nodes.new('CompositorNodeMath')
        sqr_y.operation = 'MULTIPLY'
        self.node_tree.links.new(y_to_cam.outputs[0], sqr_y.inputs[0])
        self.node_tree.links.new(y_to_cam.outputs[0], sqr_y.inputs[1])

        x_over_f = self.node_tree.nodes.new('CompositorNodeMath')
        x_over_f.label = "x_over_f"
        x_over_f.operation = 'DIVIDE'
        self.node_tree.links.new(sqr_x.outputs[0], x_over_f.inputs[0])
        x_over_f.inputs[1].default_value = self.f_x * self.f_x

        y_over_f = self.node_tree.nodes.new('CompositorNodeMath')
        y_over_f.label = "y_over_f"
        y_over_f.operation = 'DIVIDE'
        self.node_tree.links.new(sqr_y.outputs[0], y_over_f.inputs[0])
        y_over_f.inputs[1].default_value = self.f_y * self.f_y

        one_plus_x = self.node_tree.nodes.new('CompositorNodeMath')
        one_plus_x.operation = 'ADD'
        one_plus_x.inputs[0].default_value = 1.0
        self.node_tree.links.new(x_over_f.outputs[0], one_plus_x.inputs[1])

        one_plus_x_plus_y = self.node_tree.nodes.new('CompositorNodeMath')
        one_plus_x_plus_y.operation = 'ADD'
        self.node_tree.links.new(
            one_plus_x.outputs[0], one_plus_x_plus_y.inputs[0])
        self.node_tree.links.new(y_over_f.outputs[0], one_plus_x_plus_y.inputs[1])

        sqrt = self.node_tree.nodes.new('CompositorNodeMath')
        sqrt.operation = 'SQRT'
        self.node_tree.links.new(one_plus_x_plus_y.outputs[0], sqrt.inputs[0])

        # calulate final result
        dist_over_ellipse = self.node_tree.nodes.new('CompositorNodeMath')
        dist_over_ellipse.operation = 'DIVIDE'
        self.node_tree.links.new(
            group_inputs.outputs['Distance'], dist_over_ellipse.inputs[0])
        self.node_tree.links.new(
            one_plus_x_plus_y.outputs[0], dist_over_ellipse.inputs[1])

        self.node_tree.links.new(
            dist_over_ellipse.outputs[0], group_outputs.inputs['Depth'])

    def copy(self, node):
        self.node_tree = node.node_tree.copy()
        self.sep_rgba = node.sep_rgba
        self.group_inputs = node.group_inputs

    def free(self):
        bpy.data.node_groups.remove(self.node_tree, do_unlink=True)


def register():
    bpy.utils.register_class(DistanceToDepth)
    newcatlist = [CompositorNodeCategory("CN_CV", "Computer Vision", items=[
                                         NodeItem("DistanceToDepth")])]
    register_node_categories("COMPUTER_VISION", newcatlist)


def unregister():
    try:
        unregister_node_categories("COMPUTER_VISION")
        bpy.utils.unregister_class(DistanceToDepth)
    except:
        pass