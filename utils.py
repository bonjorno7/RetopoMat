from typing import List, Union

import bpy
from bpy.types import Material, Mesh, Object, ShaderNodeBsdfPrincipled, ShaderNodeEmission, ShaderNodeOutputMaterial

REFERENCE = 'RetopoMat Reference'
RETOPO = 'RetopoMat Retopo'
MATERIAL = Union[REFERENCE, RETOPO]


def get_material(name: MATERIAL) -> Material:
    '''Get a material with the given name, create it if necessary.'''
    if name in bpy.data.materials:
        material = bpy.data.materials[name]
    else:
        material = bpy.data.materials.new(name)

    if name == REFERENCE and not _check_reference_material(material):
        _setup_reference_material(material)
    elif name == RETOPO and not _check_retopo_material(material):
        _setup_retopo_material(material)

    return material


def _check_reference_material(material: Material) -> bool:
    '''Check whether the reference material is valid.'''
    if not material.use_nodes:
        return False

    # TODO: Check whether a principled node is present.

    return True


def _check_retopo_material(material: Material) -> bool:
    '''Check whether the retopo material is valid.'''
    if not material.use_nodes:
        return False

    # TODO: Check whether an emission node is present.

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


# TODO: Add function to add node at position, and maybe a dict for default values?


def set_material(objects: List[Object], material: Material = None):
    '''For each mesh object, clear materials, then add the given material.'''
    for object in objects:
        if object.type != 'MESH':
            continue

        data: Mesh = object.data
        data.materials.clear()

        if material is not None:  # If the material is None, don't assign it.
            data.materials.append(material)
