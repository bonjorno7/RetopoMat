from pathlib import Path
from typing import TYPE_CHECKING

import bgl
import bmesh
import bpy
import gpu
import gpu_extras
from bpy.props import BoolProperty, BoolVectorProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import (Context, CorrectiveSmoothModifier, Event, NodesModifier, Object, Operator, ShrinkwrapModifier,
                       SpaceView3D)
from bpy.utils import register_class, unregister_class
from bpy_extras import view3d_utils

from .utils import (MaterialName, ModifierName, ShrinkwrapName, apply_shrinkwrap, clean_shrinkwrap, flip_normals,
                    get_material, get_mirror_modifier, get_modifier, remove_modifiers, row_with_heading, set_materials,
                    setup_shrinkwrap, sort_modifiers)

if TYPE_CHECKING:
    from .props import RetopoMatSettings


class AddReferenceMaterialOperator(Operator):
    bl_idname = 'retopomat.add_reference_material'
    bl_label = 'Add Reference Material'
    bl_description = '.\n'.join((
        'Add a reference material to the active object',
        'This removes your material slots and retopo modifiers',
    ))
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH') and (object.mode == 'OBJECT')

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        material = get_material(object, MaterialName.REFERENCE, create=True)
        set_materials(object, [material])
        remove_modifiers(object)

        self.report({'INFO'}, 'Added reference material')
        return {'FINISHED'}


class AddRetopoMaterialsOperator(Operator):
    bl_idname = 'retopomat.add_retopo_materials'
    bl_label = 'Add Retopo Materials'
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


class SortModifiersOperator(Operator):
    bl_idname = 'retopomat.sort_modifiers'
    bl_label = 'Sort Modifiers'
    bl_description = 'Move retopo modifiers to the bottom of the stack'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return any(get_modifier(object, name) for name in ModifierName)

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        sort_modifiers(object)

        self.report({'INFO'}, 'Sorted modifiers')
        return {'FINISHED'}


class MirrorModifierOperator(Operator):
    bl_idname = 'retopomat.mirror_modifier'
    bl_label = 'Mirror Modifier'
    bl_description = 'Add a mirror modifier to the top of the stack'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    use_axis: BoolVectorProperty(
        name='Mirror Axis',
        description='Enable axis mirror',
        default=(True, False, False),
        size=3,
    )

    use_bisect_axis: BoolVectorProperty(
        name='Bisect Axis',
        description='Cuts the mesh across the mirror plane',
        default=(True, False, False),
        size=3,
    )

    use_bisect_flip_axis: BoolVectorProperty(
        name='Bisect Flip Axis',
        description='Flips the direction of the slice',
        default=(False, False, False),
        size=3,
    )

    def _update_mirror_object(self, context: Context):
        object: Object = context.active_object
        mirror_object: Object = bpy.data.objects.get(self.mirror_object)

        # Don't accept invalid names and don't use self as mirror.
        if (mirror_object is None) or (mirror_object is object):
            self['mirror_object'] = ''

    mirror_object: StringProperty(
        name='Mirror Object',
        description='Object to use as mirror',
        update=_update_mirror_object,
        options={'SKIP_SAVE'},
    )

    use_clip: BoolProperty(
        name='Clipping',
        description='Prevent vertices from going through the mirror during transform',
        default=True,
    )

    use_mirror_merge: BoolProperty(
        name='Merge',
        description='Merge vertices within the merge threshold',
        default=True,
    )

    def draw(self, context: Context):
        layout = self.layout.column()
        layout.use_property_split = True
        layout.use_property_decorate = False

        row = row_with_heading(layout, heading='Axis', align=True)
        for index, axis in enumerate('XYZ'):
            row.prop(self, 'use_axis', index=index, text=axis, toggle=1)

        row = row_with_heading(layout, heading='Bisect', align=True)
        for index, axis in enumerate('XYZ'):
            row.prop(self, 'use_bisect_axis', index=index, text=axis, toggle=1)

        row = row_with_heading(layout, heading='Flip', align=True)
        for index, axis in enumerate('XYZ'):
            row.prop(self, 'use_bisect_flip_axis', index=index, text=axis, toggle=1)

        layout.separator()

        layout.prop_search(self, 'mirror_object', bpy.data, 'objects')
        layout.prop(self, 'use_clip')
        layout.prop(self, 'use_mirror_merge')

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH')

    def invoke(self, context: Context, event: Event) -> set:
        object: Object = context.active_object
        modifier = get_mirror_modifier(object)

        if modifier is not None:
            # Copy settings from the existing modifier.
            self.mirror_object = modifier.mirror_object.name if (modifier.mirror_object is not None) else ''
            for key in ('use_axis', 'use_bisect_axis', 'use_bisect_flip_axis', 'use_clip', 'use_mirror_merge'):
                setattr(self, key, getattr(modifier, key))

        else:
            # Use the reference object as default mirror object.
            settings: 'RetopoMatSettings' = context.scene.retopomat
            mirror_object = settings.reference_object
            if (mirror_object is not None) and (mirror_object is not object):
                self.mirror_object = mirror_object.name

            # Report here because in execute it would spam.
            self.report({'INFO'}, 'Added mirror modifier')

        return self.execute(context)

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        modifier = get_mirror_modifier(object, create=True)

        # Copy our settings to the modifier.
        modifier.mirror_object = bpy.data.objects.get(self.mirror_object)
        for key in ('use_axis', 'use_bisect_axis', 'use_bisect_flip_axis', 'use_clip', 'use_mirror_merge'):
            setattr(modifier, key, getattr(self, key))

        return {'FINISHED'}


class QuickShrinkwrapOperator(Operator):
    bl_idname = 'retopomat.quick_shrinkwrap'
    bl_label = 'Quick Shrinkwrap'
    bl_description = 'Use shrinkwrap and corrective smooth modifiers'
    bl_options = {'INTERNAL', 'UNDO'}  # Not using REGISTER because I don't want a redo panel.

    def _update_target(self, context: Context):
        object: Object = context.active_object
        target = bpy.data.objects.get(self.target)

        # Prevent the shrinkwrap from targeting itself.
        if target is object:
            target = None

        # Clear the field if the target object doesn't exist.
        if target is None:
            self['target'] = ''

        # Set the target on the first shrinkwrap modifier.
        shrinkwrap_tangent: ShrinkwrapModifier = object.modifiers.get(ShrinkwrapName.SHRINKWRAP_TANGENT)
        if shrinkwrap_tangent is not None:
            shrinkwrap_tangent.target = target

        # Set the target on the second shrinkwrap modifier.
        shrinkwrap_nearest: ShrinkwrapModifier = object.modifiers.get(ShrinkwrapName.SHRINKWRAP_NEAREST)
        if shrinkwrap_nearest is not None:
            shrinkwrap_nearest.target = target

    target: StringProperty(
        name='Target',
        description='Target for both shrinkwrap modifiers',
        update=_update_target,
        options={'SKIP_SAVE'},
    )

    def _update_offset_tangent(self, context: Context):
        object: Object = context.active_object
        shrinkwrap_tangent: ShrinkwrapModifier = object.modifiers.get(ShrinkwrapName.SHRINKWRAP_TANGENT)
        if shrinkwrap_tangent is not None:
            shrinkwrap_tangent.offset = self.offset_tangent

    offset_tangent: FloatProperty(
        name='Offset Before',
        description='Offset for the first shrinkwrap modifier',
        default=0.0,
        soft_min=-100.0,
        soft_max=100.0,
        step=0.01,
        unit='LENGTH',
        update=_update_offset_tangent,
        options={'SKIP_SAVE'},
    )

    def _update_offset_nearest(self, context: Context):
        object: Object = context.active_object
        shrinkwrap_nearest: ShrinkwrapModifier = object.modifiers.get(ShrinkwrapName.SHRINKWRAP_NEAREST)
        if shrinkwrap_nearest is not None:
            shrinkwrap_nearest.offset = self.offset_nearest

    offset_nearest: FloatProperty(
        name='Offset After',
        description='Offset for the second shrinkwrap modifier',
        default=0.0,
        soft_min=-100.0,
        soft_max=100.0,
        step=0.01,
        unit='LENGTH',
        update=_update_offset_nearest,
        options={'SKIP_SAVE'},
    )

    def _update_factor(self, context: Context):
        object: Object = context.active_object
        corrective_smooth: CorrectiveSmoothModifier = object.modifiers.get(ShrinkwrapName.CORRECTIVE_SMOOTH)
        if corrective_smooth is not None:
            corrective_smooth.factor = self.factor

    factor: FloatProperty(
        name='Factor',
        description='Factor for the corrective smooth modifier',
        default=0.5,
        soft_min=0.0,
        soft_max=1.0,
        step=0.01,
        subtype='FACTOR',
        update=_update_factor,
        options={'SKIP_SAVE'},
    )

    def _update_iterations(self, context: Context):
        object: Object = context.active_object
        corrective_smooth: CorrectiveSmoothModifier = object.modifiers.get(ShrinkwrapName.CORRECTIVE_SMOOTH)
        if corrective_smooth is not None:
            corrective_smooth.iterations = self.iterations

    iterations: IntProperty(
        name='Repeat',
        description='Iterations for the corrective smooth modifier',
        default=5,
        soft_min=0,
        soft_max=200,
        update=_update_iterations,
        options={'SKIP_SAVE'},
    )

    def _update_scale(self, context: Context):
        object: Object = context.active_object
        smooth_modifier: CorrectiveSmoothModifier = object.modifiers.get(ShrinkwrapName.CORRECTIVE_SMOOTH)
        if smooth_modifier is not None:
            smooth_modifier.scale = self.scale

    scale: FloatProperty(
        name='Scale',
        description='Scale for the corrective smooth modifier',
        default=1.0,
        soft_min=0.0,
        soft_max=2.0,
        step=0.01,
        subtype='FACTOR',
        update=_update_scale,
        options={'SKIP_SAVE'},
    )

    def draw(self, context: Context):
        layout = self.layout.column()
        layout.use_property_split = True
        layout.use_property_decorate = False

        sub = layout.column()
        sub.alert = (not self.target)
        sub.prop_search(self, 'target', search_data=bpy.data, search_property='objects')

        sub = layout.column()
        sub.enabled = bool(self.target)
        sub.prop(self, 'offset_tangent')
        sub.prop(self, 'offset_nearest')

        layout.separator()

        layout.prop(self, 'factor')
        layout.prop(self, 'iterations')
        layout.prop(self, 'scale')

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH')

    def invoke(self, context: 'Context', event: Event) -> set:
        object: Object = context.active_object
        setup_shrinkwrap(object)

        # Use the reference object as default shrinkwrap target.
        settings: 'RetopoMatSettings' = context.scene.retopomat
        reference_object = settings.reference_object
        if (reference_object is not None) and (reference_object is not object):
            self.target = reference_object.name

        # Use a props dialog so the user can tweak values, and hit OK to apply the modifiers.
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        apply_shrinkwrap(object)

        self.report({'INFO'}, 'Applied modifiers')
        return {'FINISHED'}

    def cancel(self, context: Context):
        object: Object = bpy.context.active_object
        clean_shrinkwrap(object)


class FlipNormalsOperator(Operator):
    bl_idname = 'retopomat.flip_normals'
    bl_label = 'Flip Normals'
    bl_description = 'Flip normals of selected faces in your mesh'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH')

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        flip_normals(object)

        self.report({'INFO'}, 'Flipped normals')
        return {'FINISHED'}


class PolyStripOperator(Operator):
    bl_idname = 'retopomat.poly_strip'
    bl_label = 'Poly Strip'
    bl_description = 'Draw a strip of polygons'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    cross: IntProperty(
        name='Cross',
        description='Polygons in the U direction',
        default=8,
        min=1,
        soft_max=100,
    )

    follow: IntProperty(
        name='Follow',
        description='Polygons in the V direction',
        default=1,
        min=1,
        soft_max=100,
    )

    width: FloatProperty(
        name='Width',
        description='Width of the faces',
        default=0.1,
        min=0.0,
        soft_max=100.0,
        step=1,
    )

    @classmethod
    def poll(cls, context: Context) -> bool:
        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH') and (object.mode == 'EDIT')

    def invoke(self, context: Context, event: Event) -> set:
        self.object = None
        self.points = []

        self.draw_handler = SpaceView3D.draw_handler_add(self.draw_callback, (context,), 'WINDOW', 'POST_VIEW')
        self.lines = []

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context: Context, event: Event) -> set:
        context.window.cursor_modal_set('PAINT_BRUSH')

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            coords = event.mouse_region_x, event.mouse_region_y
            ray_origin = view3d_utils.region_2d_to_origin_3d(context.region, context.region_data, coords)
            view_vector = view3d_utils.region_2d_to_vector_3d(context.region, context.region_data, coords)

            context.active_object.hide_set(True)
            depsgraph = context.evaluated_depsgraph_get()
            results = context.scene.ray_cast(depsgraph, ray_origin, view_vector)
            context.active_object.hide_set(False)

            result, _, _, _, object, _ = results
            if not result:
                return {'RUNNING_MODAL'}

            self.object: Object = object
            return {'RUNNING_MODAL'}

        if event.type in ('RIGHTMOUSE', 'ESC'):
            context.window.cursor_modal_restore()
            return {'CANCELLED'}

        if self.object:
            if event.type == 'MOUSEMOVE':
                coords = event.mouse_region_x, event.mouse_region_y
                ray_origin = view3d_utils.region_2d_to_origin_3d(context.region, context.region_data, coords)
                view_vector = view3d_utils.region_2d_to_vector_3d(context.region, context.region_data, coords)
                ray_target = ray_origin + view_vector

                matrix_inv = self.object.matrix_world.inverted_safe()
                ray_origin_obj = matrix_inv @ ray_origin
                ray_target_obj = matrix_inv @ ray_target
                ray_direction_obj = ray_target_obj - ray_origin_obj

                depsgraph = context.evaluated_depsgraph_get()
                results = self.object.ray_cast(ray_origin_obj, ray_direction_obj, depsgraph=depsgraph)

                result, location, _, _ = results
                if not result:
                    return {'RUNNING_MODAL'}

                self.points.append(self.object.matrix_world @ location)
                if len(self.points) > 1:
                    self.lines.extend(self.points[-2:])

                context.area.tag_redraw()
                return {'RUNNING_MODAL'}

            if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                self.draw_handler = SpaceView3D.draw_handler_remove(self.draw_handler, 'WINDOW')
                context.window.cursor_modal_restore()

                self.report({'INFO'}, 'Added poly strip')
                return self.execute(context)

        return {'PASS_THROUGH'}

    def execute(self, context: Context) -> set:
        curve_data = bpy.data.curves.new('Poly Strip', 'CURVE')
        curve_object = bpy.data.objects.new('Poly Strip', curve_data)
        context.scene.collection.objects.link(curve_object)

        spline = curve_data.splines.new('POLY')
        spline.points.add(len(self.points) - 1)
        for index in range(len(self.points)):
            spline.points[index].co[:3] = self.points[index][:3]

        if 'Poly Strip' not in bpy.data.node_groups:
            path = Path(__file__).parent.joinpath('poly_strip.blend').as_posix()
            with bpy.data.libraries.load(path) as (data_from, data_to):
                data_to.node_groups.append('Poly Strip')

        node_group = bpy.data.node_groups['Poly Strip']
        modifier: NodesModifier = curve_object.modifiers.new('Poly Strip', 'NODES')
        modifier.node_group = node_group

        values = [self.object, self.cross, self.follow, self.width]
        for key in modifier.keys():
            if key.startswith('Input_') and key.endswith(tuple('0123456789')):
                modifier[key] = values.pop(0)

        depsgraph = context.evaluated_depsgraph_get()
        curve_evaluated = bpy.data.meshes.new_from_object(
            object=curve_object.evaluated_get(depsgraph),
            preserve_all_data_layers=True,
            depsgraph=depsgraph,
        )

        matrix_inv = context.active_object.matrix_world.inverted_safe()
        curve_evaluated.transform(matrix_inv)

        bm = bmesh.from_edit_mesh(context.active_object.data)
        bm.from_mesh(curve_evaluated)
        bmesh.update_edit_mesh(context.active_object.data)

        bpy.data.meshes.remove(curve_evaluated)
        bpy.data.objects.remove(curve_object)
        bpy.data.curves.remove(curve_data)

        if not node_group.users:
            bpy.data.node_groups.remove(node_group)

        return {'FINISHED'}

    def draw_callback(self, context: Context):
        scale = context.preferences.view.ui_scale

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
        bgl.glLineWidth(2 * scale)

        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        shader.bind()
        shader.uniform_float('color', (1.0, 1.0, 1.0, 1.0))

        batch = gpu_extras.batch.batch_for_shader(shader, 'LINES', {'pos': self.lines})
        batch.draw(shader)

        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_LINE_SMOOTH)
        bgl.glDisable(bgl.GL_BLEND)


classes = (
    AddReferenceMaterialOperator,
    AddRetopoMaterialsOperator,
    RemoveMaterialsOperator,
    SortModifiersOperator,
    MirrorModifierOperator,
    QuickShrinkwrapOperator,
    FlipNormalsOperator,
    PolyStripOperator,
)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
