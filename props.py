from bpy.props import BoolProperty, FloatProperty, FloatVectorProperty, PointerProperty
from bpy.types import Context, PropertyGroup, Scene
from bpy.utils import register_class, unregister_class

from .utils import MaterialName, get_material, get_wire_modifier


class RetopoMatSettings(PropertyGroup):

    def _update_reference_color(self, context: Context):
        material = get_material(MaterialName.REFERENCE)
        node = material.node_tree.nodes['Principled BSDF']
        node.inputs['Base Color'].default_value = self.reference_color

    reference_color: FloatVectorProperty(
        name='Reference Color',
        description='Color of the reference material',
        subtype='COLOR',
        size=4,
        default=(0.2, 0.2, 0.2, 1.0),
        min=0.0,
        max=1.0,
        update=_update_reference_color,
    )

    def _update_reference_opacity(self, context: Context):
        material = get_material(MaterialName.REFERENCE)
        node = material.node_tree.nodes['Principled BSDF']
        node.inputs['Alpha'].default_value = self.reference_opacity

    reference_opacity: FloatProperty(
        name='Reference Opacity',
        description='Opacity of the reference material',
        default=0.8,
        min=0.0,
        soft_max=1.0,
        update=_update_reference_opacity,
    )

    def _update_retopo_color(self, context: Context):
        material = get_material(MaterialName.RETOPO)
        node = material.node_tree.nodes['Emission']
        node.inputs['Color'].default_value = self.retopo_color

    retopo_color: FloatVectorProperty(
        name='Retopo Color',
        description='Color of the retopo material',
        subtype='COLOR',
        size=4,
        default=(0.3, 0.6, 0.9, 1.0),
        min=0.0,
        max=1.0,
        update=_update_retopo_color,
    )

    def _update_wire_color(self, context: Context):
        material = get_material(MaterialName.WIRE)
        node = material.node_tree.nodes['Emission']
        node.inputs['Color'].default_value = self.wire_color

    wire_color: FloatVectorProperty(
        name='Wire Color',
        description='Color of the wire material',
        subtype='COLOR',
        size=4,
        default=(0.0, 0.0, 0.0, 1.0),
        min=0.0,
        max=1.0,
        update=_update_wire_color,
    )

    def _update_wire_visibility(self, context: Context):
        modifier = get_wire_modifier(context.active_object)

        if modifier is not None:
            modifier.show_viewport = self.wire_visibility

    wire_visibility: BoolProperty(
        name='Wire Visibility',
        description='Whether to show the wireframe',
        default=True,
        update=_update_wire_visibility,
    )

    def _update_wire_thickness(self, context: Context):
        modifier = get_wire_modifier(context.active_object)

        if modifier is not None:
            modifier.thickness = self.wire_thickness

    wire_thickness: FloatProperty(
        name='Wire Thickness',
        description='Thickness for the wireframe',
        default=0.5,
        min=0.0,
        soft_max=10.0,
        update=_update_wire_thickness,
    )


classes = (RetopoMatSettings,)


def register():
    for cls in classes:
        register_class(cls)

    Scene.retopo_mat = PointerProperty(type=RetopoMatSettings)


def unregister():
    del Scene.retopo_mat

    for cls in reversed(classes):
        unregister_class(cls)
