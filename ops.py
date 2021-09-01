from bpy.types import Context, Event, Operator
from bpy.utils import register_class, unregister_class

from .utils import MaterialName, check_material_slots, get_material, set_materials


class AddReferenceMaterialOperator(Operator):
    bl_idname = 'retopomat.add_reference_material'
    bl_label = 'Add Reference Material'
    bl_description = 'Add a reference material to the selected objects'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return any(obj.type == 'MESH' for obj in context.selected_objects)

    def draw(self, context: Context):
        sub = self.layout.box().column()
        sub.label(text='One of your objects has mutliple material slots.')
        sub.label(text='This operation will remove them.')

    def invoke(self, context: Context, event: Event) -> set:
        if check_material_slots(context.selected_objects):
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def execute(self, context: Context) -> set:
        set_materials(context.selected_objects, [material])
        material = get_material(MaterialName.REFERENCE, create=True)

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
        set_materials(context.selected_objects, [retopo_material, wire_material])
        retopo_material = get_material(MaterialName.RETOPO, create=True)
        wire_material = get_material(MaterialName.WIRE, create=True)

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
        set_materials(context.selected_objects, [])

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
