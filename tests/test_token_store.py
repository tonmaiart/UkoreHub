import json
import sys
import types

import pytest

from core.token_store import TokenStore, TokenStoreFallbackUsed


@pytest.fixture
def failing_keyring(monkeypatch):
    fake_module = types.ModuleType("keyring")

    def _raise(*_args, **_kwargs):
        raise RuntimeError("no keyring backend available")

    fake_module.set_password = _raise
    fake_module.get_password = _raise
    fake_module.delete_password = _raise
    monkeypatch.setitem(sys.modules, "keyring", fake_module)
    yield


def test_save_token_falls_back_to_file(tmp_path, failing_keyring):
    store = TokenStore(tmp_path / "token.json")
    with pytest.raises(TokenStoreFallbackUsed):
        store.save_token("abc123")
    fallback_path = tmp_path / "token.json"
    assert fallback_path.exists()
    data = json.loads(fallback_path.read_text(encoding="utf-8"))
    assert data["token"] == "abc123"


def test_load_token_from_fallback(tmp_path, failing_keyring):
    store = TokenStore(tmp_path / "token.json")
    with pytest.raises(TokenStoreFallbackUsed):
        store.save_token("abc123")
    assert store.load_token() == "abc123"


def test_clear_token_removes_fallback_file(tmp_path, failing_keyring):
    store = TokenStore(tmp_path / "token.json")
    with pytest.raises(TokenStoreFallbackUsed):
        store.save_token("abc123")
    store.clear_token()
    assert not (tmp_path / "token.json").exists()
    assert store.load_token() is None
