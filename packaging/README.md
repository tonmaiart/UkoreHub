# packaging/

Admin-only dev/ops tooling for building `UkoreHub.exe`, a thin native
launcher artists can double-click or pin to the taskbar instead of running
`python launcher.py` from a terminal. Not imported by the running app —
run manually by an admin, only when rebranding the icon or changing
exe_entry.py itself.

- `build_exe.py` — run this to (re)build `UkoreHub.exe` at the repo root.
  Installs `pyinstaller` into the current environment if missing (this
  script's own concern only — PyInstaller is never added to launcher.py's
  dependency bootstrap). `--icon`/`--name` CLI args, defaults to
  `icon.ico`/"UkoreHub".
- `exe_entry.py` — the tiny script PyInstaller compiles. Locates
  `launcher.py` as a sibling of wherever the exe is actually running from,
  finds a real `pythonw`/`python` on PATH (never derives it from its own
  frozen `sys.executable`), and spawns `launcher.py` detached, then exits
  immediately — a hand-off, not a supervisor.
- `icon.ico` — the icon baked into `UkoreHub.exe` (swap this file and rerun
  `build_exe.py` to rebrand). Git-tracked. `launcher.py` also loads this
  same file directly (`QApplication.setWindowIcon`) — `UkoreHub.exe` only
  owns this icon for the instant it exists before handing off to a plain
  `python(w).exe` process (see `exe_entry.py`), which would otherwise show
  Windows' generic Python icon in the taskbar/title bar without that.

See root `README.md`'s "Running" section for how artists use the built
exe, and `.gitignore` for why `build/` and `*.spec` (PyInstaller's
regenerable intermediates) are excluded while the final `.exe` is not.
