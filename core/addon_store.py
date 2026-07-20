from __future__ import annotations

import json
from pathlib import Path

from core.models import AddonMetadata
from core.store import _atomic_write

SCHEMA_VERSION = 1

# Shown for any add-on that hasn't been given its own icon via Setting >
# Add-ons — lives in icons_dir alongside per-addon icon overrides.
DEFAULT_ICON_FILENAME = "icons8-tools-50.png"


class AddonMetadataStore:
    """Shared studio-wide overrides for discovered add-ons (icon,
    description, required Program(s)) — backed by data/addon_settings.json,
    tracked in git alongside programs.json/projects.json (same "shared
    team data" category, matching how enabling/disabling an add-on for a
    repo already affects everyone). Mirrors core/program_store.py's shape."""

    def __init__(self, json_path: Path):
        self.json_path = Path(json_path)
        self.addons: list[AddonMetadata] = []
        self.load()

    def load(self) -> None:
        if not self.json_path.exists():
            self.addons = []
            self.save()
            return
        data = json.loads(self.json_path.read_text(encoding="utf-8"))
        self.addons = [AddonMetadata.from_dict(a) for a in data.get("addons", [])]

    def save(self) -> None:
        data = {
            "schema_version": SCHEMA_VERSION,
            "addons": [a.to_dict() for a in self.addons],
        }
        _atomic_write(self.json_path, data)

    def get(self, addon_id: str) -> AddonMetadata:
        """Every discovered add-on is valid before its first edit, so this
        returns a default-empty AddonMetadata rather than raising."""
        for addon in self.addons:
            if addon.addon_id == addon_id:
                return addon
        return AddonMetadata(addon_id=addon_id)

    def _get_or_create(self, addon_id: str) -> AddonMetadata:
        for addon in self.addons:
            if addon.addon_id == addon_id:
                return addon
        addon = AddonMetadata(addon_id=addon_id)
        self.addons.append(addon)
        return addon

    def set_description(self, addon_id: str, description: str) -> None:
        addon = self._get_or_create(addon_id)
        addon.description = description.strip()
        self.save()

    def set_icon(self, addon_id: str, filename: str | None) -> None:
        addon = self._get_or_create(addon_id)
        addon.icon_filename = filename
        self.save()

    def set_required_program_ids(self, addon_id: str, program_ids: list[str]) -> None:
        addon = self._get_or_create(addon_id)
        addon.required_program_ids = list(program_ids)
        self.save()

    @property
    def icons_dir(self) -> Path:
        return self.json_path.parent / "addon_icons"

    def resolve_icon_path(self, addon: AddonMetadata) -> Path | None:
        if not addon.icon_filename:
            return None
        return self.icons_dir / addon.icon_filename

    def resolve_display_icon_path(self, addon: AddonMetadata) -> Path | None:
        """Like resolve_icon_path, but falls back to the shared
        DEFAULT_ICON_FILENAME when no custom icon is configured — for
        display contexts that always want to show something. Editing UIs
        that need to distinguish "no icon set" from "has an icon" should
        keep using resolve_icon_path directly."""
        icon_path = self.resolve_icon_path(addon)
        if icon_path is not None and icon_path.exists():
            return icon_path
        default_path = self.icons_dir / DEFAULT_ICON_FILENAME
        return default_path if default_path.exists() else None


def group_addon_ids_by_program(
    addon_ids: list[str], addon_store: AddonMetadataStore
) -> tuple[dict[str, list[str]], list[str]]:
    """Splits addon_ids into (by_program_id, ungrouped) using each add-on's
    AddonMetadata.required_program_ids. An add-on that declares multiple
    required programs appears under each of them (OR semantics) — an
    add-on with none, or whose declared program isn't relevant to the
    caller, lands in `ungrouped` so callers can show it in a fallback
    "Other Add-ons" section instead of silently dropping it."""
    by_program: dict[str, list[str]] = {}
    ungrouped: list[str] = []
    for addon_id in addon_ids:
        required = addon_store.get(addon_id).required_program_ids
        if not required:
            ungrouped.append(addon_id)
            continue
        for program_id in required:
            by_program.setdefault(program_id, []).append(addon_id)
    return by_program, ungrouped
