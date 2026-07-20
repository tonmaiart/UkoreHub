# Playblast wrote into C:\<name> instead of the repo's Custom Path

## Symptom

User set the repo's UkoreShot Custom Path to `/movie`, expecting it to
resolve relative to the active repo. Instead `UkoreShotPlayblast` wrote
the video straight into `C:\movie` — the repo folder was dropped
entirely.

## Root cause

`plugins/studio/UkoreShotPlayblast/maya-scripts/UkoreShotPlayblast/function.py`'s
`_resolve_video_root` joined the repo path and the stored Custom Path with
pathlib's `/` operator:

```python
return repo_path / custom_path["path"]
```

`CustomPath.path` (`plugins/studio/project_editor/pipeline_store.py`) is
saved as whatever raw string the user typed into the "Create Input Path"
field — no sanitization on write. On Windows, `WindowsPath("C:/repo") /
"/movie"` evaluates to `WindowsPath("C:/movie")`: a path segment starting
with `/` (or `\`) has a root of its own, so pathlib treats it as anchored
and discards everything from the left operand except the drive letter.
Since a Custom Path is documented (GLOSSARY.md) as always relative to the
repo, any value starting with a separator silently broke the join.

## Fix

`_resolve_video_root` now strips leading `/`/`\` from `custom_path["path"]`
before joining:

```python
return repo_path / custom_path["path"].lstrip("/\\")
```

Also fixed the same day in `plugins/studio/UkoreShot/video_path_store.py`'s
`resolve_video_root` (line 73), which this function's own docstring says it
mirrors exactly — same `repo_path / repo.local_path / custom_path["path"]`
join. Initially left unfixed as out-of-scope for the Playblast-only change,
but the user then playblasted successfully into the corrected folder and
reported UkoreShot's video library Refresh still not showing it — the
`video_path_store.py` copy of the bug was resolving to the wrong folder
(`C:\<name>` instead of the repo's real video folder) so Refresh looked in
the wrong place. Same one-line `lstrip("/\\")` fix applied there.

## Lesson

Any code that joins a stored `CustomPath.path` onto a base directory with
pathlib's `/` operator is vulnerable to this — the value is raw user input
with no sanitization at write time, so a leading `/` or `\` (easy to type,
e.g. mirroring a Unix-style path or a leftover clipboard paste) silently
anchors the join to the current drive root instead of raising an error.
Strip leading separators (or validate at write time in
`pipeline_store.py`'s `CustomPath`/the settings page instead) before
joining. Grep for `custom_path["path"]` before adding a new consumer.
