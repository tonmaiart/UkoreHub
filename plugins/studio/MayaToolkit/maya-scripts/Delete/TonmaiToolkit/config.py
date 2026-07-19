import TonmaiToolkit
import os

ROOT_PATH = TonmaiToolkit.__file__.replace("__init__.py", "")
TOOLKIT_PATH = os.path.join(ROOT_PATH,"toolkits")
CACHE_NODE = "tonmai_toolkit_cache"

# set side name config
L = "L"
R = "R"

# freeze group config
freeze_prefix = 1
freeze_name = "grp"

# quick controller config
jointOnly = False