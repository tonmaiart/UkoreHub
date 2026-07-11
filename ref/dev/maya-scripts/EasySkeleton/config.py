import EasySkeleton

# Always Re-Open The Window After Config Edited
root_file = EasySkeleton.__file__.replace("\__init__.py", "")

# OBJECT TYPE NAME CONVENTION
grpCtrl = "grpCtrl"
grpOff = "grpOff"
ctrl = "ctrl"
jnt = "jnt"
grp = "grp"
loc = "loc"
crv = "crv"
nrb = "nrb"
guide = "guide"
grpPin = "grpPin"
grpAim = "grpAim"
flc = "flc"
list_type = [grpCtrl,grpOff,ctrl,jnt,grp,loc,crv,nrb,guide,grpPin,grpAim,flc]

# SIDE NAME CONVENTION
isDebug = 1
L = "LFT"
R = "RGT"
center = "CEN"

# RIG STRUCTURE
default_rig_name = "CharacterRig"
ctrl_main = "WorldCtrl"
ctrl_fly = "RootCtrl"
loc_root = "rootLoc"
grp_skin = "GlobalJoints"
grp_local = "LocalJoints"
grp_still = "Others"
grp_anim = "AutoRig"
grp_mesh = "Meshes"
grp_global_joint_backup = "GlobalJointsBackup"
grp_local_joint_backup = "LocalJointsBackup"
grp_controller_backup = "ControllerBackup"
grp_controller_reference = "ControllerReference"

all_controller_sets = "AllController"

root_file = EasySkeleton.__file__.replace("\__init__.py", "")
toolkit_path = root_file+"\\toolkits"

unit_scale = 1
