import re
import maya.cmds as cmds
import os
import maya.api.OpenMaya as om
import glob


def get_min_max_position_from_vertices(vertices):
    """
    get min vector and max vector of input vertices
    """

    x_values = []
    y_values = []
    z_values = []

    for v in vertices:
        pos = cmds.xform(v,ws=1,t=1,q=1)

        x_values.append(pos[0])
        y_values.append(pos[1])
        z_values.append(pos[2])

    # get max value
    min_vector = [min(x_values),min(y_values),min(z_values)]
    max_vector = [max(x_values),max(y_values),max(z_values)]

    return min_vector,max_vector

def auto_match_bounding_box_by_vertices(
    vertices_ref:list,
    vertices_target:list
):
    """scaling target mesh based on vertices target vertices bounding box"""

    # selection = cmds.ls(sl=1)
    ref = vertices_ref[0].split(".")[0]
    target = vertices_target[0].split(".")[0]

    ref_vector_min,ref_vector_max =  get_min_max_position_from_vertices(vertices_ref)
    target_vector_min,target_vector_max =  get_min_max_position_from_vertices(vertices_target)

    print("ref vector min :",ref_vector_min)
    print("ref vector max :",ref_vector_max)

    # reset pivot
    cmds.xform(target,rotatePivot=(0,0,0))
    cmds.xform(target,rotatePivot=(0,0,0))

    cmds.xform(target,scalePivot=(0,0,0))
    cmds.xform(ref,scalePivot=(0,0,0))

    pivot_ref_vertex = om.MVector(ref_vector_max)
    pivot_target_vertex = om.MVector(target_vector_max)

    pivot_ref_space = cmds.xform(ref,ws=1,q=1,rotatePivot=1)
    pivot_target_space = cmds.xform(target,ws=1,q=1,rotatePivot=1)

    # # create vector from ref to target space
    v_TS_RS_pivot = om.MVector(pivot_ref_space) - om.MVector(pivot_target_space)
    v_RO_RV = pivot_ref_vertex - om.MVector(pivot_ref_space)
    v_TO_TV = pivot_target_vertex - om.MVector(pivot_target_space)

    # ==============
    # Match World Position
    # ==============
    t_match_space = om.MVector(pivot_target_space)+v_TS_RS_pivot
    t_offset_to_vertex = t_match_space + (v_RO_RV-v_TO_TV) 
    cmds.xform(target,ws=1,t=t_offset_to_vertex)

    # ==============================
    # scale to match bounding box
    # ==============================

    # update new min , max vector
    target_vector_min,target_vector_max =  get_min_max_position_from_vertices(vertices_target)
    pivot_target_vertex = om.MVector(target_vector_max)
    # Visualized.create_point_visualized(pivot_ref_vertex,"ref_vertex")
    # Visualized.create_point_visualized(pivot_target_vertex,"target_vertex")

    cmds.xform(target,scalePivot=pivot_target_vertex,ws=1)

    # snap pivot
    pivot_ref_vertex_second =  om.MVector(cmds.xform(vertices_ref[1],ws=1,q=1,t=1)) 
    pivot_target_vertex_second =  om.MVector(cmds.xform(vertices_target[1],ws=1,q=1,t=1))
    
    v_refFirst_to_refSecond = pivot_ref_vertex_second-pivot_ref_vertex
    v_targetFirst_to_targetSecond = pivot_target_vertex_second-pivot_target_vertex 

    # Visualized.create_vector_visualized(start_point=(pivot_target_vertex+v_targetFirst_to_targetSecond),end_point=(pivot_ref_vertex+v_refFirst_to_refSecond))

    for i,axis in enumerate("xyz"):
        # if (pivot_target_vertex_second[i]-pivot_target_vertex[i]) == 0:
        #     continue
        
        print("# ======= axis : ",axis)
        # finding scale offset 
        ref_value_min = ref_vector_min[i]
        target_value_min = target_vector_min[i]
        
        ref_value_min_length = ref_value_min - pivot_ref_vertex[i]
        target_value_min_length = target_value_min - pivot_target_vertex[i]

        print(pivot_ref_vertex[i],pivot_target_vertex[i])
        print(ref_value_min_length,target_value_min_length)
        ratio = ref_value_min_length/target_value_min_length

        #scale_offset = #(pivot_ref_vertex_second[i]-pivot_ref_vertex[i]) / (pivot_target_vertex_second[i]-pivot_target_vertex[i])

        print("axis : {} , ref value {} , target value {} ,ratio : {}".format(
            axis,
            pivot_ref_vertex_second[i]-pivot_ref_vertex[i],
            pivot_target_vertex_second[i]-pivot_target_vertex[i], 
            ratio))

        cmds.setAttr(target+".s{}".format(axis),ratio)
