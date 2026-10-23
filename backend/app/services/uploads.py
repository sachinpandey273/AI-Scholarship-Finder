"""Private local-development upload storage with signature validation."""
from __future__ import annotations
import hashlib
import os
import secrets
from pathlib import Path
from fastapi import HTTPException, UploadFile
from ..core.config import Settings

ALLOWED = {
    "application/pdf": (".pdf", lambda header: header.startswith(b"%PDF-")),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (".docx", lambda header: header.startswith(b"PK\x03\x04")),
}

class LocalUploadStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.root = settings.upload_storage_path.resolve()

    async def save(self, upload: UploadFile) -> tuple[str, str, int, str]:
        mime = upload.content_type or ""
        if mime not in ALLOWED:
            raise HTTPException(415, "Only PDF and DOCX uploads are supported")
        content = await upload.read(self.settings.upload_max_bytes + 1)
        if not content or len(content) > self.settings.upload_max_bytes:
            raise HTTPException(413, "Upload exceeds the permitted size")
        suffix, signature = ALLOWED[mime]
        if not signature(content[:8]):
            raise HTTPException(415, "File signature does not match its declared type")
        self.root.mkdir(parents=True, exist_ok=True)
        object_name = f"{secrets.token_urlsafe(24)}{suffix}"
        target = (self.root / object_name).resolve()
        if target.parent != self.root:
            raise HTTPException(400, "Unsafe storage path")
        temp = target.with_suffix(target.suffix + ".tmp")
        temp.write_bytes(content)
        os.replace(temp, target)
        return object_name, hashlib.sha256(content).hexdigest(), len(content), upload.filename or "upload"
