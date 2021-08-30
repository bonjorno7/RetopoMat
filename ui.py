from bpy.types import Context, Panel, UILayout
from bpy.utils import register_class, unregister_class


class RetopoMatPanel(Panel):
    bl_category = 'RetopoMat'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def configure_layout(self) -> UILayout:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        return layout


class MaterialsPanel(RetopoMatPanel):
    bl_idname = 'RETOPOMAT_PT_materials'
    bl_label = 'Materials'

    def draw(self, context: Context):
        layout = self.configure_layout()

        layout.operator('retopomat.add_reference_material')
        layout.operator('retopomat.add_retopo_material')
        layout.operator('retopomat.remove_materials')


classes = (
    MaterialsPanel,
)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
