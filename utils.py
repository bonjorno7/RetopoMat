from enum import Enum
from typing import List, Union

import bpy
from bpy.types import (Material, Mesh, Object, ShaderNodeBsdfPrincipled, ShaderNodeEmission, ShaderNodeOutputMaterial,
                       WireframeModifier)


class MaterialName(Enum):
    REFERENCE = 'RetopoMat Reference'
    RETOPO = 'RetopoMat Retopo'
    WIRE = 'RetopoMat Wire'


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
    material.use_nodes = True
    material.node_tree.nodes.clear()

    principled_node = material.node_tree.nodes.new(ShaderNodeBsdfPrincipled.__name__)
    output_node = material.node_tree.nodes.new(ShaderNodeOutputMaterial.__name__)

    # TODO: Move nodes to aesthetically pleasing positions.
    # TODO: Set default values for nodes.

    material.node_tree.links.new(output_node.inputs[0], principled_node.outputs[0])


def _setup_retopo_material(material: Material):
    '''Setup the retopo material.'''
    material.use_nodes = True
    material.node_tree.nodes.clear()

    emission_node = material.node_tree.nodes.new(ShaderNodeEmission.__name__)
    output_node = material.node_tree.nodes.new(ShaderNodeOutputMaterial.__name__)

    # TODO: Move nodes to aesthetically pleasing positions.
    # TODO: Set default values for nodes.

    material.node_tree.links.new(output_node.inputs[0], emission_node.outputs[0])


def _setup_wire_material(material: Material):
    '''Setup the wire material.'''
    material.use_nodes = True
    material.node_tree.nodes.clear()

    emission_node = material.node_tree.nodes.new(ShaderNodeEmission.__name__)
    output_node = material.node_tree.nodes.new(ShaderNodeOutputMaterial.__name__)

    # TODO: Move nodes to aesthetically pleasing positions.
    # TODO: Set default values for nodes.

    material.node_tree.links.new(output_node.inputs[0], emission_node.outputs[0])


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
