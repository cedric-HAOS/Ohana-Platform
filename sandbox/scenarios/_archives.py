"""A local directory standing in for the iCloud backup remote (Phase 10)."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ohana_agent.plugins.backup.archive_verifier import RcloneReadError

REMOTE = "icloud:Ohana/Backups"


class DirectoryRemote:
    """Implements the verifier's reader over a directory; can go offline."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.online = True

    def _path(self, remote_path: str) -> Path:
        return self.root / remote_path.removeprefix(REMOTE).lstrip("/")

    def _require_online(self) -> None:
        if not self.online:
            raise RcloneReadError("Invalid global session")

    def list_files(self, remote_path: str) -> list[dict[str, Any]]:
        self._require_online()
        base = self._path(remote_path)
        return [
            {
                "Path": file.relative_to(base).as_posix(),
                "Name": file.name,
                "Size": file.stat().st_size,
                "IsDir": False,
            }
            for file in sorted(base.rglob("*"))
            if file.is_file()
        ]

    def read_small(self, remote_path: str, limit: int = 65536) -> bytes:
        self._require_online()
        return self._path(remote_path).read_bytes()[:limit]

    def stream(self, remote_path: str, *, timeout: float) -> Iterator[bytes]:
        self._require_online()
        with self._path(remote_path).open("rb") as source:
            while chunk := source.read(1024 * 1024):
                yield chunk


def publish_infra(root: Path, backup_id: str, body: bytes, *, lie: bool = False) -> Path:
    folder = root / "infra-01" / backup_id
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / f"{backup_id}.tar.age"
    archive.write_bytes(body)
    (folder / "manifest.json").write_text(
        json.dumps(
            {
                "archive": {
                    "filename": archive.name,
                    "size_bytes": len(body),
                    "sha256": "0" * 64 if lie else hashlib.sha256(body).hexdigest(),
                }
            }
        ),
        encoding="utf-8",
    )
    return archive


def publish_haos(root: Path, target: str, stamp: str, body: bytes) -> Path:
    folder = root / target / stamp[:4] / stamp[4:6]
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / f"{stamp}_ab12cd34.tar"
    archive.write_bytes(body)
    Path(f"{archive}.sha256").write_text(
        f"{hashlib.sha256(body).hexdigest()}  {archive.name}\n", encoding="utf-8"
    )
    return archive


def age_body(size: int = 2 * 1024 * 1024) -> bytes:
    return b"age-encryption.org/v1\n-> X25519 sandbox\n" + os.urandom(size)
