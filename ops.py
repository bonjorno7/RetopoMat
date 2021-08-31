from bpy.types import Context, Operator
from bpy.utils import register_class, unregister_class

from .utils import REFERENCE, RETOPO, get_material, set_material


class AddReferenceMaterialOperator(Operator):
    bl_idname = 'retopomat.add_reference_material'
    bl_label = 'Add Reference Material'
    bl_description = 'Add a reference material to the selected objects'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return any(obj.type == 'MESH' for obj in context.selected_objects)

    def execute(self, context: Context) -> set:
        material = get_material(REFERENCE)
        set_material(context.selected_objects, material)

        self.report({'INFO'}, 'Added reference material')
        return {'FINISHED'}


class AddRetopoMaterialOperator(Operator):
    bl_idname = 'retopomat.add_retopo_material'
    bl_label = 'Add Retopo Material'
    bl_description = 'Add a retopo material to the selected objects'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return any(obj.type == 'MESH' for obj in context.selected_objects)

    def execute(self, context: Context) -> set:
        material = get_material(RETOPO)
        set_material(context.selected_objects, material)

        self.report({'INFO'}, 'Added retopo material')
        return {'FINISHED'}


class RemoveMaterialsOperator(Operator):
    bl_idname = 'retopomat.remove_materials'
    bl_label = 'Remove Materials'
    bl_description = 'Remove all materials from the selected objects'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return any(obj.type == 'MESH' for obj in context.selected_objects)

    def execute(self, context: Context) -> set:
        material = None  # Only remove materials.
        set_material(context.selected_objects, material)

        self.report({'INFO'}, 'Cleared materials')
        return {'FINISHED'}


classes = (
    AddReferenceMaterialOperator,
    AddRetopoMaterialOperator,
    RemoveMaterialsOperator,
)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
