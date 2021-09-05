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

    def row_with_heading(self, layout: UILayout, heading: str) -> UILayout:
        try:  # Newer versions of Blender can use heading.
            return layout.row(heading=heading)

        except:  # Older version of Blender have to use split.
            split = layout.row().split(factor=0.4)
            split.use_property_split = False
            split.use_property_decorate = True

            left = split.row()
            left.alignment = 'RIGHT'
            left.label(text=heading)

            right = split.row()
            right.alignment = 'LEFT'
            return right


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

        layout.prop(settings, 'reference_color', text='Reference')
        layout.prop(settings, 'retopo_color', text='Retopo')
        layout.prop(settings, 'wireframe_color', text='Wireframe')

        layout.separator()

        row = self.row_with_heading(layout, 'Displace')
        row.prop(settings, 'displace_visibility', text='')
        sub = row.row()
        sub.enabled = settings.wireframe_visibility
        sub.prop(settings, 'displace_strength', text='')

        row = self.row_with_heading(layout, 'Solidify')
        row.prop(settings, 'solidify_visibility', text='')
        sub = row.row()
        sub.enabled = settings.wireframe_visibility
        sub.prop(settings, 'solidify_thickness', text='')

        row = self.row_with_heading(layout, 'Wireframe')
        row.prop(settings, 'wireframe_visibility', text='')
        sub = row.row()
        sub.enabled = settings.wireframe_visibility
        sub.prop(settings, 'wireframe_thickness', text='')

        layout.separator()

        try:
            layout.prop(context.preferences.themes['Default'].view_3d, 'vertex', text='Vertex Color')
            layout.prop(context.preferences.themes['Default'].view_3d, 'vertex_size', text='Vertex Size')
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
