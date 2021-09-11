from enum import Enum
from typing import TYPE_CHECKING, List, Tuple, Union

import bmesh
import bpy
from bmesh.types import BMFace
from bpy.types import (Context, CorrectiveSmoothModifier, Depsgraph, DisplaceModifier, Material, Mesh, Modifier, Object,
                       Scene, ShaderNode, ShaderNodeBsdfPrincipled, ShaderNodeEmission, ShaderNodeMixShader,
                       ShaderNodeNewGeometry, ShaderNodeOutputMaterial, ShrinkwrapModifier, SolidifyModifier,
                       WireframeModifier)

if TYPE_CHECKING:
    from .props import RetopoMatSettings


class MaterialName(Enum):
    REFERENCE = 'RetopoMat Reference'
    RETOPO = 'RetopoMat Retopo'
    WIREFRAME = 'RetopoMat Wireframe'


class ModifierName(Enum):
    DISPLACE = 'RetopoMat Displace'
    SOLIDIFY = 'RetopoMat Solidify'
    WIREFRAME = 'RetopoMat Wireframe'


class ShrinkwrapName:
    SHRINKWRAP_TANGENT = 'RetopoMat Shrinkwrap Tangent'
    CORRECTIVE_SMOOTH = 'RetopoMat Corrective Smooth'
    SHRINKWRAP_NEAREST = 'RetopoMat Shrinkwrap Nearest'
    VERTEX_GROUP = 'RetopoMat Quick Shrinkwrap'

    @classmethod
    def modifiers(cls) -> List[str]:
        return (cls.SHRINKWRAP_TANGENT, cls.CORRECTIVE_SMOOTH, cls.SHRINKWRAP_NEAREST)


def check_context(context: Context) -> bool:
    '''Check whether the current context has write access to ID properties.'''
    try:
        context.scene.name = context.scene.name
    except:
        return False
    else:
        return True


def get_material(object: Union[Object, None], name: MaterialName, create: bool = False) -> Union[Material, None]:
    '''Get a material with the given name from the given mesh object, create it if necessary.'''
    material = _find_material(object, name)

    if material is None:
        if create:
            material = bpy.data.materials.new(name.value)

        else:  # If the material isn't found or created, see if it's on the last reference or retopo object.
            settings: 'RetopoMatSettings' = bpy.context.scene.retopomat

            if name is MaterialName.REFERENCE:
                material = _find_material(settings.reference_object, name)
            elif name in (MaterialName.RETOPO, MaterialName.WIREFRAME):
                material = _find_material(settings.retopo_object, name)

    if material is not None:
        if create:  # If create is used, always setup the material, even if it's already valid.
            setup_material(material, name)

        elif not check_material(material, name):
            if check_context(bpy.context):  # The material is not valid, but we can fix it here.
                setup_material(material, name)
            else:  # The material is not valid and we can't safely fix it here.
                material = None

    return material


def _find_material(object: Union[Object, None], name: MaterialName) -> Union[Material, None]:
    '''Try to find the material with the given name on the given mesh object.'''
    if (object is not None) and (object.type == 'MESH'):
        data: Mesh = object.data

        for material in data.materials:
            material: Material

            if material.name.startswith(name.value):
                return material

    return None


def check_material(material: Material, name: MaterialName) -> bool:
    '''Check whether the given material is valid.'''
    if name is MaterialName.REFERENCE:
        return _check_reference_material(material)
    elif name is MaterialName.RETOPO:
        return _check_retopo_material(material)
    elif name is MaterialName.WIREFRAME:
        return _check_wireframe_material(material)


def _check_reference_material(material: Material) -> bool:
    '''Check whether the reference material is valid.'''
    if not material.use_nodes:
        return False
    elif 'Principled BSDF' not in material.node_tree.nodes:
        return False

    return True


def _check_retopo_material(material: Material) -> bool:
    '''Check whether the retopo material is valid.'''
    if not material.use_nodes:
        return False
    elif 'Principled BSDF' not in material.node_tree.nodes:
        return False

    return True


def _check_wireframe_material(material: Material) -> bool:
    '''Check whether the wireframe material is valid.'''
    if not material.use_nodes:
        return False

    return True


def setup_material(material: Material, name: MaterialName):
    '''Setup the given material.'''
    if name is MaterialName.REFERENCE:
        _setup_reference_material(material)
    elif name is MaterialName.RETOPO:
        _setup_retopo_material(material)
    elif name is MaterialName.WIREFRAME:
        _setup_wireframe_material(material)


def _setup_reference_material(material: Material):
    '''Setup the reference material.'''
    settings: 'RetopoMatSettings' = bpy.context.scene.retopomat
    blend: bool = settings.get_internal('reference_blend')
    color: Tuple[float, float, float, float] = settings.get_internal('reference_color')

    material.blend_method = 'BLEND' if blend else 'OPAQUE'
    material.shadow_method = 'NONE'
    material.use_backface_culling = False
    material.show_transparent_back = False
    material.use_nodes = True
    material.node_tree.nodes.clear()

    output_node = _add_node(material, ShaderNodeOutputMaterial, (0, 0))
    principled_node = _add_node(material, ShaderNodeBsdfPrincipled, (-300, 0))

    _set_defaults(principled_node, {
        'Base Color': color,
        'Metallic': 1.0,
        'Roughness': 0.7,
        'Alpha': color[3],
    })

    material.node_tree.links.new(output_node.inputs['Surface'], principled_node.outputs['BSDF'])


def _setup_retopo_material(material: Material):
    '''Setup the retopo material.'''
    settings: 'RetopoMatSettings' = bpy.context.scene.retopomat
    blend: bool = settings.get_internal('retopo_blend')
    color: Tuple[float, float, float, float] = settings.get_internal('retopo_color')

    material.blend_method = 'BLEND' if blend else 'OPAQUE'
    material.shadow_method = 'NONE'
    material.use_backface_culling = False
    material.show_transparent_back = False
    material.use_nodes = True
    material.node_tree.nodes.clear()

    output_node = _add_node(material, ShaderNodeOutputMaterial, (0, 0))
    mix_shader_node = _add_node(material, ShaderNodeMixShader, (-200, 0))
    geometry_node = _add_node(material, ShaderNodeNewGeometry, (-200, 300))
    principled_node = _add_node(material, ShaderNodeBsdfPrincipled, (-500, 0))
    emission_node = _add_node(material, ShaderNodeEmission, (-200, -200))

    _set_defaults(principled_node, {
        'Base Color': color,
        'Metallic': 0.0,
        'Roughness': 0.3,
        'Alpha': color[3],
    })

    _set_defaults(emission_node, {
        'Color': (0.0, 0.0, 0.0, 1.0),
    })

    # Using nodes to make back faces easier to spot. Using indices for mix shader inputs because of name overlap.
    material.node_tree.links.new(output_node.inputs['Surface'], mix_shader_node.outputs['Shader'])
    material.node_tree.links.new(mix_shader_node.inputs[0], geometry_node.outputs['Backfacing'])
    material.node_tree.links.new(mix_shader_node.inputs[1], principled_node.outputs['BSDF'])
    material.node_tree.links.new(mix_shader_node.inputs[2], emission_node.outputs['Emission'])


def _setup_wireframe_material(material: Material):
    '''Setup the wireframe material.'''
    settings: 'RetopoMatSettings' = bpy.context.scene.retopomat
    blend: bool = settings.get_internal('retopo_blend')

    material.blend_method = 'BLEND' if blend else 'OPAQUE'
    material.shadow_method = 'NONE'
    material.use_backface_culling = False
    material.show_transparent_back = False
    material.use_nodes = True
    material.node_tree.nodes.clear()

    output_node = _add_node(material, ShaderNodeOutputMaterial, (0, 0))
    principled_node = _add_node(material, ShaderNodeBsdfPrincipled, (-300, 0))

    _set_defaults(principled_node, {
        'Base Color': (0.0, 0.0, 0.0, 1.0),
        'Specular': 0.0,
        'Emission': (0.0, 0.0, 0.0, 1.0),
        'Alpha': 1.0,
    })

    material.node_tree.links.new(output_node.inputs['Surface'], principled_node.outputs['BSDF'])


def _add_node(material: Material, node_type: type, location: Tuple[float, float]) -> ShaderNode:
    '''Create a node of the given type at the given position.'''
    node = material.node_tree.nodes.new(node_type.__name__)
    node.location = location
    node.select = False
    return node


def _set_defaults(node: ShaderNode, defaults: dict):
    '''Set default input values based on the given dictionary.'''
    for key, value in defaults.items():
        node.inputs[key].default_value = value


def set_materials(object: Object, materials: List[Material]):
    '''Clear materials, then add the given materials.'''
    if (object is not None) and (object.type == 'MESH'):
        data: Mesh = object.data

        data.materials.clear()

        for material in materials:
            data.materials.append(material)


def get_modifier(object: Union[Object, None], name: ModifierName, create: bool = False) -> Union[Modifier, None]:
    '''Get a modifier with the given name from the given mesh object, create it if necessary.'''
    modifier = _find_modifier(object, name)

    if modifier is None:
        if create:
            modifier = object.modifiers.new(name.value, name.name)

        else:  # If the modifier isn't found or created, see if it's on the last retopo object.
            settings: 'RetopoMatSettings' = bpy.context.scene.retopomat
            modifier = _find_modifier(settings.retopo_object, name)

    if (modifier is not None) and create:  # If create is used, always setup the modifier, even if it already existed.
        setup_modifier(modifier, name)

    return modifier


def _find_modifier(object: Union[Object, None], name: ModifierName) -> Union[Modifier, None]:
    '''Try to find the modifier with the given name on the given mesh object.'''
    if (object is not None) and (object.type == 'MESH'):
        if name.value in object.modifiers:
            return object.modifiers[name.value]

    return None


def setup_modifier(modifier: Modifier, name: ModifierName):
    '''Setup the given modifier.'''
    if name == ModifierName.DISPLACE:
        _setup_displace_modifier(modifier)
    elif name == ModifierName.SOLIDIFY:
        _setup_solidify_modifier(modifier)
    elif name == ModifierName.WIREFRAME:
        _setup_wireframe_modifier(modifier)


def _setup_displace_modifier(modifier: DisplaceModifier):
    '''Setup the displace modifier.'''
    modifier.show_in_editmode = True
    modifier.show_on_cage = True
    modifier.direction = 'NORMAL'
    modifier.mid_level = 0.0

    settings: 'RetopoMatSettings' = bpy.context.scene.retopomat
    modifier.show_viewport = settings.get_internal('displace_visibility')
    modifier.strength = settings.get_internal('displace_strength')


def _setup_solidify_modifier(modifier: SolidifyModifier):
    '''Setup the solidify modifier.'''
    modifier.show_in_editmode = True
    modifier.show_on_cage = True
    modifier.offset = 1.0
    modifier.use_even_offset = False
    modifier.use_rim = True
    modifier.use_rim_only = True
    modifier.material_offset = 1
    modifier.material_offset_rim = 1

    settings: 'RetopoMatSettings' = bpy.context.scene.retopomat
    modifier.show_viewport = settings.get_internal('solidify_visibility')
    modifier.thickness = settings.get_internal('solidify_thickness')


def _setup_wireframe_modifier(modifier: WireframeModifier):
    '''Setup the wireframe modifier.'''
    modifier.show_in_editmode = True
    modifier.show_on_cage = False
    modifier.offset = 0.0
    modifier.use_boundary = True
    modifier.use_replace = False
    modifier.use_even_offset = False
    modifier.use_relative_offset = False
    modifier.use_crease = False
    modifier.material_offset = 1

    settings: 'RetopoMatSettings' = bpy.context.scene.retopomat
    modifier.show_viewport = settings.get_internal('wireframe_visibility')
    modifier.thickness = settings.get_internal('wireframe_thickness')


def remove_modifiers(object: Object):
    '''Remove retopo modifiers from the given object.'''
    for name in ModifierName:
        modifier = _find_modifier(object, name)

        if modifier is not None:
            object.modifiers.remove(modifier)


def sort_modifiers(object: Object):
    '''Move retopo modifiers to the bottom of the stack.'''
    index = len(object.modifiers) - 1

    for name in ModifierName:
        modifier = _find_modifier(object, name)

        if modifier is not None:
            _move_modifier(object, modifier, index)


def _move_modifier(object: Object, modifier: Modifier, index: int):
    '''Move the given modifier to the given index.'''
    try:  # Newer versions of Blender can use modifier_move_to_index.
        bpy.ops.object.modifier_move_to_index(modifier=modifier.name, index=index)

    except:  # Older versions of Blender have to use modifier_move_down/up.
        current = object.modifiers.find(modifier.name)

        if index > current:
            for _ in range(index - current):
                bpy.ops.object.modifier_move_down(modifier=modifier.name)

        elif current > index:
            for _ in range(current - index):
                bpy.ops.object.modifier_move_up(modifier=modifier.name)


def setup_shrinkwrap(object: Object):
    '''Setup shrinkwrap and corrective smooth modifiers.'''
    # Remove the vertex group if it's left over from last time.
    if ShrinkwrapName.VERTEX_GROUP in object.vertex_groups:
        vertex_group = object.vertex_groups[ShrinkwrapName.VERTEX_GROUP]
        object.vertex_groups.remove(vertex_group)

    # Use selected vertices if we are in edit mode.
    if object.mode == 'EDIT':
        bpy.ops.object.vertex_group_assign_new()
        vertex_group = object.vertex_groups[-1]
        vertex_group.name = ShrinkwrapName.VERTEX_GROUP

    # Setup the first shrinkwrap modifier.
    shrinkwrap_tangent_name = ShrinkwrapName.SHRINKWRAP_TANGENT
    shrinkwrap_tangent: ShrinkwrapModifier = object.modifiers.new(shrinkwrap_tangent_name, 'SHRINKWRAP')
    shrinkwrap_tangent.show_viewport = shrinkwrap_tangent.show_in_editmode = shrinkwrap_tangent.show_on_cage = True
    shrinkwrap_tangent.wrap_method = 'TARGET_PROJECT'
    shrinkwrap_tangent.wrap_mode = 'ABOVE_SURFACE'
    shrinkwrap_tangent.vertex_group = ShrinkwrapName.VERTEX_GROUP

    # Setup the corrective smooth modifier.
    corrective_smooth_name = ShrinkwrapName.CORRECTIVE_SMOOTH
    corrective_smooth: CorrectiveSmoothModifier = object.modifiers.new(corrective_smooth_name, 'CORRECTIVE_SMOOTH')
    corrective_smooth.show_viewport = corrective_smooth.show_in_editmode = corrective_smooth.show_on_cage = True
    corrective_smooth.vertex_group = ShrinkwrapName.VERTEX_GROUP

    # Setup the second shrinkwrap modifier.
    shrinkwrap_neartest_name = ShrinkwrapName.SHRINKWRAP_NEAREST
    shrinkwrap_neartest: ShrinkwrapModifier = object.modifiers.new(shrinkwrap_neartest_name, 'SHRINKWRAP')
    shrinkwrap_neartest.show_viewport = shrinkwrap_neartest.show_in_editmode = shrinkwrap_neartest.show_on_cage = True
    shrinkwrap_neartest.wrap_method = 'NEAREST_SURFACEPOINT'
    shrinkwrap_neartest.wrap_mode = 'ABOVE_SURFACE'
    shrinkwrap_neartest.vertex_group = ShrinkwrapName.VERTEX_GROUP

    # Move our modifiers to the top of the stack.
    _move_modifier(object, shrinkwrap_tangent, 0)
    _move_modifier(object, corrective_smooth, 1)
    _move_modifier(object, shrinkwrap_neartest, 2)


def apply_shrinkwrap(object: Object):
    '''Apply shrinkwrap and corrective smooth modifiers.'''
    # Switch to object mode if we are not already.
    object_mode = object.mode
    if object_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Disable the original modifiers.
    original_modifiers: List[Modifier] = []
    for modifier in object.modifiers[3:]:
        modifier: Modifier

        if modifier.show_viewport:
            modifier.show_viewport = False
            original_modifiers.append(modifier)

    # Get an up to date dependency graph.
    bpy.context.view_layer.update()
    depsgraph = bpy.context.view_layer.depsgraph

    # Apply our modifiers with bmesh.
    bm = bmesh.new()
    bm.from_object(object, depsgraph)
    bm.to_mesh(object.data)
    bm.free()

    # Remove our modifiers.
    for modifier_name in ShrinkwrapName.modifiers():
        if modifier_name in object.modifiers:
            modifier = object.modifiers[modifier_name]
            object.modifiers.remove(modifier)

    # Remove the vertex group if we made one.
    if ShrinkwrapName.VERTEX_GROUP in object.vertex_groups:
        vertex_group = object.vertex_groups[ShrinkwrapName.VERTEX_GROUP]
        object.vertex_groups.remove(vertex_group)

    # Enable the modifiers we disabled.
    for modifier in original_modifiers:
        modifier.show_viewport = True

    # Switch back to the mode we had before.
    if object_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode=object_mode)


def clean_shrinkwrap(object: Object):
    '''Remove shrinkwrap and corrective smooth modifiers.'''
    for modifier_name in ShrinkwrapName.modifiers():
        if modifier_name in object.modifiers:
            modifier = object.modifiers[modifier_name]
            object.modifiers.remove(modifier)

    if ShrinkwrapName.VERTEX_GROUP in object.vertex_groups:
        vertex_group = object.vertex_groups[ShrinkwrapName.VERTEX_GROUP]
        object.vertex_groups.remove(vertex_group)


def flip_normals(object: Object):
    '''Flip normals of selected faces on the given mesh object.'''
    data: Mesh = object.data

    if object.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(data)

        faces: List[BMFace] = bm.faces
        selected = [face for face in faces if face.select]
        selected = selected if selected else faces

        for face in selected:
            face.normal_flip()

        bmesh.update_edit_mesh(data)

    else:
        bm = bmesh.new(use_operators=False)
        bm.from_mesh(data)

        faces: List[BMFace] = bm.faces

        for face in faces:
            face.normal_flip()

        bm.to_mesh(data)
        data.update()


@bpy.app.handlers.persistent
def update_handler(scene: Scene, depsgraph: Depsgraph):
    object: Object = depsgraph.view_layer.objects.active

    # Update the stored reference or retopo object with the active mesh object.
    if (object is not None) and (object.type == 'MESH'):
        settings: 'RetopoMatSettings' = scene.retopomat

        # If an object has the reference material, it is a reference object.
        if _find_material(object, MaterialName.REFERENCE):
            settings.reference_object = object

        # If an object has any of the retopo materials or modifiers, it is a retopo object.
        elif any(_find_material(object, name) for name in (MaterialName.RETOPO, MaterialName.WIREFRAME)):
            settings.retopo_object = object
        elif any(_find_modifier(object, name) for name in ModifierName):
            settings.retopo_object = object


def register():
    bpy.app.handlers.depsgraph_update_post.append(update_handler)


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(update_handler)
