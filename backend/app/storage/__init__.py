"""
Storage service abstraction. Implement LocalStorage now (files encrypted at rest
with Fernet). Structured so S3 / Azure Blob can be added later.
"""
import abc
import os
import uuid
from typing import BinaryIO, Optional

from cryptography.fernet import Fernet

from app.core.config import settings


class StorageService(abc.ABC):
    """Abstract base for file storage."""

    @abc.abstractmethod
    def save(self, data: bytes, filename: str) -> str:
        """Save data, return a storage key."""
        ...

    @abc.abstractmethod
    def read(self, storage_key: str) -> bytes:
        """Return the raw (decrypted) bytes for a storage key."""
        ...

    @abc.abstractmethod
    def delete(self, storage_key: str) -> None:
        """Delete a stored file."""
        ...


class LocalStorage(StorageService):
    """
    Stores files on the local filesystem, encrypted at rest with Fernet.
    Directory layout: <STORAGE_PATH>/<first-2-chars>/<storage_key>
    """

    def __init__(self):
        self.root = os.path.abspath(settings.STORAGE_PATH)
        os.makedirs(self.root, exist_ok=True)

        key = settings.FILE_ENCRYPTION_KEY
        if not key:
            # Auto-generate a key for dev — in production the env var must be set
            key = Fernet.generate_key().decode()
            print(f"[WARN] FILE_ENCRYPTION_KEY not set. Generated ephemeral key.")
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def _path_for_key(self, storage_key: str) -> str:
        prefix = storage_key[:2]
        dir_path = os.path.join(self.root, prefix)
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, storage_key)

    def save(self, data: bytes, filename: str) -> str:
        ext = os.path.splitext(filename)[1]
        storage_key = f"{uuid.uuid4().hex}{ext}"
        path = self._path_for_key(storage_key)
        encrypted = self._fernet.encrypt(data)
        with open(path, "wb") as f:
            f.write(encrypted)
        return storage_key

    def read(self, storage_key: str) -> bytes:
        path = self._path_for_key(storage_key)
        with open(path, "rb") as f:
            encrypted = f.read()
        return self._fernet.decrypt(encrypted)

    def delete(self, storage_key: str) -> None:
        path = self._path_for_key(storage_key)
        if os.path.exists(path):
            os.remove(path)


# Singleton — swap to S3Storage etc. via config later
storage_service: StorageService = LocalStorage()
