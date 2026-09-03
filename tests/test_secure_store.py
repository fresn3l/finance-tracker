"""Tests for encrypted JSON storage and file permissions."""

import json
import stat

import pytest

from finance_tracker.secure_store import MAGIC, SecureJSON, ensure_secure_dir, load_or_create_key


class TestSecureJSON:
    def test_round_trip_encrypted(self, tmp_path):
        store = SecureJSON(tmp_path, enabled=True)
        path = tmp_path / "data.json"
        store.write(path, {"hello": "world", "n": 1})

        raw = path.read_bytes()
        assert raw.startswith(MAGIC)
        assert not raw.lstrip().startswith(b"{")
        assert store.read(path) == {"hello": "world", "n": 1}

    def test_plaintext_fallback_and_migrate(self, tmp_path):
        path = tmp_path / "legacy.json"
        path.write_text(json.dumps({"transactions": []}), encoding="utf-8")
        store = SecureJSON(tmp_path, enabled=True)
        assert store.read(path) == {"transactions": []}

        store.migrate_if_plaintext(path)
        assert path.read_bytes().startswith(MAGIC)
        assert store.read(path) == {"transactions": []}

    def test_disabled_writes_plaintext(self, tmp_path):
        store = SecureJSON(tmp_path, enabled=False)
        path = tmp_path / "plain.json"
        store.write(path, {"a": 1})
        assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1}

    def test_file_and_dir_permissions(self, tmp_path):
        store = SecureJSON(tmp_path, enabled=True)
        path = tmp_path / "secret.json"
        store.write(path, {"x": 1})

        dir_mode = stat.S_IMODE(tmp_path.stat().st_mode)
        file_mode = stat.S_IMODE(path.stat().st_mode)
        assert dir_mode == 0o700
        assert file_mode == 0o600

    def test_key_file_is_private(self, tmp_path):
        key = load_or_create_key(tmp_path)
        assert len(key) > 0
        key_path = tmp_path / ".key"
        assert key_path.exists()
        assert stat.S_IMODE(key_path.stat().st_mode) == 0o600
        assert load_or_create_key(tmp_path) == key

    def test_ensure_secure_dir(self, tmp_path):
        nested = tmp_path / "a" / "b"
        ensure_secure_dir(nested)
        assert nested.is_dir()
        assert stat.S_IMODE(nested.stat().st_mode) == 0o700

    def test_encrypted_file_requires_key(self, tmp_path):
        store = SecureJSON(tmp_path, enabled=True)
        path = tmp_path / "data.json"
        store.write(path, {"secret": True})
        plaintext_store = SecureJSON(tmp_path, enabled=False)
        with pytest.raises(ValueError, match="encrypted"):
            plaintext_store.read(path)
