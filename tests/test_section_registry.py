import pytest

from core.exceptions import ValidationError
from interface.section_registry import SectionRegistry, SectionSpec


def _spec(key, order=0, **kwargs):
    return SectionSpec(key=key, label=key, order=order, page_factory=lambda: None, **kwargs)


def test_register_then_ordered_returns_by_order():
    registry = SectionRegistry()
    registry.register(_spec("c", order=20))
    registry.register(_spec("a", order=0))
    registry.register(_spec("b", order=10))

    assert [spec.key for spec in registry.ordered()] == ["a", "b", "c"]


def test_ties_broken_by_key():
    registry = SectionRegistry()
    registry.register(_spec("z", order=0))
    registry.register(_spec("a", order=0))

    assert [spec.key for spec in registry.ordered()] == ["a", "z"]


def test_duplicate_key_raises_validation_error():
    registry = SectionRegistry()
    registry.register(_spec("dup", order=0))
    with pytest.raises(ValidationError):
        registry.register(_spec("dup", order=10))


def test_page_factory_is_stored_not_invoked():
    calls = []
    spec = SectionSpec(key="k", label="K", order=0, page_factory=lambda: calls.append("called"))
    registry = SectionRegistry()
    registry.register(spec)

    registry.ordered()

    assert calls == []
