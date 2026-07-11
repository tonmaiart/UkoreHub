import tmlib
from tmlib.core import QuickData, Validate,Visualized,Geometry
import maya.cmds as cmds
import maya.api.OpenMaya as om
import os
import maya.cmds as cmds
import glob
def clean_up_char_model_file():
    selection = cmds.ls(sl=1)
    Validate.validate_material_face_set(selection=selection)

    # validate uv sets

    pass

def match_shape_with_wrap():
    """
    Blend Shape with wrap deformer , ignore vertex id

    To use
    1.select prefer shape mesh > select before mesh (vertex order should match) > select target mesh that wanna match

    """

    pass

def auto_match_bounding_box():
    """Select ref and target mesh , the ref will try to scale the mesh size to reach fill the bounding box of target mesh"""

    # get from selection
    sel = cmds.ls(sl=1)

    if not sel:
        return

    if (cmds.selectPref(tso=True, q=True)==0):
        cmds.selectPref(tso=True)
        
    sel = cmds.ls(orderedSelection =1,fl=1)

    # first one is target , second one is ref
    vertices_ref = []
    vertices_target = []

    first_name = None
    second_name = None

    for s in sel:
        mesh_name = s.split(".")[0]

        if first_name is None:
            first_name = mesh_name
        
        if first_name and second_name is None and first_name != mesh_name:
            second_name = mesh_name
        
        if mesh_name == first_name:
            vertices_target.append(s)
        elif mesh_name == second_name:
            vertices_ref.append(s)

    Geometry.auto_match_bounding_box_by_vertices(vertices_ref=vertices_ref,vertices_target=vertices_target)



def clean_model():
    sel = cmds.ls(sl=1, l=1)
    list_child = cmds.listRelatives(sel, ad=1, typ="transform", f=1)
    list_target = sel + list_child if list_child is not None else sel

    # unlock attributes
    for target in list_target:
        list_attr = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]
        [cmds.setAttr("{}.{}".format(target, attr), k=1, l=0) for attr in list_attr]

    # delete history
    [cmds.delete(list_target, ch=1) for target in list_target]

    # delete orig shape
    for target in list_target:
        list_shapes = cmds.listRelatives(target, c=1, s=1, typ="mesh", f=1)

        if list_shapes:
            # delete orig
            for shape in list_shapes:
                if "Orig" in shape:
                    cmds.delete(shape)

            # rename all shape
            for shape in list_shapes:
                parent_name = cmds.listRelatives(shape, p=1, typ="transform")[0]
                parent_name = (
                    parent_name.split("|")[-1]
                    if "|" in parent_name
                    else parent_name
                )

                cmds.rename(shape, parent_name + "Shape")

    cmds.select(cl=1)


def run_matcap_ui():
    # --- Configuration ---
    DEFAULT_PATH = r"G:\My Drive\Mellowstar\share\MatCaps"
    THUMB_SIZE = 90  # Slightly smaller to account for scrollbar padding
    COLUMNS = 5

    def matCapShader():
        if cmds.objExists("matCapShader"):
            return ("matCapShader", "matCapFile")
            
        mainShader = cmds.shadingNode("surfaceShader", n="matCapShader", asShader=True)
        envBall = cmds.shadingNode("envBall", n="matCapBall", asTexture=True)
        placeTextureNode3D = cmds.shadingNode("place3dTexture", n="matCapTexturePlacer3d", asUtility=True)
        fileNode = cmds.shadingNode("file", n="matCapFile", asTexture=True)
        placeTextureNode2D = cmds.shadingNode("place2dTexture", n="matCapTexturePlacer2d", asUtility=True)
        
        cmds.connectAttr(f"{placeTextureNode3D}.worldInverseMatrix", f"{envBall}.placementMatrix")
        cmds.connectAttr(f"{envBall}.outColor", f"{mainShader}.outColor")
        
        attrs = ["coverage", "translateFrame", "rotateFrame", "mirrorU", "mirrorV", 
                "stagger", "wrapU", "wrapV", "repeatUV", "offset", "rotateUV", "noiseUV"]
        for attr in attrs:
            cmds.connectAttr(f"{placeTextureNode2D}.{attr}", f"{fileNode}.{attr}")
            
        cmds.connectAttr(f"{placeTextureNode2D}.outUV", f"{fileNode}.uv")
        cmds.connectAttr(f"{placeTextureNode2D}.outUvFilterSize", f"{fileNode}.uvFilterSize")
        cmds.connectAttr(f"{fileNode}.outColor", f"{envBall}.image", force=True)
        
        cmds.setAttr(f"{fileNode}.filterType", 0)
        cmds.setAttr(f"{envBall}.eyeSpace", 1)
        
        return (mainShader, fileNode)

    def set_matcap(path):
        if cmds.objExists(fileName):
            cmds.setAttr(f"{fileName}.fileTextureName", path, type="string")
            print(f"Applied: {os.path.basename(path)}")

    def fetchFiles(*args):
        path = cmds.textField(inputPath, q=True, text=True)
        
        # Clear existing grid
        children = cmds.rowColumnLayout(gridParent, q=True, ca=True) or []
        for child in children:
            cmds.deleteUI(child)

        if os.path.exists(path):
            extensions = ('.jpg', '.jpeg', '.png', '.tga', '.tif', '.tiff')
            files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(extensions)]
            
            if files:
                cmds.setParent(gridParent)
                for f in files:
                    short_name = os.path.basename(f)
                    # We use iconOnly style and put the name in the annotation (tooltip)
                    # to maximize the space for the image.
                    cmds.iconTextButton(
                        style='iconOnly',
                        image1=f,
                        w=THUMB_SIZE,
                        h=THUMB_SIZE,
                        mw=2, # Margin width
                        mh=2, # Margin height
                        c=lambda x=f: set_matcap(x),
                        ann=short_name,
                        bgc=(0.15, 0.15, 0.15)
                    )
            else:
                cmds.warning("No images found.")
        else:
            cmds.warning("Path not found.")

    def assignShader(*args):
        sel = cmds.ls(sl=True)
        if sel:
            cmds.hyperShade(assign=shaderName)
        else:
            cmds.warning("Select an object.")

    # --- UI Setup ---
    win_id = "matcapGridWin"
    if cmds.window(win_id, exists=True):
        cmds.deleteUI(win_id)

    window = cmds.window(win_id, title="MatCap Browser", widthHeight=(520, 550), sizeable=True)
    
    createShader = matCapShader()
    fileName = createShader[1]
    shaderName = createShader[0]

    main_layout = cmds.columnLayout(adjustableColumn=True)
    
    # Path bar
    cmds.rowLayout(nc=3, ad3=2, p=main_layout, columnOffset3=[5, 5, 5])
    cmds.text(l="Path:")
    inputPath = cmds.textField(text=DEFAULT_PATH)
    cmds.button(l="Refresh", c=fetchFiles)
    cmds.setParent(main_layout)

    cmds.separator(h=10, style='none')

    # Scrollable Grid
    scroll = cmds.scrollLayout(h=400, childResizable=True, p=main_layout, bgc=(0.1, 0.1, 0.1))
    gridParent = cmds.rowColumnLayout(nc=COLUMNS, cw=[(i, THUMB_SIZE) for i in range(1, COLUMNS+1)], rat=[(i, 'top', 0) for i in range(1, COLUMNS+1)])
    
    cmds.setParent(main_layout)
    cmds.separator(h=10, style='none')
    cmds.button(l="Assign MatCap to Selection", h=50, bgc=(0.3, 0.4, 0.3), c=assignShader)

    fetchFiles()
    cmds.showWindow(window)
