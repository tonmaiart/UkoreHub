from UkoreMaya.menu import General, Rig, Skin
from UkoreMaya.core import Plugin, function
from tmlib.core import File

# ------------- File Launchers -------------------


def browser():
    File.launch("UkoreBrowser")


def python_reader():
    File.launch("PythonReader")


def model_publisher():
    File.launch("ModelPublisher")


def rig_publisher():
    File.launch("RigPublisher")


def animation_publisher():
    File.launch("AnimationPublisher")


def publish_browser():
    File.launch("PublishBrowser")


def renamer():
    File.launch("Renamer")


def attribute():
    File.launch("Attribute")


def quickdata():
    File.launch("QuickData")


def easy_controller():
    File.launch("EasyController")


def advanced_control():
    File.launch("AdvancedControl")


def snapper():
    File.launch("Snapper")


def weight_puller():
    File.launch("WeightPuller")


def shot_splitter():
    File.launch("ShotSplitter")


def cfx_tools():
    File.launch("CFXTools")

def quick_script():
    File.launch("QuickScript")


# ------------- Scene ----------------------------


def save_increment():
    File.save_increment()


def update_references():
    print("# Checking for Update References #")
    update_ref_result = function.update_references()

    if update_ref_result is True:
        function.import_all_picker()


# ------------- General --------------------------


def reset_transform():
    General.reset_transform()


def flip_selection():
    General.flip_selection()


def flip_animation_value():
    File.launch("FlipAnimValue")


def smart_parent():
    General.smart_parent()


def lock_attr():
    General.lock_attribute()


def unlock_attr():
    General.unlock_attribute()


def sort_type(t):
    General.sort_by_type(t)


# ------------- Model ---------------
def auto_position_to_grid():
    General.move_to_grid_from_biggest_bbox(4, padding=0)


def export_selected_to_substance():
    validate_material()
    General.check_and_select_multi_uv()
    General.export_single_combined()


def export_selected_to_multiple():
    validate_material()
    General.check_and_select_multi_uv()
    General.export_multiple_separated()


def validate_material():
    General.validate_and_fix_material_names()


def cleanup_uvmap():
    General.clean_uvmap()


def validate_uv_map():
    General.check_and_select_multi_uv()


def validate_facesets():
    General.validate_facesets()


# ------------- Rig ------------------------------


def run_advanced():
    function.run_advance()


def run_advanced_face():
    function.run_advance_face()


def auto_constraint(mode):
    Rig.auto_constraint(mode)


def auto_connection(mode):
    Rig.auto_connection(mode)


def follicle_pin():
    Rig.create_follicle_pin()


def freeze_group():
    Rig.freeze_group()


def copy_shape():
    Rig.copy_shape()


# ------------- Skin -----------------------------


def create_joint_set():
    Skin.create_joint_set()


def copy_skin_weight():
    Skin.fast_copy_weight()


def add_multi_skin():
    Skin.add_multi_skin_cluster()


# ------------- Animation ------------------------


def dreamwall_picker():
    function.dreamwall_picker()

def studio_library():
    function.studio_library()

# ------------- Developer ------------------------


def faster_plugin():
    function.setup_faster_load()


def playblast():
    # Split out into its own plugin 2026-07-19 (configurable options +
    # destination now live entirely inside Maya instead of being
    # hardcoded here) — see plugins/studio/UkoreShotPlayblast/README.md.
    from UkoreShotPlayblast import function as ukore_shot_playblast

    ukore_shot_playblast.publish_playblast()


def playblast_options():
    from UkoreShotPlayblast import options_dialog as ukore_shot_playblast_options

    ukore_shot_playblast_options.show()


def print_selected():
    function.print_selected()


def selected_to_dict():
    function.selected_to_blank_dict()


# ------------- Reload Plug-ins ------------------
def reload_plugins():
    Plugin.reload_plugins()
