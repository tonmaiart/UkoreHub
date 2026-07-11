import os

# # Set the environment variable before loading Shifter
current_file = __file__
current_dir = os.path.dirname(__file__)
mgear_path = os.path.join(current_dir,"mgear_shifter_components")
os.environ["MGEAR_SHIFTER_COMPONENT_PATH"] = mgear_path

print("""

  _______                          _   _______          _ _    _ _   
 |__   __|                        (_) |__   __|        | | |  (_) |  
    | | ___  _ __  _ __ ___   __ _ _     | | ___   ___ | | | ___| |_ 
    | |/ _ \| '_ \| '_ ` _ \ / _` | |    | |/ _ \ / _ \| | |/ / | __|
    | | (_) | | | | | | | | | (_| | |    | | (_) | (_) | |   <| | |_ 
    |_|\___/|_| |_|_| |_| |_|\__,_|_|    |_|\___/ \___/|_|_|\_\_|\__|


""")