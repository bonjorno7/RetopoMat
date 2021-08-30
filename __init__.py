# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    'name': 'RetopoMat',
    'author': 'luwizart, bonjorno7',
    'description': 'A new method that makes retopology fun',
    'blender': (2, 80, 0),
    'version': (1, 0, 0),
    'category': '3D View',
    'location': 'View3D',
}

from . import ops, props, ui

modules = (
    props,
    ops,
    ui,
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
