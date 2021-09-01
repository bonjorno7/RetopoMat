from enum import Enum
from typing import List, Union

import bpy
from bpy.types import (Material, Mesh, Object, ShaderNodeBsdfPrincipled, ShaderNodeEmission, ShaderNodeOutputMaterial,
                       WireframeModifier)


class MaterialName(Enum):
    REFERENCE = 'RetopoMat Reference'
    RETOPO = 'RetopoMat Retopo'
    WIRE = 'RetopoMat Wire'


def check_material_slots(objects: List[Object]) -> bool:
    '''Check whether any of the given objects have multiple material slots.'''
    for object in objects:
        if object.type != 'MESH':
            continue

        data: Mesh = object.data
        if len(data.materials) > 1:
            return True

    return False


def get_material(name: MaterialName) -> Material:
    '''Get a material with the given name, create it if necessary.'''
    if name.value in bpy.data.materials:
        material = bpy.data.materials[name.value]
    else:
        material = bpy.data.materials.new(name.value)

    if name is MaterialName.REFERENCE:
        if not _check_reference_material(material):
            _setup_reference_material(material)

    elif name is MaterialName.RETOPO:
        if not _check_retopo_material(material):
            _setup_retopo_material(material)

    elif name is MaterialName.WIRE:
        if not _check_wire_material(material):
            _setup_wire_material(material)

    return material


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

    if 'Emission' not in material.node_tree.nodes:
        return False

    return True


def _check_wire_material(material: Material) -> bool:
    '''Check whether the wire material is valid.'''
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
    principled_node = _add_node(material, ShaderNodeBsdfPrincipled, (-400, 0))

    # TODO: Get color and alpha from settings.
    _set_defaults(principled_node, {
        'Base Color': (0.2, 0.2, 0.2, 1.0),
        'Roughness': 0.7,
        'Metallic': 1.0,
        'Alpha': 0.8,
    })

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
    emission_node = _add_node(material, ShaderNodeEmission, (-200, 0))
    invert_node = _add_node(material, ShaderNodeInvert, (-400, 0))
    geometry_node = _add_node(material, ShaderNodeNewGeometry, (-600, 0))

    settings: 'RetopoMatSettings' = bpy.context.scene.retopo_mat
    _set_defaults(emission_node, {'Color': settings.color})

    material.node_tree.links.new(output_node.inputs['Surface'], emission_node.outputs['Emission'])
    material.node_tree.links.new(emission_node.inputs['Strength'], invert_node.outputs['Color'])
    material.node_tree.links.new(invert_node.inputs['Color'], geometry_node.outputs['Backfacing'])


def _setup_wire_material(material: Material):
    '''Setup the wire material.'''
    material.blend_method = 'OPAQUE'
    material.shadow_method = 'NONE'

    material.use_backface_culling = False
    material.show_transparent_back = False

    material.use_nodes = True
    material.node_tree.nodes.clear()

    output_node = _add_node(material, ShaderNodeOutputMaterial, (0, 0))
    emission_node = _add_node(material, ShaderNodeEmission, (-200, 0))

    # TODO: Get color from settings.
    _set_defaults(emission_node, {'Color': (0, 0, 0, 1)})

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


def set_materials(objects: List[Object], materials: List[Material]):
    '''For each mesh object, clear materials, then add the given materials.'''
    for object in objects:
        if object.type != 'MESH':
            continue

        data: Mesh = object.data
        data.materials.clear()

        for material in materials:
            data.materials.append(material)


def get_wire_modifier(object: Union[Object, None]) -> Union[WireframeModifier, None]:
    '''Get the last wireframe modifier for the given mesh object, create it if necessary.'''
    if object is None or object.type != 'MESH':
        return None

    for modifier in reversed(object.modifiers):
        if modifier.type == 'WIREFRAME':
            return modifier

    modifier: WireframeModifier = object.modifiers.new('Wireframe', 'WIREFRAME')
    modifier.show_in_editmode = True
    modifier.offset = 0.0
    modifier.use_boundary = True
    modifier.use_replace = False
    modifier.use_even_offset = False
    modifier.use_relative_offset = False
    modifier.use_crease = False
    modifier.material_offset = 1

    settings: 'RetopoMatSettings' = bpy.context.scene.retopo_mat
    modifier.show_viewport = settings.wire_visibility
    modifier.thickness = settings.wire_thickness

    return modifier
