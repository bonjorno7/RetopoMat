from traceback import print_exc

from bpy.types import Context, Panel, UILayout
from bpy.utils import register_class, unregister_class

from .ops import (AddReferenceMaterialOperator, AddRetopoMaterialOperator, FlipNormalsOperator,
                  MoveModifiersToBottomOperator, RemoveMaterialsOperator)
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
    bl_order = 1

    def draw(self, context: Context):
        layout = self.configure_layout()

        layout.operator(AddReferenceMaterialOperator.bl_idname)
        layout.operator(AddRetopoMaterialOperator.bl_idname)
        layout.operator(RemoveMaterialsOperator.bl_idname)


class SettingsPanel(RetopoMatPanel):
    bl_idname = 'RETOPOMAT_PT_settings'
    bl_label = 'Settings'
    bl_order = 2

    def draw(self, context: Context):
        layout = self.configure_layout().column()
        settings: RetopoMatSettings = context.scene.retopo_mat

        row = layout.row(align=True)
        row.prop(settings, 'reference_color', text='Reference')
        icon = 'IMAGE_RGB_ALPHA' if settings.reference_blend else 'IMAGE_RGB'
        row.prop(settings, 'reference_blend', text='', icon=icon)

        row = layout.row(align=True)
        row.prop(settings, 'retopo_color', text='Retopo')
        icon = 'IMAGE_RGB_ALPHA' if settings.retopo_blend else 'IMAGE_RGB'
        row.prop(settings, 'retopo_blend', text='', icon=icon)

        row = layout.row(align=True)
        row.prop(settings, 'wireframe_color', text='Wireframe')
        icon = 'IMAGE_RGB_ALPHA' if settings.wireframe_blend else 'IMAGE_RGB'
        row.prop(settings, 'wireframe_blend', text='', icon=icon)

        layout.separator()

        row = layout.row(align=True)
        row.prop(settings, 'displace_strength', text='Offset')
        icon = 'RESTRICT_VIEW_OFF' if settings.displace_visibility else 'RESTRICT_VIEW_ON'
        row.prop(settings, 'displace_visibility', text='', icon=icon)

        row = layout.row(align=True)
        row.prop(settings, 'solidify_thickness', text='Thickness')
        icon = 'RESTRICT_VIEW_OFF' if settings.solidify_visibility else 'RESTRICT_VIEW_ON'
        row.prop(settings, 'solidify_visibility', text='', icon=icon)

        row = layout.row(align=True)
        row.prop(settings, 'wireframe_thickness', text='Wireframe')
        icon = 'RESTRICT_VIEW_OFF' if settings.wireframe_visibility else 'RESTRICT_VIEW_ON'
        row.prop(settings, 'wireframe_visibility', text='', icon=icon)

        layout.separator()

        try:
            layout.prop(context.space_data.shading, 'studiolight_rotate_z', text='World Rotation')
            layout.prop(context.space_data.shading, 'studiolight_intensity', text='World Strength')
            layout.prop(context.preferences.themes['Default'].view_3d, 'vertex_size', text='Vertex Size')
        except:
            print_exc()


class UtilitiesPanel(RetopoMatPanel):
    bl_idname = 'RETOPOMAT_PT_utilities'
    bl_label = 'Utilities'
    bl_order = 3

    def draw(self, context: Context):
        layout = self.configure_layout()

        layout.operator(MoveModifiersToBottomOperator.bl_idname)
        layout.operator(FlipNormalsOperator.bl_idname)


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
