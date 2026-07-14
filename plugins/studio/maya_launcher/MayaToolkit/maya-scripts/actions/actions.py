# ============================================================
# Copyright (c) 2022 PluginMania. All rights reserved.
# Please check the license at the following link.
# https://raw.githubusercontent.com/PluginMania/RenderOverrideForMaya/main/LICENSE
# ============================================================

# https://docs.python.org/ja/3/library/typing.html
from __future__ import annotations

import maya.cmds as cmds


def __get_valid_node_name():
    '''Get a node with a valid RenderOverride

    :returns: Return the node name. If there is no valid node, return None.
    :rtype: str | None
    '''
    node_list = cmds.listNodeTypes('utility/general')
    if 'renderOverride' not in node_list:
        return

    render_override_nodes = cmds.ls(type='renderOverride')
    if not render_override_nodes:
        return

    # Returns node names for which the node's enabled attribute
    # is True (checked in name sort order).
    # If there is no applicable node, "None" is returned.
    for node in sorted(render_override_nodes):
        if cmds.getAttr(f'{node}.enable'):
            return node

def __get_action_attr_list():
    '''Returns information about the action attribute.
    The elements of the list are tuples of "(ActionName, StartFrame)"

    :returns: Returns information about the action attribute.
              If there is no information, an empty list is returned.
    :rtype: list
    '''
    render_override_node = __get_valid_node_name()
    if render_override_node is None:
        return []

    # Get information on multiIndices
    index_list = cmds.getAttr(f'{render_override_node}.actions', multiIndices=True)
    if index_list is None:
        return []

    # Summarize information on actions in action_list
    # [('walk', 1, 14), ('run', 15, 30), (action_name, start_frame, end_frame)....]
    action_list: list = []
    for index in index_list:
        # Action name
        action_name = cmds.getAttr(f'{render_override_node}.actions[{index}].actionName')
        if action_name is None:
            action_name = ''
        # Start frame
        start_frame = cmds.getAttr(f'{render_override_node}.actions[{index}].actionStartFrame')
        if type(start_frame) != float:
            start_frame = 0.0
        # End frame
        end_frame = cmds.getAttr(f'{render_override_node}.actions[{index}].actionEndFrame')
        if type(end_frame) != float:
            end_frame = 0.0

        action_list.append((action_name, start_frame, end_frame))

    # Sort the list by start_frame, just in case
    return sorted(action_list, key=lambda x:x[1])

def __get_cur_action_info():
    '''Returns information about the current action in dict type

    :returns: Returns information on the current action as a dict type,
              or None if there is no action information.
              e.g.)
              {
                  'action_name': 'Walk',
                  'start_frame': 1,
                  'end_frame': 10
              }
    :rtype: dict | None
    '''
    # Obtain information on actions that apply in the current frame
    #
    #      1             cur_frame            15
    #      | --------------- | --------------- | ----....
    #  ('walk', 1, 14)                        ('run', 15, 30)
    #  => The action that applies to the current frame is 'walk'.

    action_attr_list: list = __get_action_attr_list()
    if not action_attr_list:
        return

    cur_frame = cmds.currentTime(query=True)
    # Variable to store the return value
    cur_action_info = {}
    for (action_name, start_frame, end_frame) in action_attr_list:
        if start_frame <= cur_frame <= end_frame:
            cur_action_info['action_name'] = action_name
            cur_action_info['start_frame'] = int(start_frame)
            cur_action_info['end_frame']   = int(end_frame)
            break

    if not cur_action_info:
        return

    return cur_action_info

def actions_text() -> str | list[str]:
    '''Returns the text to be displayed by RenderOverride.
    The developer must set the return type to either str or list[str].
    It is the developer's responsibility to guarantee the return type.
    If there is no character to return, return an empty character.

    :returns: Returns the text to be displayed by RenderOverride.
    :rtype: str | list[str]
    '''
    cur_action_info = __get_cur_action_info()
    if cur_action_info is None:
        return ''

    action_name: str = cur_action_info['action_name']
    start_frame: int = cur_action_info['start_frame']
    end_frame  : int = cur_action_info['end_frame']

    return f'{action_name} [{start_frame}-{end_frame}]'
