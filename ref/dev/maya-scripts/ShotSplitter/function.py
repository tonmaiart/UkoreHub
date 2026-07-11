import maya.cmds as cmds


def offset_all_keyframes(time_shift):
    animated_curves = (
        cmds.ls(type=["animCurve", "animCurveUT", "animCurveUU", "animCurveUL"]) or []
    )

    for curve in animated_curves:
        try:
            cmds.keyframe(curve, edit=True, relative=True, timeChange=time_shift)
        except Exception:
            # ignore curves we can't edit (refs, locked, etc.)
            pass


def emphazise_keyframes(new_start_frame, new_end_frame):
    animated_curves = (
        cmds.ls(type=["animCurve", "animCurveUT", "animCurveUU", "animCurveUL"]) or []
    )

    for curve in animated_curves:
        # get plugs this curve drives
        plugs = cmds.listConnections(curve + ".output", plugs=True) or []
        if not plugs:
            continue
        # could be multiple plugs; iterate all
        for plug in plugs:
            # plug format: "node.attr" or "node.attr[sub]"
            if "." not in plug:
                continue
            node, attr = plug.split(".", 1)
            # check existing key at new_start_frame
            existing_start = cmds.keyframe(
                node + "." + attr,
                time=(new_start_frame, new_start_frame),
                query=True,
            )
            if not existing_start:
                try:
                    cmds.setKeyframe(node, at=attr, t=new_start_frame, i=True)
                except Exception:
                    pass
            existing_end = cmds.keyframe(
                node + "." + attr,
                time=(new_end_frame, new_end_frame),
                query=True,
            )
            if not existing_end:
                try:
                    cmds.setKeyframe(node, at=attr, t=new_end_frame, i=True)
                except Exception:
                    pass


def set_time_range(start_frame, end_frame):
    cmds.playbackOptions(animationStartTime=start_frame, animationEndTime=end_frame)
    cmds.playbackOptions(minTime=start_frame, maxTime=end_frame)


def trim_all_keyframes(start_frame, end_frame):
    animated_curves = (
        cmds.ls(type=["animCurve", "animCurveUT", "animCurveUU", "animCurveUL"]) or []
    )
    total_trimmed = 0

    for curve in animated_curves:
        try:
            cmds.cutKey(curve, time=(None, start_frame - 1), option="keys")
            total_trimmed += 1
        except Exception:
            pass
        try:
            cmds.cutKey(curve, time=(end_frame + 1, None), option="keys")
            total_trimmed += 1
        except Exception:
            pass


def set_audio_ranges(t_start, t_end, i_start, i_end):
    """
    Set timeline start/end and internal start/end (offset)
    for all audio nodes in scene.
    """

    audios = cmds.ls(type="audio")
    if not audios:
        cmds.warning("No audio nodes found.")
        return

    for a in audios:
        print("Editing:", a)

        # Timeline start
        cmds.setAttr(a + ".offset", t_start)

        # Timeline end
        cmds.setAttr(a + ".endFrame", t_end)

        # Internal offset start
        cmds.setAttr(a + ".sourceStart", i_start)

        # Internal offset end
        cmds.setAttr(a + ".sourceEnd", i_end)
