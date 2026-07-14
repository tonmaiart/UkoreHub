# interface/about/

The About tab (`SectionRegistry` key `repo_about`) — repo info, requirements/
add-ons, and the dynamic per-add-on panels. Browser Links used to be
configured from a third sub-tab here ("Browser") — moved to
`interface/settings/browser_links_settings_page.py` under Settings > Repo,
since it's a repo *setting* rather than repo info (see
`interface/settings/README.md`).

- `repo_about_page.py` — `RepoAboutPage`: a left-tab-bar shell (like
  `interface/settings/settings_view.py`), not a flat page. Fixed sub-tabs:
  - **About** (`_RepoAboutInfoTab`) — repo info, an editable Description
    (writes through `core/store.py`'s `MetadataStore.set_repo_description`,
    edited via the shared `_DescriptionEditDialog`), Open Folder, and Choose
    Thumbnail (writes through `MetadataStore.set_repo_thumbnail`).
  - **Requirement** (`_RepoRequirementsTab`) — `RequirementCard`/`AddonCard`
    rendering (`AddonCard` shows an add-on's icon/name/description only —
    no source badge, the tab itself already makes clear these are add-ons)
    plus an Edit Requirements button (`interface/shared/dialogs.py`'s
    `RequirementsEditDialog`) and, per `RequirementCard`, an inline Edit
    Description button that also uses `_DescriptionEditDialog` and writes
    through `core/program_store.py`'s `ProgramStore.edit_program` — the
    same field `interface/settings/program_database_page.py` edits, just a
    more convenient second entry point.

  Plus one dynamic sub-tab per enabled add-on with a
  `RepoAddonPanelRegistry` panel, rebuilt on every `set_repo()`.
- `browser_link_page.py` — `BrowserLinkPage`: one dynamically-created
  top-level tab per configured Browser Link (not itself a `SectionRegistry`
  section — rebuilt on every repo switch by `main_window.py`, see its
  `_rebuild_browser_link_tabs`). Embeds the link's URL in a
  `QWebEngineView` behind a Back/Forward/Reset toolbar, using the single
  persistent `QWebEngineProfile` `main_window.py` constructs via
  `interface/web_engine_profile.py` so a login (Notion, Google Sheet, ...)
  survives app restarts. Lives here rather than at the interface/ root
  because it's still About's own dynamic-tab machinery, even though the
  Browser Links themselves are now configured from Settings > Repo.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, a `shared/` addition, or touches `main_window.py`'s
wiring.
