from typing import Any

import bpy
from bpy.props import BoolProperty, FloatProperty, FloatVectorProperty, PointerProperty
from bpy.types import Object, PropertyGroup, Scene
from bpy.utils import register_class, unregister_class

from .utils import MaterialName, get_material, get_wire_modifier


class RetopoMatSettings(PropertyGroup):

    def get_default(self, key: str) -> Any:
        property = self.bl_rna.properties[key]

        if property.is_array:
            return property.default_array
        else:
            return property.default

    def get_internal(self, key: str) -> Any:
        return self.get(key, self.get_default(key))

    def set_internal(self, key: str, value: Any):
        self[key] = value

    def _get_reference_color(self) -> tuple:
        object: Object = bpy.context.active_object
        material = get_material(object, MaterialName.REFERENCE)

        if material is not None:
            node = material.node_tree.nodes['Principled BSDF']
            color = node.inputs['Base Color'].default_value[:3]
            alpha = node.inputs['Alpha'].default_value
            return color + (alpha,)

        return self.get_internal('reference_color')

    def _set_reference_color(self, value: tuple):
        object: Object = bpy.context.active_object
        material = get_material(object, MaterialName.REFERENCE)

        if material is not None:
            node = material.node_tree.nodes['Principled BSDF']
            node.inputs['Base Color'].default_value = value[:3] + (1.0,)
            node.inputs['Alpha'].default_value = value[3]

        self.set_internal('reference_color', value)

    reference_color: FloatVectorProperty(
        name='Reference Color',
        description='Color and opacity of the reference material',
        subtype='COLOR',
        size=4,
        default=(0.2, 0.2, 0.2, 0.8),
        min=0.0,
        max=1.0,
        get=_get_reference_color,
        set=_set_reference_color,
    )

    def _get_retopo_color(self) -> tuple:
        object: Object = bpy.context.active_object
        material = get_material(object, MaterialName.RETOPO)

        if material is not None:
            node = material.node_tree.nodes['Emission']
            color = node.inputs['Color'].default_value[:3]
            return color + (1.0,)

        return self.get_internal('retopo_color')[:3] + (1.0,)

    def _set_retopo_color(self, value: tuple):
        object: Object = bpy.context.active_object
        material = get_material(object, MaterialName.RETOPO)

        if material is not None:
            node = material.node_tree.nodes['Emission']
            node.inputs['Color'].default_value = value[:3] + (1.0,)

        self.set_internal('retopo_color', value[:3] + (1.0,))

    retopo_color: FloatVectorProperty(
        name='Retopo Color',
        description='Color of the retopo material',
        subtype='COLOR',
        size=4,
        default=(0.3, 0.6, 0.9, 1.0),
        min=0.0,
        max=1.0,
        get=_get_retopo_color,
        set=_set_retopo_color,
    )

    def _get_wire_color(self) -> tuple:
        object: Object = bpy.context.active_object
        material = get_material(object, MaterialName.WIRE)

        if material is not None:
            node = material.node_tree.nodes['Emission']
            color = node.inputs['Color'].default_value[:3]
            return color + (1.0,)

        return self.get_internal('wire_color')[:3] + (1.0,)

    def _set_wire_color(self, value: tuple):
        object: Object = bpy.context.active_object
        material = get_material(object, MaterialName.WIRE)

        if material is not None:
            node = material.node_tree.nodes['Emission']
            node.inputs['Color'].default_value = value[:3] + (1.0,)

        self.set_internal('wire_color', value[:3] + (1.0,))

    wire_color: FloatVectorProperty(
        name='Wire Color',
        description='Color of the wire material',
        subtype='COLOR',
        size=4,
        default=(0.0, 0.0, 0.0, 1.0),
        min=0.0,
        max=1.0,
        get=_get_wire_color,
        set=_set_wire_color,
    )

    def _get_wire_visibility(self) -> bool:
        object: Object = bpy.context.active_object
        modifier = get_wire_modifier(object)

        if modifier is not None:
            return modifier.show_viewport

        default = self.bl_rna.properties['wire_visibility'].default
        return self.get('wire_visibility', default)

    def _set_wire_visibility(self, value: bool):
        object: Object = bpy.context.active_object
        modifier = get_wire_modifier(object)

        if modifier is not None:
            modifier.show_viewport = value

        self['wire_visibility'] = value

    wire_visibility: BoolProperty(
        name='Wire Visibility',
        description='Whether to show the wireframe',
        default=True,
        get=_get_wire_visibility,
        set=_set_wire_visibility,
    )

    def _get_wire_thickness(self) -> float:
        object: Object = bpy.context.active_object
        modifier = get_wire_modifier(object)

        if modifier is not None:
            return modifier.thickness

        default = self.bl_rna.properties['wire_thickness'].default
        return self.get('wire_thickness', default)

    def _set_wire_thickness(self, value: float):
        object: Object = bpy.context.active_object
        modifier = get_wire_modifier(object)

        if modifier is not None:
            modifier.thickness = value

        self['wire_thickness'] = value

    wire_thickness: FloatProperty(
        name='Wire Thickness',
        description='Thickness for the wireframe',
        subtype='DISTANCE',
        unit='LENGTH',
        default=0.02,
        soft_min=0.0,
        soft_max=1.0,
        step=0.01,
        get=_get_wire_thickness,
        set=_set_wire_thickness,
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
