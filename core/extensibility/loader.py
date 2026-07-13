from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

MANIFEST_FILENAME = "manifest.json"


@dataclass
class PluginManifest:
    id: str
    name: str
    version: str
    api_version: int
    entry_point: str
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "PluginManifest":
        return cls(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            api_version=int(data["api_version"]),
            entry_point=data["entry_point"],
            description=data.get("description", ""),
        )


@dataclass
class DiscoveredPlugin:
    manifest: PluginManifest
    module: ModuleType
    dir_path: Path


@dataclass
class PluginLoadFailure:
    dir_path: Path
    reason: str


@dataclass
class PluginDiscoveryResult:
    loaded: list[DiscoveredPlugin]
    failures: list[PluginLoadFailure]


def discover_plugins(roots: list[Path], api_version: int) -> PluginDiscoveryResult:
    """Scans each root's immediate subdirectories for a manifest.json + entry
    point module, in the order `roots` is given (so passing [studio, local]
    means a duplicate plugin id in `local` loses to `studio`). Never raises —
    any problem with a single plugin directory is recorded as a
    PluginLoadFailure and skipped, so one broken plugin can't stop the app
    from starting."""
    loaded: list[DiscoveredPlugin] = []
    failures: list[PluginLoadFailure] = []
    seen_ids: set[str] = set()

    for root in roots:
        if not root.is_dir():
            continue
        for plugin_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            result = _load_one(plugin_dir, api_version, seen_ids)
            if isinstance(result, PluginLoadFailure):
                failures.append(result)
            else:
                loaded.append(result)
                seen_ids.add(result.manifest.id)

    return PluginDiscoveryResult(loaded=loaded, failures=failures)


def _load_one(plugin_dir: Path, api_version: int, seen_ids: set[str]) -> DiscoveredPlugin | PluginLoadFailure:
    manifest_path = plugin_dir / MANIFEST_FILENAME
    if not manifest_path.exists():
        return PluginLoadFailure(plugin_dir, f"no {MANIFEST_FILENAME} found")

    try:
        manifest = PluginManifest.from_dict(json.loads(manifest_path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        return PluginLoadFailure(plugin_dir, f"malformed manifest: {exc}")

    if manifest.id in seen_ids:
        return PluginLoadFailure(plugin_dir, f"duplicate plugin id '{manifest.id}' (already loaded)")

    if manifest.api_version != api_version:
        return PluginLoadFailure(
            plugin_dir,
            f"api_version {manifest.api_version} does not match app's {api_version}",
        )

    entry_path = plugin_dir / manifest.entry_point
    if not entry_path.exists():
        return PluginLoadFailure(plugin_dir, f"entry_point '{manifest.entry_point}' not found")

    try:
        spec = importlib.util.spec_from_file_location(f"ukorehub_plugin_{manifest.id}", entry_path)
        if spec is None or spec.loader is None:
            return PluginLoadFailure(plugin_dir, f"could not build import spec for '{entry_path}'")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 - isolate any import-time failure in plugin code
        return PluginLoadFailure(plugin_dir, f"failed to import entry_point: {exc}")

    return DiscoveredPlugin(manifest=manifest, module=module, dir_path=plugin_dir)


def plugin_source(discovered: DiscoveredPlugin) -> str:
    """'studio' or 'local' — the plugins_root subdirectory this plugin was
    discovered under (see discover_plugins' `roots` order)."""
    return discovered.dir_path.parent.name


def apply_plugins(discovered: list[DiscoveredPlugin], api) -> list[PluginLoadFailure]:
    """Calls `module.register(api)` for each discovered plugin, isolated in
    its own try/except. `api` is duck-typed here on purpose — this function
    doesn't need to know PluginAPI's shape, keeping it Qt-agnostic and
    testable with a fake api object and fake plugin modules."""
    failures: list[PluginLoadFailure] = []
    for plugin in discovered:
        register = getattr(plugin.module, "register", None)
        if register is None:
            failures.append(PluginLoadFailure(plugin.dir_path, "entry_point has no register(api) function"))
            continue
        try:
            register(api)
        except Exception as exc:  # noqa: BLE001 - isolate a broken plugin's register() call
            failures.append(PluginLoadFailure(plugin.dir_path, f"register(api) raised: {exc}"))
    return failures
