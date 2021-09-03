from enum import Enum
from typing import TYPE_CHECKING, List, Tuple, Union

from bmesh import from_edit_mesh, update_edit_mesh
from bmesh.types import BMFace
import bpy
from bpy.types import (Material, Mesh, Object, ShaderNode, ShaderNodeBsdfPrincipled, ShaderNodeEmission,
                       ShaderNodeInvert, ShaderNodeNewGeometry, ShaderNodeOutputMaterial, WireframeModifier)

if TYPE_CHECKING:
    from .props import RetopoMatSettings


class MaterialName(Enum):
    REFERENCE = 'RetopoMat Reference'
    RETOPO = 'RetopoMat Retopo'
    WIRE = 'RetopoMat Wire'


_WIREFRAME_NAME = 'RetopoMat Wireframe'


def check_material_slots(object: Object) -> bool:
    '''Check whether the given object has multiple material slots.'''
    data: Mesh = object.data
    return len(data.materials) > 1


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

    elif name is MaterialName.WIRE:
        if not _check_wire_material(material):
            _setup_wire_material(material)

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

    settings: 'RetopoMatSettings' = bpy.context.scene.retopo_mat
    _set_defaults(principled_node, {
        'Base Color': settings.reference_color,
        'Alpha': settings.reference_color[3],
        'Roughness': 0.7,
        'Metallic': 1.0,
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
    _set_defaults(emission_node, {'Color': settings.retopo_color})

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

    settings: 'RetopoMatSettings' = bpy.context.scene.retopo_mat
    _set_defaults(emission_node, {'Color': settings.wire_color})

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
    if object is None or object.type != 'MESH':
        return

    data: Mesh = object.data
    data.materials.clear()

    for material in materials:
        data.materials.append(material)


def get_wire_modifier(object: Union[Object, None], create: bool = False) -> Union[WireframeModifier, None]:
    '''Get the last wireframe modifier for the given mesh object, create it if necessary.'''
    if object is None or object.type != 'MESH':
        return None
    elif _WIREFRAME_NAME in object.modifiers:
        return object.modifiers[_WIREFRAME_NAME]
    elif not create:
        return None

    modifier: WireframeModifier = object.modifiers.new(_WIREFRAME_NAME, 'WIREFRAME')
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


def remove_wire_modifier(object: Union[Object, None]):
    '''Remove our wireframe modifier from the given object.'''
    modifier = get_wire_modifier(object)

    if modifier is not None:
        object.modifiers.remove(modifier)


def flip_normals(object: Object):
    '''Flip all face normals on the given edit mode mesh object.'''
    bm = from_edit_mesh(object.data)

    for face in bm.faces:
        face: BMFace
        face.normal_flip()

    update_edit_mesh(object.data)


def move_wireframe_to_bottom(object: Object):
    '''Move our wireframe modifier to the bottom of the stack.'''
    index = len(object.modifiers) - 1

    try:  # Newer versions of Blender can use modifier_move_to_index.
        bpy.ops.object.modifier_move_to_index(modifier=_WIREFRAME_NAME, index=index)

    except:  # Older versions of Blender have to use modifier_move_down.
        for _ in range(index - object.modifiers.find(_WIREFRAME_NAME)):
            bpy.ops.object.modifier_move_down(modifier=_WIREFRAME_NAME)
