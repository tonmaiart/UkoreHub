from __future__ import annotations

from typing import Generic, Protocol, TypeVar

from core.exceptions import ValidationError


class _KeyedOrderedSpec(Protocol):
    key: str
    order: int


T = TypeVar("T", bound=_KeyedOrderedSpec)


class KeyedOrderedRegistry(Generic[T]):
    """Shared base for interface/'s open, ordered, duplicate-key-rejecting
    registries — SectionRegistry, SettingsTabRegistry, and
    SidebarFooterActionRegistry are otherwise identical: register a
    dataclass spec keyed by its own `key` field, reject a duplicate key,
    expose specs sorted by `(order, key)`. RepoAddonPanelRegistry (keyed,
    but no ordering concept — just a `get(addon_id)` lookup) and
    FileOpenerRegistry (unordered, duplicate keys allowed by design — see
    its own docstring) are deliberately NOT built on this; each solves a
    different problem than "ordered, unique-key list of specs"."""

    def __init__(self, *, label: str) -> None:
        self._label = label
        self._specs: dict[str, T] = {}

    def register(self, spec: T) -> None:
        if spec.key in self._specs:
            raise ValidationError(f"{self._label} key '{spec.key}' is already registered")
        self._specs[spec.key] = spec

    def ordered(self) -> list[T]:
        return sorted(self._specs.values(), key=lambda spec: (spec.order, spec.key))

    def keys(self) -> set[str]:
        return set(self._specs.keys())
