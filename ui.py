import bpy
from bpy.types import Context, Panel, ThemeView3D, UILayout, View3DShading
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

        layout.prop_search(
            settings,
            'reference_object_name',
            search_data=bpy.data,
            search_property='objects',
            text='Reference',
        )

        layout.prop_search(
            settings,
            'retopo_object_name',
            search_data=bpy.data,
            search_property='objects',
            text='Retopo',
        )

        layout.separator()

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

        if self.should_draw_world(context):
            layout.separator()
            self.draw_world(context, layout)

        if self.should_draw_edit(context):
            layout.separator()
            self.draw_edit(context, layout)

    def should_draw_world(self, context: Context) -> bool:
        shading: View3DShading = context.space_data.shading

        if shading.type == 'SOLID' and shading.light == 'STUDIO':
            return True
        elif shading.type == 'MATERIAL' and not shading.use_scene_world:
            return True
        elif shading.type == 'RENDERED' and not shading.use_scene_world_render:
            return True

        return False

    def draw_world(self, context: Context, layout: UILayout):
        shading: View3DShading = context.space_data.shading

        row = layout.row(align=True)
        row.prop(shading, 'studiolight_rotate_z', text='World Rotation')
        prop = 'use_world_space_lighting' if shading.type == 'SOLID' else 'use_studiolight_view_rotation'
        row.prop(shading, prop, text='', icon='WORLD')

        row = layout.row(align=True)
        row.prop(shading, 'studiolight_intensity', text='World Strength')
        row.prop(shading, 'studio_light', text='', icon_only=True)

    def should_draw_edit(self, context: Context):
        if context.mode != 'EDIT_MESH':
            return False
        elif 'Default' not in context.preferences.themes:
            return False

        return True

    def draw_edit(self, context: Context, layout: UILayout) -> bool:
        view_3d: ThemeView3D = context.preferences.themes['Default'].view_3d
        layout.prop(view_3d, 'vertex_size', text='Vertex Size')


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
