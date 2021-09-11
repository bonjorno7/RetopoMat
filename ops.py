from typing import TYPE_CHECKING

import bpy
from bpy.props import FloatProperty, IntProperty, StringProperty
from bpy.types import Context, CorrectiveSmoothModifier, Event, Object, Operator, ShrinkwrapModifier
from bpy.utils import register_class, unregister_class

from .utils import (MaterialName, ModifierName, ShrinkwrapName, apply_shrinkwrap, clean_shrinkwrap, flip_normals,
                    get_material, get_modifier, remove_modifiers, set_materials, setup_shrinkwrap, sort_modifiers)

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
    bl_options = {'INTERNAL', 'UNDO'}  # Not using REGISTER because I don't want a redo panel.

    def _update_target(self, context: Context):
        object: Object = context.active_object
        target = bpy.data.objects.get(self.target)

        # Prevent the shrinkwrap from targeting itself.
        if target is object:
            target = None

        # Clear the field if the target object doesn't exist.
        if target is None:
            self['target'] = ''

        # Set the target on the first shrinkwrap modifier.
        shrinkwrap_tangent: ShrinkwrapModifier = object.modifiers.get(ShrinkwrapName.SHRINKWRAP_TANGENT)
        if shrinkwrap_tangent is not None:
            shrinkwrap_tangent.target = target

        # Set the target on the second shrinkwrap modifier.
        shrinkwrap_nearest: ShrinkwrapModifier = object.modifiers.get(ShrinkwrapName.SHRINKWRAP_NEAREST)
        if shrinkwrap_nearest is not None:
            shrinkwrap_nearest.target = target

    target: StringProperty(
        name='Target',
        description='Target for both shrinkwrap modifiers',
        update=_update_target,
        options={'SKIP_SAVE'},
    )

    def _update_offset_tangent(self, context: Context):
        object: Object = context.active_object
        shrinkwrap_tangent: ShrinkwrapModifier = object.modifiers.get(ShrinkwrapName.SHRINKWRAP_TANGENT)
        if shrinkwrap_tangent is not None:
            shrinkwrap_tangent.offset = self.offset_tangent

    offset_tangent: FloatProperty(
        name='Offset Before',
        description='Offset for the first shrinkwrap modifier',
        default=0.0,
        soft_min=-100.0,
        soft_max=100.0,
        step=0.01,
        unit='LENGTH',
        update=_update_offset_tangent,
        options={'SKIP_SAVE'},
    )

    def _update_offset_nearest(self, context: Context):
        object: Object = context.active_object
        shrinkwrap_nearest: ShrinkwrapModifier = object.modifiers.get(ShrinkwrapName.SHRINKWRAP_NEAREST)
        if shrinkwrap_nearest is not None:
            shrinkwrap_nearest.offset = self.offset_nearest

    offset_nearest: FloatProperty(
        name='Offset After',
        description='Offset for the second shrinkwrap modifier',
        default=0.0,
        soft_min=-100.0,
        soft_max=100.0,
        step=0.01,
        unit='LENGTH',
        update=_update_offset_nearest,
        options={'SKIP_SAVE'},
    )

    def _update_factor(self, context: Context):
        object: Object = context.active_object
        corrective_smooth: CorrectiveSmoothModifier = object.modifiers.get(ShrinkwrapName.CORRECTIVE_SMOOTH)
        if corrective_smooth is not None:
            corrective_smooth.factor = self.factor

    factor: FloatProperty(
        name='Factor',
        description='Factor for the corrective smooth modifier',
        default=0.5,
        soft_min=0.0,
        soft_max=1.0,
        step=0.01,
        subtype='FACTOR',
        update=_update_factor,
        options={'SKIP_SAVE'},
    )

    def _update_iterations(self, context: Context):
        object: Object = context.active_object
        corrective_smooth: CorrectiveSmoothModifier = object.modifiers.get(ShrinkwrapName.CORRECTIVE_SMOOTH)
        if corrective_smooth is not None:
            corrective_smooth.iterations = self.iterations

    iterations: IntProperty(
        name='Repeat',
        description='Iterations for the corrective smooth modifier',
        default=5,
        soft_min=0,
        soft_max=200,
        update=_update_iterations,
        options={'SKIP_SAVE'},
    )

    def _update_scale(self, context: Context):
        object: Object = context.active_object
        smooth_modifier: CorrectiveSmoothModifier = object.modifiers.get(ShrinkwrapName.CORRECTIVE_SMOOTH)
        if smooth_modifier is not None:
            smooth_modifier.scale = self.scale

    scale: FloatProperty(
        name='Scale',
        description='Scale for the corrective smooth modifier',
        default=1.0,
        soft_min=0.0,
        soft_max=2.0,
        step=0.01,
        subtype='FACTOR',
        update=_update_scale,
        options={'SKIP_SAVE'},
    )

    def draw(self, context: Context):
        layout = self.layout.column()
        layout.use_property_split = True
        layout.use_property_decorate = False

        sub = layout.column()
        sub.alert = (not self.target)
        sub.prop_search(self, 'target', search_data=bpy.data, search_property='objects')

        sub = layout.column()
        sub.enabled = bool(self.target)
        sub.prop(self, 'offset_tangent')
        sub.prop(self, 'offset_nearest')

        layout.separator()

        layout.prop(self, 'factor')
        layout.prop(self, 'iterations')
        layout.prop(self, 'scale')

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH')

    def invoke(self, context: 'Context', event: Event) -> set:
        object: Object = context.active_object

        # Instead of this check, it'd be ideal if I could just remove the modifiers on cancel.
        # But since there's no way to know when and if a props dialog is closed, I don't know how.
        for modifier_name in ShrinkwrapName.modifiers():
            if modifier_name in object.modifiers:
                self.report({'WARNING'}, 'First remove existing Quick Shrinkwrap modifiers')
                return {'CANCELLED'}

        setup_shrinkwrap(object)

        # Use the reference object as default shrinkwrap target.
        settings: 'RetopoMatSettings' = context.scene.retopomat
        reference_object = settings.reference_object
        if (reference_object is not None) and (reference_object is not object):
            self.target = reference_object.name

        # Use a props dialog so the user can tweak values, and hit OK to apply the modifiers.
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        apply_shrinkwrap(object)

        self.report({'INFO'}, 'Applied modifiers')
        return {'FINISHED'}

    def __del__(self):
        object: Object = bpy.context.active_object
        clean_shrinkwrap(object)


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
