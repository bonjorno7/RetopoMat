from bpy.types import Context, Object, Panel, Theme, UILayout
from bpy.utils import register_class, unregister_class

from .ops import (AddReferenceMaterialOperator, AddRetopoMaterialsOperator, FlipNormalsOperator,
                  MoveModifiersToBottomOperator, RemoveMaterialsOperator)
from .props import RetopoMatSettings
from .utils import MaterialName, ModifierName, get_material, get_modifier


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
        layout.operator(AddRetopoMaterialsOperator.bl_idname)
        layout.operator(RemoveMaterialsOperator.bl_idname)


class SettingsPanel(RetopoMatPanel):
    bl_idname = 'RETOPOMAT_PT_settings'
    bl_label = 'Settings'
    bl_order = 2

    def draw(self, context: Context):
        layout = self.configure_layout().column()

        object: Object = context.active_object
        settings: RetopoMatSettings = context.scene.retopo_mat

        reference_material = get_material(object, MaterialName.REFERENCE)
        retopo_material = get_material(object, MaterialName.RETOPO)
        displace_modifier = get_modifier(object, ModifierName.DISPLACE)
        solidify_modifier = get_modifier(object, ModifierName.SOLIDIFY)
        wireframe_modifier = get_modifier(object, ModifierName.WIREFRAME)

        row = layout.row(align=True)
        row.enabled = (reference_material is not None)
        row.prop(settings, 'reference_color', text='Reference')
        icon = 'IMAGE_RGB_ALPHA' if settings.reference_blend else 'IMAGE_RGB'
        row.prop(settings, 'reference_blend', text='', icon=icon)

        row = layout.row(align=True)
        row.enabled = (retopo_material is not None)
        row.prop(settings, 'retopo_color', text='Retopo')
        icon = 'IMAGE_RGB_ALPHA' if settings.retopo_blend else 'IMAGE_RGB'
        row.prop(settings, 'retopo_blend', text='', icon=icon)

        layout.separator()

        row = layout.row(align=True)
        row.enabled = (displace_modifier is not None)
        row.prop(settings, 'displace_strength', text='Offset')
        icon = 'RESTRICT_VIEW_OFF' if settings.displace_visibility else 'RESTRICT_VIEW_ON'
        row.prop(settings, 'displace_visibility', text='', icon=icon)

        row = layout.row(align=True)
        row.enabled = (solidify_modifier is not None)
        row.prop(settings, 'solidify_thickness', text='Thickness')
        icon = 'RESTRICT_VIEW_OFF' if settings.solidify_visibility else 'RESTRICT_VIEW_ON'
        row.prop(settings, 'solidify_visibility', text='', icon=icon)

        row = layout.row(align=True)
        row.enabled = (wireframe_modifier is not None)
        row.prop(settings, 'wireframe_thickness', text='Wireframe')
        icon = 'RESTRICT_VIEW_OFF' if settings.wireframe_visibility else 'RESTRICT_VIEW_ON'
        row.prop(settings, 'wireframe_visibility', text='', icon=icon)

        theme: Theme = context.preferences.themes.get('Default')
        if theme is not None:
            layout.separator()

            row = layout.row(align=True)
            row.enabled = (context.mode == 'EDIT_MESH')
            row.prop(theme.view_3d, 'vertex_size', text='Vertex')


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
