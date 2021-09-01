from bpy.types import Context, Event, Operator
from bpy.utils import register_class, unregister_class

from .utils import (MaterialName, check_material_slots, flip_normals, get_material, get_wire_modifier,
                    remove_wire_modifier, set_materials)


class AddReferenceMaterialOperator(Operator):
    bl_idname = 'retopomat.add_reference_material'
    bl_label = 'Add Reference Material'
    bl_description = 'Add a reference material to the active object'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object = context.active_object
        return (object is not None) and (object.type == 'MESH') and (object.mode == 'OBJECT')

    def draw(self, context: Context):
        sub = self.layout.box().column()
        sub.label(text='Your object has mutliple material slots.')
        sub.label(text='This operation will remove them.')

    def invoke(self, context: Context, event: Event) -> set:
        if check_material_slots(context.selected_objects):
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def execute(self, context: Context) -> set:
        material = get_material(MaterialName.REFERENCE, create=True)
        set_materials(context.active_object, [material])

        self.report({'INFO'}, 'Added reference material')
        return {'FINISHED'}


class AddRetopoMaterialOperator(Operator):
    bl_idname = 'retopomat.add_retopo_material'
    bl_label = 'Add Retopo Material'
    bl_description = 'Add retopo materials and wireframe modifier to the active object'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object = context.active_object
        return (object is not None) and (object.type == 'MESH') and (object.mode == 'OBJECT')

    def execute(self, context: Context) -> set:
        retopo_material = get_material(MaterialName.RETOPO, create=True)
        wire_material = get_material(MaterialName.WIRE, create=True)
        set_materials(context.active_object, [retopo_material, wire_material])
        get_wire_modifier(context.active_object, create=True)

        self.report({'INFO'}, 'Added retopo material')
        return {'FINISHED'}


class RemoveMaterialsOperator(Operator):
    bl_idname = 'retopomat.remove_materials'
    bl_label = 'Remove Materials'
    bl_description = 'Remove all materials and our wireframe modifier from the active object'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object = context.active_object
        return (object is not None) and (object.type == 'MESH') and (object.mode == 'OBJECT')

    def execute(self, context: Context) -> set:
        set_materials(context.active_object, [])
        remove_wire_modifier(context.active_object)

        self.report({'INFO'}, 'Cleared materials')
        return {'FINISHED'}


class FlipNormalsOperator(Operator):
    bl_idname = 'retopomat.flip_normals'
    bl_label = 'Flip Normals'
    bl_description = 'Flip normals of all the faces in your mesh'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object = context.active_object
        return (object is not None) and (object.type == 'MESH') and (object.mode == 'EDIT')

    def execute(self, context: Context) -> set:
        flip_normals(context.active_object)

        self.report({'INFO'}, 'Flipped normals')
        return {'FINISHED'}


classes = (
    AddReferenceMaterialOperator,
    AddRetopoMaterialOperator,
    RemoveMaterialsOperator,
    FlipNormalsOperator,
)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
