from bpy.types import Context, Event, Object, Operator
from bpy.utils import register_class, unregister_class

from .utils import (MaterialName, ModifierName, check_material_slots, flip_normals, get_material, get_modifier,
                    move_modifiers_to_bottom, remove_modifiers, set_materials)


class AddReferenceMaterialOperator(Operator):
    bl_idname = 'retopomat.add_reference_material'
    bl_label = 'Add Reference Material'
    bl_description = 'Add a reference material to the active object'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH') and (object.mode == 'OBJECT')

    def draw(self, context: Context):
        sub = self.layout.box().column()
        sub.label(text='Your object has mutliple material slots.')
        sub.label(text='This operation will remove them.')

    def invoke(self, context: Context, event: Event) -> set:
        object: Object = context.active_object

        if check_material_slots(object):
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        material = get_material(object, MaterialName.REFERENCE, create=True)
        set_materials(object, [material])

        self.report({'INFO'}, 'Added reference material')
        return {'FINISHED'}


class AddRetopoMaterialOperator(Operator):
    bl_idname = 'retopomat.add_retopo_material'
    bl_label = 'Add Retopo Material'
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


class MoveModifiersToBottomOperator(Operator):
    bl_idname = 'retopomat.move_modifiers_to_bottom'
    bl_label = 'Move Modifiers to Bottom'
    bl_description = 'Move retopo modifiers to the bottom of the stack'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH')

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        move_modifiers_to_bottom(object)

        self.report({'INFO'}, 'Moved retopo modifiers to bottom')
        return {'FINISHED'}


class FlipNormalsOperator(Operator):
    bl_idname = 'retopomat.flip_normals'
    bl_label = 'Flip Normals'
    bl_description = 'Flip normals of all the faces in your mesh'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH') and (object.mode == 'EDIT')

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        flip_normals(object)

        self.report({'INFO'}, 'Flipped normals')
        return {'FINISHED'}


classes = (
    AddReferenceMaterialOperator,
    AddRetopoMaterialOperator,
    RemoveMaterialsOperator,
    MoveModifiersToBottomOperator,
    FlipNormalsOperator,
)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
