from __future__ import annotations

from pathlib import Path

from core.addon_store import AddonMetadataStore
from core.extensibility.loader import DiscoveredPlugin
from core.git_service import GitService
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore
from interface.about.repo_about_page import RepoAboutPage
from interface.repo_addon_panel_registry import RepoAddonPanelRegistry
from interface.section_registry import SectionRegistry, SectionSpec

# Same string value as the old SectionKey(str, Enum) member, so anything
# persisted under this string (e.g. nothing currently is, but this keeps
# the door open) stays stable across the migration. Explorer/Submit used to
# be registered here too (REPO_BROWSER/REPO_GIT_STATUS) — they're now real
# plugins, see plugins/studio/explorer/plugin.py and
# plugins/studio/submit/plugin.py.
REPO_ABOUT = "repo_about"

_ICONS_DIR = Path(__file__).resolve().parent.parent / "data" / "icons"


def register_builtin_sections(
    registry: SectionRegistry,
    *,
    store: MetadataStore,
    local_config_store: LocalConfigStore,
    git_service: GitService,
    program_store: ProgramStore,
    addon_store: AddonMetadataStore,
    repo_addon_panel_registry: RepoAddonPanelRegistry,
    addon_catalog: list[DiscoveredPlugin],
) -> None:
    """Constructs the built-in About page and registers it into `registry`
    exactly like a plugin would register its own — order 30 leaves room
    (10/20) for Explorer/Submit's own plugins to insert sections before it."""
    repo_about_page = RepoAboutPage(
        store=store,
        local_config_store=local_config_store,
        program_store=program_store,
        addon_store=addon_store,
        git_service=git_service,
        addon_catalog=addon_catalog,
        repo_addon_panel_registry=repo_addon_panel_registry,
    )

    registry.register(
        SectionSpec(
            key=REPO_ABOUT,
            label="About",
            order=30,
            page_factory=lambda: repo_about_page,
            icon_path=_ICONS_DIR / "icons8-about-32.png",
        )
    )
