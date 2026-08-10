from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from core.models import Program, Repo


@dataclass(frozen=True)
class ProgramLaunchSpec:
    """Lets one plugin (e.g. maya_launcher) contribute its own launch
    behavior for a Program that plugins/core/software_linker's Program
    Launcher tab would otherwise just subprocess.Popen the raw linked exe
    for — Maya needs setProject/env-merge/force-load-plugins wiring, not a
    bare process launch. `match` decides whether this spec applies to a
    given Program; `launch` does the actual launch given the active Repo
    and returns True once it has handled it (mirrors
    interface/extensibility/file_opener.py's FileOpenerSpec shape)."""

    match: Callable[[Program], bool]
    launch: Callable[[Repo], bool]


class ProgramLaunchRegistry:
    """Open collection of ProgramLaunchSpecs — not a KeyedOrderedRegistry
    (specs aren't keyed by a stable string id, and more than one could
    legitimately match different Programs). First match wins, checked in
    registration order. There's no guaranteed order between plugins'
    register(api) calls, but plugins/core/software_linker/plugin.py only
    ever calls find_launcher() later, at double-click time — long after
    every plugin has finished registering — so that ordering caveat
    doesn't matter in practice."""

    def __init__(self) -> None:
        self._specs: list[ProgramLaunchSpec] = []

    def register(self, spec: ProgramLaunchSpec) -> None:
        self._specs.append(spec)

    def find_launcher(self, program: Program) -> Callable[[Repo], bool] | None:
        for spec in self._specs:
            if spec.match(program):
                return spec.launch
        return None
