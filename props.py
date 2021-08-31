from bpy.props import BoolProperty, FloatProperty, FloatVectorProperty, PointerProperty
from bpy.types import Context, PropertyGroup, WindowManager
from bpy.utils import register_class, unregister_class

from .utils import get_material, MaterialName


class RetopoMatSettings(PropertyGroup):

    def _update_color(self, context: Context):
        material = get_material(MaterialName.RETOPO)
        node = material.node_tree.nodes['Emission']
        socket = node.inputs['Color']
        socket.default_value = self.color

    color: FloatVectorProperty(
        name='Color',
        description='Color of the retopo material',
        subtype='COLOR',
        size=4,
        default=(0.9, 0.6, 0.0, 1.0),
        min=0.0,
        max=1.0,
        update=_update_color,
    )

    def _update_intensity(self, context: Context):
        material = get_material(MaterialName.RETOPO)
        node = material.node_tree.nodes['Emission']
        socket = node.inputs['Strength']
        socket.default_value = self.intensity

    intensity: FloatProperty(
        name='Intensity',
        description='Intensity of the retopo material',
        default=1.0,
        min=0.0,
        soft_max=1.0,
        update=_update_intensity,
    )

    wire_visibility: BoolProperty(
        name='Wire Visibility',
        description='Whether to show the wireframe',
        default=True,
        # TODO: Add getter and setter for selected object wireframe visibility.
    )

    wire_thickness: FloatProperty(
        name='Wire Thickness',
        description='Thickness for the wireframe',
        default=0.5,
        min=0.0,
        soft_max=10.0,
        # TODO: Add getter and setter for selected object wireframe thickness.
    )


classes = (RetopoMatSettings,)


def register():
    for cls in classes:
        register_class(cls)

    WindowManager.retopo_mat = PointerProperty(type=RetopoMatSettings)


def unregister():
    del WindowManager.retopo_mat

    for cls in reversed(classes):
        unregister_class(cls)
