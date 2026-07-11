from core.store import MetadataStore


def test_set_repo_thumbnail_persists(tmp_path):
    json_path = tmp_path / "projects.json"
    store_a = MetadataStore(json_path)
    project = store_a.add_project("Kafka")
    repo = store_a.add_repo(project.id, "repo1", "https://example.com/repo1.git", str(tmp_path))
    store_a.set_repo_thumbnail(project.id, repo.id, "abc123.png")

    store_b = MetadataStore(json_path)
    reloaded_repo = store_b.get_repo(project.id, repo.id)
    assert reloaded_repo.thumbnail_filename == "abc123.png"


def test_resolve_thumbnail_path_none_when_unset(tmp_path):
    store = MetadataStore(tmp_path / "projects.json")
    project = store.add_project("Kafka")
    repo = store.add_repo(project.id, "repo1", "https://example.com/repo1.git", str(tmp_path))
    assert store.resolve_thumbnail_path(repo) is None


def test_resolve_thumbnail_path_when_set(tmp_path):
    store = MetadataStore(tmp_path / "projects.json")
    project = store.add_project("Kafka")
    repo = store.add_repo(project.id, "repo1", "https://example.com/repo1.git", str(tmp_path))
    store.set_repo_thumbnail(project.id, repo.id, "abc123.png")
    repo = store.get_repo(project.id, repo.id)
    assert store.resolve_thumbnail_path(repo) == store.thumbnails_dir / "abc123.png"


def test_backward_compat_missing_thumbnail_field(tmp_path):
    json_path = tmp_path / "projects.json"
    json_path.write_text(
        """{
        "schema_version": 1,
        "projects": [
            {"id": "p1", "name": "Kafka", "repos": [
                {"id": "r1", "name": "repo1", "git_url": "x", "local_path": "Kafka/repo1"}
            ]}
        ]
        }""",
        encoding="utf-8",
    )
    store = MetadataStore(json_path)
    repo = store.get_repo("p1", "r1")
    assert repo.thumbnail_filename is None
