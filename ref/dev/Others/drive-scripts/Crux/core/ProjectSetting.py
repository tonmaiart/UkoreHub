import sys
import os
import logging
import re
import shutil
import Crux

from Crux.utils import utility

import logging

logging.basicConfig(level=logging.INFO)

# ==============================
# Management Class
# ==============================


class ProjectSetting:
    """Store all preference setting of project"""

    def __init__(self):
        # Define Paths
        self.project_config_path = os.path.normpath(os.path.join(os.path.dirname(Crux.__file__), "prefs"))
        self.job_data_cache_path = os.path.normpath(os.path.join(self.project_config_path, "job_data_cache.json"))


        # Define Variables
        self.workspace_config = None
        self.project_config = None
        self.job_requirements_config = None
        self.publish_paths_config = None
        self.software_config = None
        self.job_data_cache = None

        # Load Data Once
        self.load_config_json()

    def get_creds_oauth_client(self):
        return os.path.join(
            os.path.dirname(Crux.__file__), "prefs", "oauth_client_creds.json"
        )

    def get_creds_service_client(self):
        return os.path.join(
            os.path.dirname(Crux.__file__), "prefs", "service_client_creds.json"
        )

    def get_project_name(self):
        return self.project_config["project"]["name"]

    def get_project_config_data(self):
        return self.project_config

    def load_config_json(self):
        self.project_config = utility.import_json_to_dict(
            os.path.join(self.project_config_path, "project_paths.json")
        )

        self.workspace_config = utility.import_json_to_dict(
            os.path.join(self.project_config_path, "workspace_paths.json")
        )

        self.job_requirements_config = utility.import_json_to_dict(
            os.path.join(self.project_config_path, "job_requirements.json")
        )

        self.publish_paths_config = utility.import_json_to_dict(
            os.path.join(self.project_config_path, "publish_paths.json")
        )

        self.software_config = utility.import_json_to_dict(
            os.path.join(self.project_config_path, "job_software.json")
        )

        self.job_data_cache = utility.import_json_to_dict(self.job_data_cache_path)

    def get_workspace_config(self):
        return self.workspace_config

    def get_project_config(self):
        return self.project_config

    def get_job_requirements_config(self):
        return self.job_requirements_config

    def get_publish_paths_config(self):
        return self.publish_paths_config

    def get_project_name(self):
        return self.project_config["name"]

    def get_software_config(self):
        return self.software_config
