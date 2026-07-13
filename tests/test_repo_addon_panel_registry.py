import pytest

from core.exceptions import ValidationError
from interface.repo_addon_panel_registry import RepoAddonPanelRegistry, RepoAddonPanelSpec


def _spec(addon_id, **kwargs):
    return RepoAddonPanelSpec(addon_id=addon_id, panel_factory=lambda repo: None, **kwargs)


def test_register_then_get_returns_spec():
    registry = RepoAddonPanelRegistry()
    spec = _spec("maya_launcher")
    registry.register(spec)

    assert registry.get("maya_launcher") is spec


def test_get_on_unregistered_id_returns_none():
    registry = RepoAddonPanelRegistry()
    assert registry.get("missing") is None


def test_duplicate_addon_id_raises_validation_error():
    registry = RepoAddonPanelRegistry()
    registry.register(_spec("dup"))
    with pytest.raises(ValidationError):
        registry.register(_spec("dup"))


def test_panel_factory_is_stored_not_invoked():
    calls = []
    spec = RepoAddonPanelSpec(addon_id="k", panel_factory=lambda repo: calls.append("called"))
    registry = RepoAddonPanelRegistry()
    registry.register(spec)

    registry.get("k")

    assert calls == []
