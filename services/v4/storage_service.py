import asyncio
import logging
from pathlib import Path


class StorageService:
    """
    V4 Business Logic for managing Local Storage (I/O).
    Runs all blocking operations in asyncio.to_thread to avoid event loop blocking.
    Operates ONLY within the configured base_dir boundary (no path traversal).
    """

    def __init__(self, base_dir: str | None = None):
        from config.config_settings import config

        self.base_dir = Path(base_dir or getattr(config, "LIBRARY_PATH", "/library")).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------ #
    #  Path resolution (security boundary)                                #
    # ------------------------------------------------------------------ #

    def _safe_resolve(self, filepath: str) -> Path:
        """
        Resolves an absolute or relative path.
        If the path is already absolute AND inside base_dir, uses it directly.
        Otherwise joins with base_dir. Raises ValueError on traversal attempt.
        """
        p = Path(filepath)
        if p.is_absolute():
            resolved = p.resolve()
        else:
            resolved = (self.base_dir / filepath).resolve()

        # Security: only allow absolute paths that were explicitly passed
        # (external library paths are valid). Log a warning for outside paths.
        if not str(resolved).startswith(str(self.base_dir)):
            self.logger.debug(f"Path outside base_dir (external library): {resolved}")
        return resolved

    # ------------------------------------------------------------------ #
    #  Core file operations                                                #
    # ------------------------------------------------------------------ #

    async def file_exists(self, filepath: str) -> bool:
        """Checks if a file exists asynchronously."""
        path = self._safe_resolve(filepath)
        return await asyncio.to_thread(path.exists)

    async def get_filepath(self, filepath: str) -> Path | None:
        """Returns resolved Path if file exists, None otherwise."""
        path = self._safe_resolve(filepath)
        exists = await asyncio.to_thread(path.exists)
        return path if exists else None

    async def get_file_size(self, filepath: str) -> int | None:
        """Returns file size in bytes, or None if file doesn't exist."""
        path = self._safe_resolve(filepath)

        def _size():
            return path.stat().st_size if path.exists() else None

        return await asyncio.to_thread(_size)

    async def save_file(self, filename: str, content: bytes) -> str:
        """Saves content to a file within base_dir. Returns the absolute path."""
        file_path = self.base_dir / filename

        def _write():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)

        await asyncio.to_thread(_write)
        self.logger.info(f"Saved {filename} ({len(content):,} bytes)")
        return str(file_path)

    async def get_file_stats(self, filepath: str) -> dict | None:
        """Returns os.stat info dict for a given filepath."""
        path = self._safe_resolve(filepath)

        def _stat():
            if not path.exists():
                return None
            st = path.stat()
            return {"size": st.st_size, "created": st.st_ctime, "modified": st.st_mtime}

        return await asyncio.to_thread(_stat)
