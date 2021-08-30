from typing import List

import bpy
from bpy.types import Material, Mesh, Object, ShaderNodeBsdfPrincipled, ShaderNodeEmission, ShaderNodeOutputMaterial


def get_material(name: str) -> Material:
    '''Get an empty material with the given name, create it if necessary.'''
    if name in bpy.data.materials:
        material = bpy.data.materials[name]
    else:
        material = bpy.data.materials.new(name)

    material.use_nodes = True
    material.node_tree.nodes.clear()

    return material


# TODO: Add function to add node at position, and maybe a dict for default values?


def get_reference_material() -> Material:
    '''Setup the reference material.'''
    material = get_material('RetopoMat Reference')

    principled_node = material.node_tree.nodes.new(ShaderNodeBsdfPrincipled.__name__)
    output_node = material.node_tree.nodes.new(ShaderNodeOutputMaterial.__name__)

    # TODO: Move nodes to aesthetically pleasing positions.
    # TODO: Set default values for nodes.

    material.node_tree.links.new(output_node.inputs[0], principled_node.outputs[0])

    return material


def get_retopo_material() -> Material:
    '''Setup the retopo material.'''
    material = get_material('RetopoMat Retopo')

    emission_node = material.node_tree.nodes.new(ShaderNodeEmission.__name__)
    output_node = material.node_tree.nodes.new(ShaderNodeOutputMaterial.__name__)

    # TODO: Move nodes to aesthetically pleasing positions.
    # TODO: Set default values for nodes.

    material.node_tree.links.new(output_node.inputs[0], emission_node.outputs[0])

    return material


def assign_material(objects: List[Object], material: Material):
    '''For each mesh object, clear materials, then assign the given material.'''
    for object in objects:
        if object.type != 'MESH':
            continue

        data: Mesh = object.data
        data.materials.clear()

        if material is not None:  # If the material is None, don't assign it.
            data.materials.append(material)
