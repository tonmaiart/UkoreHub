from enum import Enum


class SectionKey(str, Enum):
    PROJECT_INFO = "project_info"
    REPO_BROWSER = "repo_browser"
    REPO_GIT_STATUS = "repo_git_status"
    REPO_ABOUT = "repo_about"
