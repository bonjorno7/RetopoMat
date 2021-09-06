from enum import Enum
from typing import TYPE_CHECKING, List, Tuple, Union

import bmesh
import bpy
from bmesh.types import BMFace
from bpy.types import (DisplaceModifier, Material, Mesh, Modifier, Object, ShaderNode, ShaderNodeBsdfPrincipled,
                       ShaderNodeEmission, ShaderNodeInvert, ShaderNodeNewGeometry, ShaderNodeOutputMaterial,
                       SolidifyModifier, WireframeModifier)

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


def get_material(object: Union[Object, None], name: MaterialName, create: bool = False) -> Union[Material, None]:
    '''Get a material with the given name from the given mesh object, create it if necessary.'''
    material = _find_material(object, name)

    if material is None:
        if create:
            material = bpy.data.materials.new(name.value)
        else:
            return None

    if name is MaterialName.REFERENCE:
        if not _check_reference_material(material):
            _setup_reference_material(material)

    elif name is MaterialName.RETOPO:
        if not _check_retopo_material(material):
            _setup_retopo_material(material)

    elif name is MaterialName.WIREFRAME:
        if not _check_wireframe_material(material):
            _setup_wireframe_material(material)

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


def _check_reference_material(material: Material) -> bool:
    '''Check whether the reference material is valid.'''
    if not material.use_nodes:
        return False

    if 'Principled BSDF' not in material.node_tree.nodes:
        return False

    return True


def _check_retopo_material(material: Material) -> bool:
    '''Check whether the retopo material is valid.'''
    if not material.use_nodes:
        return False

    if 'Principled BSDF' not in material.node_tree.nodes:
        return False

    return True


def _check_wireframe_material(material: Material) -> bool:
    '''Check whether the wireframe material is valid.'''
    if not material.use_nodes:
        return False

    if 'Emission' not in material.node_tree.nodes:
        return False

    return True


def _setup_reference_material(material: Material):
    '''Setup the reference material.'''
    material.blend_method = 'BLEND'
    material.shadow_method = 'NONE'

    material.use_backface_culling = False
    material.show_transparent_back = False

    material.use_nodes = True
    material.node_tree.nodes.clear()

    output_node = _add_node(material, ShaderNodeOutputMaterial, (0, 0))
    principled_node = _add_node(material, ShaderNodeBsdfPrincipled, (-300, 0))

    settings: 'RetopoMatSettings' = bpy.context.scene.retopo_mat
    color: Tuple[float, float, float, float] = settings.get_internal('reference_color')
    _set_defaults(principled_node, {'Base Color': color, 'Alpha': color[3], 'Roughness': 0.7, 'Metallic': 1.0})

    material.node_tree.links.new(output_node.inputs['Surface'], principled_node.outputs['BSDF'])


def _setup_retopo_material(material: Material):
    '''Setup the retopo material.'''
    material.blend_method = 'OPAQUE'
    material.shadow_method = 'NONE'

    material.use_backface_culling = False
    material.show_transparent_back = False

    material.use_nodes = True
    material.node_tree.nodes.clear()

    output_node = _add_node(material, ShaderNodeOutputMaterial, (0, 0))
    principled_node = _add_node(material, ShaderNodeBsdfPrincipled, (-300, 0))
    invert_node = _add_node(material, ShaderNodeInvert, (-500, 0))
    geometry_node = _add_node(material, ShaderNodeNewGeometry, (-700, 0))

    settings: 'RetopoMatSettings' = bpy.context.scene.retopo_mat
    color: Tuple[float, float, float, float] = settings.get_internal('retopo_color')
    _set_defaults(principled_node, {'Base Color': color, 'Roughness': 0.3, 'Metallic': 0.0})

    material.node_tree.links.new(output_node.inputs['Surface'], principled_node.outputs['BSDF'])
    material.node_tree.links.new(principled_node.inputs['Alpha'], invert_node.outputs['Color'])
    material.node_tree.links.new(invert_node.inputs['Color'], geometry_node.outputs['Backfacing'])


def _setup_wireframe_material(material: Material):
    '''Setup the wireframe material.'''
    material.blend_method = 'OPAQUE'
    material.shadow_method = 'NONE'

    material.use_backface_culling = False
    material.show_transparent_back = False

    material.use_nodes = True
    material.node_tree.nodes.clear()

    output_node = _add_node(material, ShaderNodeOutputMaterial, (0, 0))
    emission_node = _add_node(material, ShaderNodeEmission, (-200, 0))

    settings: 'RetopoMatSettings' = bpy.context.scene.retopo_mat
    color: Tuple[float, float, float, float] = settings.get_internal('wireframe_color')
    _set_defaults(emission_node, {'Color': color})

    material.node_tree.links.new(output_node.inputs['Surface'], emission_node.outputs['Emission'])


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

    if modifier is None and create:
        modifier = object.modifiers.new(name.value, name.name)

        if name == ModifierName.DISPLACE:
            _setup_displace_modifier(modifier)
        elif name == ModifierName.SOLIDIFY:
            _setup_solidify_modifier(modifier)
        elif name == ModifierName.WIREFRAME:
            _setup_wireframe_modifier(modifier)

    return modifier


def _find_modifier(object: Union[Object, None], name: MaterialName) -> Union[Modifier, None]:
    '''Try to find the modifier with the given name on the given mesh object.'''
    if (object is not None) and (object.type == 'MESH'):
        if name.value in object.modifiers:
            return object.modifiers[name.value]

    return None


def _setup_displace_modifier(modifier: DisplaceModifier):
    '''Setup the displace modifier.'''
    modifier.show_in_editmode = True
    modifier.show_on_cage = True
    modifier.direction = 'NORMAL'
    modifier.mid_level = 0.0

    settings: 'RetopoMatSettings' = bpy.context.scene.retopo_mat
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

    settings: 'RetopoMatSettings' = bpy.context.scene.retopo_mat
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

    settings: 'RetopoMatSettings' = bpy.context.scene.retopo_mat
    modifier.show_viewport = settings.get_internal('wireframe_visibility')
    modifier.thickness = settings.get_internal('wireframe_thickness')


def remove_modifiers(object: Object):
    '''Remove retopo modifiers with from the given object.'''
    for name in ModifierName:
        modifier = _find_modifier(object, name)

        if modifier is not None:
            object.modifiers.remove(modifier)


def move_modifiers_to_bottom(object: Object):
    '''Move retopo modifiers to the bottom of the stack.'''
    index = len(object.modifiers) - 1

    for name in ModifierName:
        modifier = _find_modifier(object, name)

        if modifier is not None:
            try:  # Newer versions of Blender can use modifier_move_to_index.
                bpy.ops.object.modifier_move_to_index(modifier=modifier.name, index=index)

            except:  # Older versions of Blender have to use modifier_move_down.
                for _ in range(index - object.modifiers.find(modifier.name)):
                    bpy.ops.object.modifier_move_down(modifier=modifier.name)


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
