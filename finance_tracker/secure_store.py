"""
Local encryption and file-permission helpers.

Financial JSON files are encrypted at rest with Fernet (AES-128). The key lives
in the data directory at `.key` (mode 0600), or in the macOS Keychain when
available. Plaintext files written by older versions are read and rewritten
encrypted on the next save.

The data directory is mode 0700; data files are 0600. New keys are written only
to `.key` (never passed on a `security` process argv).
"""

from __future__ import annotations

import json
import logging
import os
import stat
import subprocess
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

MAGIC = b"FTENC1"
KEYCHAIN_ACCOUNT = "finance-tracker"
KEYCHAIN_SERVICE = "finance-tracker-data-key"


class _JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


def ensure_secure_dir(path: Path) -> None:
    """Create a directory and restrict it to the current user (0700)."""
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, stat.S_IRWXU)
    except OSError as exc:
        logger.warning("Could not set directory permissions on %s: %s", path, exc)


def chmod_private(path: Path) -> None:
    """Restrict a file to owner read/write (0600)."""
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError as exc:
        logger.warning("Could not set file permissions on %s: %s", path, exc)


def _fernet():
    from cryptography.fernet import Fernet

    return Fernet


def _keychain_get() -> Optional[bytes]:
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-a",
                KEYCHAIN_ACCOUNT,
                "-s",
                KEYCHAIN_SERVICE,
                "-w",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    secret = result.stdout.strip()
    return secret.encode() if secret else None


def load_or_create_key(data_dir: Path) -> bytes:
    """Load the Fernet key from Keychain or `.key`, creating one if needed.

    New keys are written only to `.key` with mode 0600. The key is never passed
    as a `security -w` argument (visible in process listings).
    """
    Fernet = _fernet()
    keychain_key = _keychain_get()
    if keychain_key:
        return keychain_key

    ensure_secure_dir(data_dir)
    key_path = data_dir / ".key"
    if key_path.exists():
        return key_path.read_bytes().strip()

    key = Fernet.generate_key()
    key_path.write_bytes(key)
    chmod_private(key_path)
    return key


class SecureJSON:
    """Read/write JSON with optional Fernet encryption and tight permissions."""

    def __init__(self, data_dir: Path, enabled: bool = True):
        self.data_dir = Path(data_dir)
        ensure_secure_dir(self.data_dir)
        self.enabled = enabled
        self._fernet = None
        if enabled:
            Fernet = _fernet()
            self._fernet = Fernet(load_or_create_key(self.data_dir))

    def write(self, path: Path, data: Any) -> None:
        """Serialize `data` to JSON, encrypt if enabled, write with mode 0600."""
        path = Path(path)
        ensure_secure_dir(path.parent)
        raw = json.dumps(data, indent=2, cls=_JSONEncoder).encode("utf-8")
        if self.enabled and self._fernet is not None:
            payload = MAGIC + self._fernet.encrypt(raw)
            path.write_bytes(payload)
        else:
            path.write_bytes(raw)
        chmod_private(path)

    def read(self, path: Path) -> Any:
        """Read JSON, decrypting FTENC1 payloads. Plaintext JSON still loads."""
        path = Path(path)
        raw = path.read_bytes()
        if raw.startswith(MAGIC):
            if self._fernet is None:
                raise ValueError(f"{path} is encrypted; enable security.encryption")
            from cryptography.fernet import InvalidToken

            try:
                raw = self._fernet.decrypt(raw[len(MAGIC) :])
            except InvalidToken as exc:
                raise ValueError(f"Could not decrypt {path}") from exc
        return json.loads(raw.decode("utf-8"))

    def migrate_if_plaintext(self, path: Path) -> None:
        """Re-encrypt a plaintext JSON file in place when encryption is on."""
        if not self.enabled or not path.exists():
            return
        raw = path.read_bytes()
        if raw.startswith(MAGIC):
            return
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return
        self.write(path, data)
        logger.info("Encrypted existing plaintext file %s", path)
