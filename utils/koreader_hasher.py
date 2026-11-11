import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def calculate_koreader_fast_digest(file_path: Path | str) -> str:
    """Calcula el partial MD5 idéntico al Document:fastDigest() de KOReader.

    Muestrea bloques de 1024 bytes en posiciones exponenciales:
    - i = -1: offset 256 (1024 >> 2)
    - i = 0..10: offset 1024 << (2 * i)  (1024, 4096, 16384, 65536, ...)

    Retorna un string hexadecimal en minúsculas de 32 caracteres.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

    file_size = path.stat().st_size
    step, size = 1024, 1024
    md5 = hashlib.md5()

    with path.open("rb") as f:
        for i in range(-1, 11):
            if i == -1:
                offset = step >> 2  # 256
            else:
                offset = step << (2 * i)

            if offset >= file_size:
                break

            f.seek(offset)
            sample = f.read(size)
            if not sample:
                break
            md5.update(sample)

    return md5.hexdigest()

