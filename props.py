from typing import Any

import bpy
from bpy.props import BoolProperty, FloatProperty, FloatVectorProperty, PointerProperty
from bpy.types import Object, PropertyGroup, Scene
from bpy.utils import register_class, unregister_class

from .utils import MaterialName, ModifierName, get_material, get_modifier


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
            material.blend_method = 'BLEND' if value[3] < 1.0 else 'OPAQUE'
            node = material.node_tree.nodes['Principled BSDF']
            node.inputs['Base Color'].default_value = value[:3] + (1.0,)
            node.inputs['Alpha'].default_value = value[3]

        self.set_internal('reference_color', value)

    reference_color: FloatVectorProperty(
        name='Reference Color',
        description='Color and opacity of the reference material',
        subtype='COLOR',
        size=4,
        default=(0.2, 0.2, 0.2, 1.0),
        min=0.0,
        max=1.0,
        get=_get_reference_color,
        set=_set_reference_color,
    )

    def _get_retopo_color(self) -> tuple:
        object: Object = bpy.context.active_object
        material = get_material(object, MaterialName.RETOPO)

        if material is not None:
            node = material.node_tree.nodes['Principled BSDF']
            color = node.inputs['Base Color'].default_value[:3]
            alpha = node.inputs['Alpha'].default_value
            return color + (alpha,)

        return self.get_internal('retopo_color')

    def _set_retopo_color(self, value: tuple):
        object: Object = bpy.context.active_object
        material = get_material(object, MaterialName.RETOPO)

        if material is not None:
            material.blend_method = 'BLEND' if value[3] < 1.0 else 'OPAQUE'
            node = material.node_tree.nodes['Principled BSDF']
            node.inputs['Base Color'].default_value = value[:3] + (1.0,)
            node.inputs['Alpha'].default_value = value[3]

        self.set_internal('retopo_color', value)

    retopo_color: FloatVectorProperty(
        name='Retopo Color',
        description='Color of the retopo material',
        subtype='COLOR',
        size=4,
        default=(0.3, 0.6, 0.9, 0.2),
        min=0.0,
        max=1.0,
        get=_get_retopo_color,
        set=_set_retopo_color,
    )

    def _get_wireframe_color(self) -> tuple:
        object: Object = bpy.context.active_object
        material = get_material(object, MaterialName.WIREFRAME)

        if material is not None:
            node = material.node_tree.nodes['Principled BSDF']
            color = node.inputs['Emission'].default_value[:3]
            alpha = node.inputs['Alpha'].default_value
            return color + (alpha,)

        return self.get_internal('wireframe_color')

    def _set_wireframe_color(self, value: tuple):
        object: Object = bpy.context.active_object
        material = get_material(object, MaterialName.WIREFRAME)

        if material is not None:
            material.blend_method = 'BLEND' if value[3] < 1.0 else 'OPAQUE'
            node = material.node_tree.nodes['Principled BSDF']
            node.inputs['Emission'].default_value = value[:3] + (1.0,)
            node.inputs['Alpha'].default_value = value[3]

        self.set_internal('wireframe_color', value)

    wireframe_color: FloatVectorProperty(
        name='Wireframe Color',
        description='Color of the wireframe material',
        subtype='COLOR',
        size=4,
        default=(0.0, 0.0, 0.0, 0.99),
        min=0.0,
        max=1.0,
        get=_get_wireframe_color,
        set=_set_wireframe_color,
    )

    def _get_displace_visibility(self) -> bool:
        object: Object = bpy.context.active_object
        modifier = get_modifier(object, ModifierName.DISPLACE)

        if modifier is not None:
            return modifier.show_viewport

        return self.get_internal('displace_visibility')

    def _set_displace_visibility(self, value: bool):
        object: Object = bpy.context.active_object
        modifier = get_modifier(object, ModifierName.DISPLACE)

        if modifier is not None:
            modifier.show_viewport = value

        self.set_internal('displace_visibility', value)

    displace_visibility: BoolProperty(
        name='Displace Visibility',
        description='Whether to show the displace modifier',
        default=False,
        get=_get_displace_visibility,
        set=_set_displace_visibility,
    )

    def _get_displace_strength(self) -> float:
        object: Object = bpy.context.active_object
        modifier = get_modifier(object, ModifierName.DISPLACE)

        if modifier is not None:
            return modifier.strength

        return self.get_internal('displace_strength')

    def _set_displace_strength(self, value: float):
        object: Object = bpy.context.active_object
        modifier = get_modifier(object, ModifierName.DISPLACE)

        if modifier is not None:
            modifier.strength = value

        self.set_internal('displace_strength', value)

    displace_strength: FloatProperty(
        name='Displace Strength',
        description='Strength for the displace modifier',
        subtype='DISTANCE',
        unit='LENGTH',
        default=0.02,
        soft_min=0.0,
        soft_max=1.0,
        step=0.01,
        get=_get_displace_strength,
        set=_set_displace_strength,
    )

    def _get_solidify_visibility(self) -> bool:
        object: Object = bpy.context.active_object
        modifier = get_modifier(object, ModifierName.SOLIDIFY)

        if modifier is not None:
            return modifier.show_viewport

        return self.get_internal('solidify_visibility')

    def _set_solidify_visibility(self, value: bool):
        object: Object = bpy.context.active_object
        modifier = get_modifier(object, ModifierName.SOLIDIFY)

        if modifier is not None:
            modifier.show_viewport = value

        self.set_internal('solidify_visibility', value)

    solidify_visibility: BoolProperty(
        name='Solidify Visibility',
        description='Whether to show the solidify modifier',
        default=False,
        get=_get_solidify_visibility,
        set=_set_solidify_visibility,
    )

    def _get_solidify_thickness(self) -> float:
        object: Object = bpy.context.active_object
        modifier = get_modifier(object, ModifierName.SOLIDIFY)

        if modifier is not None:
            return modifier.thickness

        return self.get_internal('solidify_thickness')

    def _set_solidify_thickness(self, value: float):
        object: Object = bpy.context.active_object
        modifier = get_modifier(object, ModifierName.SOLIDIFY)

        if modifier is not None:
            modifier.thickness = value

        self.set_internal('solidify_thickness', value)

    solidify_thickness: FloatProperty(
        name='Solidify Thickness',
        description='Thickness for the solidify modifier',
        subtype='DISTANCE',
        unit='LENGTH',
        default=0.02,
        soft_min=0.0,
        soft_max=1.0,
        step=0.01,
        get=_get_solidify_thickness,
        set=_set_solidify_thickness,
    )

    def _get_wireframe_visibility(self) -> bool:
        object: Object = bpy.context.active_object
        modifier = get_modifier(object, ModifierName.WIREFRAME)

        if modifier is not None:
            return modifier.show_viewport

        return self.get_internal('wireframe_visibility')

    def _set_wireframe_visibility(self, value: bool):
        object: Object = bpy.context.active_object
        modifier = get_modifier(object, ModifierName.WIREFRAME)

        if modifier is not None:
            modifier.show_viewport = value

        self.set_internal('wireframe_visibility', value)

    wireframe_visibility: BoolProperty(
        name='Wireframe Visibility',
        description='Whether to show the wireframe modifier',
        default=True,
        get=_get_wireframe_visibility,
        set=_set_wireframe_visibility,
    )

    def _get_wireframe_thickness(self) -> float:
        object: Object = bpy.context.active_object
        modifier = get_modifier(object, ModifierName.WIREFRAME)

        if modifier is not None:
            return modifier.thickness

        return self.get_internal('wireframe_thickness')

    def _set_wireframe_thickness(self, value: float):
        object: Object = bpy.context.active_object
        modifier = get_modifier(object, ModifierName.WIREFRAME)

        if modifier is not None:
            modifier.thickness = value

        self.set_internal('wireframe_thickness', value)

    wireframe_thickness: FloatProperty(
        name='Wireframe Thickness',
        description='Thickness for the wireframe modifier',
        subtype='DISTANCE',
        unit='LENGTH',
        default=0.02,
        soft_min=0.0,
        soft_max=1.0,
        step=0.01,
        get=_get_wireframe_thickness,
        set=_set_wireframe_thickness,
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
