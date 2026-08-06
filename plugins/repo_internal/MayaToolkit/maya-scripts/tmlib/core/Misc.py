import re
import maya.cmds as cmds
import os
import maya.api.OpenMaya as om
import glob


def extract_vertices(vertex_range):
    # Use regex to parse the vertex string
    match = re.match(r"(.+)\.vtx\[(\d+):(\d+)\]", vertex_range)
    if not match:
        raise ValueError("Invalid vertex range format.")

    base_name = match.group(1)
    start_idx = int(match.group(2))
    end_idx = int(match.group(3))

    # Generate the list of individual vertices
    return [f"{base_name}.vtx[{i}]" for i in range(start_idx, end_idx + 1)]


"""
Collection of function that deal with polishing rig
"""


def scale_to_matrix(scale=(1, 1, 1)):
    sx, sy, sz = scale
    matrix_list = [sx, 0, 0, 0, 0, sy, 0, 0, 0, 0, sz, 0, 0, 0, 0, 1]
    return om.MMatrix(matrix_list)


def get_scale_from_matrix(matrix):
    """
    Accepts a 4x4 matrix (nested or flat) and returns scale (sx, sy, sz).
    Requires maya.api.OpenMaya (API 2.0)
    """
    # Flatten if nested
    if isinstance(matrix[0], list):
        matrix = [item for row in matrix for item in row]

    # Convert to MMatrix and extract scale
    mtx = om.MMatrix(matrix)
    mtx_transform = om.MTransformationMatrix(mtx)
    return mtx_transform.getScale(om.MSpace.kTransform)
