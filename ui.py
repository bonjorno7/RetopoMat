from traceback import print_exc

from bpy.types import Context, Panel, UILayout
from bpy.utils import register_class, unregister_class

from .ops import (AddReferenceMaterialOperator, AddRetopoMaterialOperator, FlipNormalsOperator,
                  MoveWireframeToBottomOperator, RemoveMaterialsOperator)
from .props import RetopoMatSettings


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

        layout.operator(AddReferenceMaterialOperator.bl_idname)
        layout.operator(AddRetopoMaterialOperator.bl_idname)
        layout.operator(RemoveMaterialsOperator.bl_idname)


class SettingsPanel(RetopoMatPanel):
    bl_idname = 'RETOPOMAT_PT_settings'
    bl_label = 'Settings'

    def draw(self, context: Context):
        layout = self.configure_layout().column()
        settings: RetopoMatSettings = context.scene.retopo_mat

        layout.prop(settings, 'reference_color')
        layout.prop(settings, 'retopo_color')

        layout.separator()

        layout.prop(settings, 'wire_visibility')
        sub = layout.column()
        sub.enabled = settings.wire_visibility
        sub.prop(settings, 'wire_color')
        sub.prop(settings, 'wire_thickness')

        try:
            sub.prop(context.preferences.themes['Default'].view_3d, 'vertex_size', text='Vertex Size')
        except:
            print_exc()

        layout.separator()

        try:
            layout.prop(context.space_data.shading, 'studiolight_rotate_z', text='World Rotation')
            layout.prop(context.space_data.shading, 'studiolight_intensity', text='World Strength')
        except:
            print_exc()


class UtilitiesPanel(RetopoMatPanel):
    bl_idname = 'RETOPOMAT_PT_utilities'
    bl_label = 'Utilities'

    def draw(self, context: Context):
        layout = self.configure_layout()

        layout.operator(FlipNormalsOperator.bl_idname)
        layout.operator(MoveWireframeToBottomOperator.bl_idname)


classes = (
    MaterialsPanel,
    SettingsPanel,
    UtilitiesPanel,
)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
