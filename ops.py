from typing import TYPE_CHECKING

import bpy
from bpy.props import FloatProperty, IntProperty, StringProperty
from bpy.types import Context, Event, Object, Operator
from bpy.utils import register_class, unregister_class

from .utils import (MaterialName, ModifierName, flip_normals, get_material, get_modifier, quick_shrinkwrap,
                    remove_modifiers, set_materials, sort_modifiers)

if TYPE_CHECKING:
    from .props import RetopoMatSettings


class AddReferenceMaterialOperator(Operator):
    bl_idname = 'retopomat.add_reference_material'
    bl_label = 'Add Reference Material'
    bl_description = '.\n'.join((
        'Add a reference material to the active object',
        'This removes your material slots and retopo modifiers',
    ))
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH') and (object.mode == 'OBJECT')

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        material = get_material(object, MaterialName.REFERENCE, create=True)
        set_materials(object, [material])
        remove_modifiers(object)

        self.report({'INFO'}, 'Added reference material')
        return {'FINISHED'}


class AddRetopoMaterialsOperator(Operator):
    bl_idname = 'retopomat.add_retopo_materials'
    bl_label = 'Add Retopo Materials'
    bl_description = 'Add retopo materials and modifiers to the active object'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH') and (object.mode == 'OBJECT')

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        retopo_material = get_material(object, MaterialName.RETOPO, create=True)
        wireframe_material = get_material(object, MaterialName.WIREFRAME, create=True)
        set_materials(object, [retopo_material, wireframe_material])

        get_modifier(object, ModifierName.DISPLACE, create=True)
        get_modifier(object, ModifierName.SOLIDIFY, create=True)
        get_modifier(object, ModifierName.WIREFRAME, create=True)

        self.report({'INFO'}, 'Added retopo material')
        return {'FINISHED'}


class RemoveMaterialsOperator(Operator):
    bl_idname = 'retopomat.remove_materials'
    bl_label = 'Remove Materials'
    bl_description = 'Remove all materials and retopo modifiers from the active object'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH') and (object.mode == 'OBJECT')

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        set_materials(object, [])
        remove_modifiers(object)

        self.report({'INFO'}, 'Cleared materials')
        return {'FINISHED'}


class SortModifiersOperator(Operator):
    bl_idname = 'retopomat.sort_modifiers'
    bl_label = 'Sort Modifiers'
    bl_description = 'Move retopo modifiers to the bottom of the stack'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return any(get_modifier(object, name) for name in ModifierName)

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        sort_modifiers(object)

        self.report({'INFO'}, 'Sorted modifiers')
        return {'FINISHED'}


class QuickShrinkwrapOperator(Operator):
    bl_idname = 'retopomat.quick_shrinkwrap'
    bl_label = 'Quick Shrinkwrap'
    bl_description = 'Use shrinkwrap and corrective smooth modifiers'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    target: StringProperty(
        name='Target',
        description='Target for both shrinkwrap modifiers',
    )

    offset_one: FloatProperty(
        name='Offset Before',
        description='Offset for the first shrinkwrap modifier',
        default=0.0,
        soft_min=-100.0,
        soft_max=100.0,
        step=0.01,
        unit='LENGTH',
    )

    offset_two: FloatProperty(
        name='Offset After',
        description='Offset for the second shrinkwrap modifier',
        default=0.0,
        soft_min=-100.0,
        soft_max=100.0,
        step=0.01,
        unit='LENGTH',
    )

    factor: FloatProperty(
        name='Factor',
        description='Factor for the corrective smooth modifier',
        default=0.5,
        soft_min=0.0,
        soft_max=1.0,
        step=0.01,
        subtype='FACTOR',
    )

    iterations: IntProperty(
        name='Repeat',
        description='Iterations for the corrective smooth modifier',
        default=5,
        soft_min=0,
        soft_max=200,
    )

    scale: FloatProperty(
        name='Scale',
        description='Scale for the corrective smooth modifier',
        default=1.0,
        soft_min=0.0,
        soft_max=2.0,
        step=0.01,
        subtype='FACTOR',
    )

    def draw(self, context: Context):
        layout = self.layout.column()
        layout.use_property_split = True
        layout.use_property_decorate = False

        object: Object = context.active_object
        target = bpy.data.objects.get(self.target)
        valid = (target is not None) and (target is not object)

        row = layout.row()
        row.alert = not valid
        col = layout.column()
        col.enabled = valid

        row.prop_search(self, 'target', search_data=bpy.data, search_property='objects')
        col.prop(self, 'offset_one')
        col.prop(self, 'offset_two')

        col.separator()

        col.prop(self, 'factor')
        col.prop(self, 'iterations')
        col.prop(self, 'scale')

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH')

    def invoke(self, context: 'Context', event: Event) -> set:
        settings: 'RetopoMatSettings' = context.scene.retopomat
        target = settings.reference_object

        if target is not None:
            self.target = target.name

        return self.execute(context)

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        target = bpy.data.objects.get(self.target)

        if target is None:
            self.report({'WARNING'}, 'Shrinkwrap needs a target')
        elif target is object:
            self.report({'WARNING'}, 'Can not shrinkwrap to self')
        else:
            quick_shrinkwrap(
                object=object,
                target=target,
                offset_one=self.offset_one,
                offset_two=self.offset_two,
                factor=self.factor,
                iterations=self.iterations,
                scale=self.scale,
            )

        return {'FINISHED'}


class FlipNormalsOperator(Operator):
    bl_idname = 'retopomat.flip_normals'
    bl_label = 'Flip Normals'
    bl_description = 'Flip normals of selected faces in your mesh'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH')

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        flip_normals(object)

        self.report({'INFO'}, 'Flipped normals')
        return {'FINISHED'}


classes = (
    AddReferenceMaterialOperator,
    AddRetopoMaterialsOperator,
    RemoveMaterialsOperator,
    SortModifiersOperator,
    QuickShrinkwrapOperator,
    FlipNormalsOperator,
)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
