import pytest

from core.exceptions import ValidationError
from interface.settings_tab_registry import SettingsTabRegistry, SettingsTabSpec


def _spec(key, order=0, **kwargs):
    return SettingsTabSpec(key=key, label=key, order=order, page_factory=lambda: None, **kwargs)


def test_register_then_ordered_returns_by_order():
    registry = SettingsTabRegistry()
    registry.register(_spec("c", order=20))
    registry.register(_spec("a", order=0))
    registry.register(_spec("b", order=10))

    assert [spec.key for spec in registry.ordered()] == ["a", "b", "c"]


def test_duplicate_key_raises_validation_error():
    registry = SettingsTabRegistry()
    registry.register(_spec("dup", order=0))
    with pytest.raises(ValidationError):
        registry.register(_spec("dup", order=10))


def test_on_activated_is_optional_and_stored():
    activated = []
    spec = SettingsTabSpec(
        key="k",
        label="K",
        order=0,
        page_factory=lambda: None,
        on_activated=lambda widget: activated.append(widget),
    )
    registry = SettingsTabRegistry()
    registry.register(spec)

    (stored,) = registry.ordered()
    stored.on_activated("widget")

    assert activated == ["widget"]


def test_on_activated_defaults_to_none():
    registry = SettingsTabRegistry()
    registry.register(_spec("k"))
    (stored,) = registry.ordered()
    assert stored.on_activated is None
