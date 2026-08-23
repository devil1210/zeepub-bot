"""
Tests unitarios para el flujo de subida de EPUBs (UploadService, UploadRoutes, UploadBook).
"""

import io
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile

from models.library import UploadBook
from repositories.upload_repository import upload_repo
from services.upload_service import upload_service


def create_minimal_epub_bytes(title="Test Book", author="Test Author") -> bytes:
    """Genera bytes de un archivo EPUB mínimo y válido en memoria."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
        )
        z.writestr(
            "OEBPS/content.opf",
            f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>{title}</dc:title>
    <dc:creator opf:role="aut">{author}</dc:creator>
    <dc:language>es</dc:language>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
  </manifest>
  <spine toc="ncx">
  </spine>
</package>""",
        )
    return buf.getvalue()


@pytest.mark.asyncio
async def test_validate_epub_structure(tmp_path: Path):
    """Verifica que _validate_epub_structure reconozca EPUBs válidos y rechace inválidos."""
    # 1. Archivo válido
    valid_epub = tmp_path / "valid.epub"
    valid_epub.write_bytes(create_minimal_epub_bytes())
    assert await upload_service._validate_epub_structure(valid_epub) is True

    # 2. Archivo corrupto / texto plano
    corrupt_file = tmp_path / "corrupt.epub"
    corrupt_file.write_text("not a zip file content")
    assert await upload_service._validate_epub_structure(corrupt_file) is False

    # 3. Archivo vacío
    empty_file = tmp_path / "empty.epub"
    empty_file.touch()
    assert await upload_service._validate_epub_structure(empty_file) is False


@pytest.mark.asyncio
async def test_upload_book_model_and_repository():
    """Verifica que el modelo UploadBook soporte telegram_id, user_id y upload_metadata."""
    meta = {
        "title": "Overlord",
        "author": "Kugane Maruyama",
        "series": "Overlord",
        "volume": 1.0,
        "book_hash": "hash123",
        "series_hash": "shash123",
    }
    record = UploadBook(
        telegram_id=123456789,
        original_filename="Overlord_01.epub",
        temp_filepath="/tmp/test.epub",
        title="Overlord",
        series="Overlord",
        volume=1.0,
        book_hash="hash123",
        upload_metadata=meta,
    )

    # Verificar hybrid property
    assert record.telegram_id == 123456789
    assert record.user_id == 123456789
    record.user_id = 987654321
    assert record.telegram_id == 987654321
    assert record.upload_metadata == meta


@pytest.mark.asyncio
async def test_analyze_epub_flow(tmp_path: Path):
    """Verifica el flujo completo de análisis de EPUB con mocks de persistencia."""
    epub_file = tmp_path / "test_book.epub"
    epub_file.write_bytes(create_minimal_epub_bytes("Test Series V01", "Author Name"))

    mock_record = MagicMock()
    mock_record.id = 42

    with (
        patch(
            "services.upload_service.enrich_metadata_from_epub",
            new=AsyncMock(
                return_value={
                    "titulo_serie": "Test Series",
                    "titulo_volumen": "Test Series V01",
                    "autor": "Author Name",
                    "volume_index": "01",
                    "generos": ["Fantasía"],
                    "demografia": ["Shonen"],
                }
            ),
        ),
        patch.object(
            upload_repo, "create_upload_record", new=AsyncMock(return_value=mock_record)
        ),
        patch(
            "services.upload_service.book_repo.get_by_hash",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "services.upload_service.book_repo.get_by_series_and_volume",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "repositories.series_repository.series_repo.find_by_title_or_alias",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "services.upload_service.book_repo.get_one_by_attr",
            new=AsyncMock(return_value=None),
        ),
        patch("services.upload_service.get_setting", return_value="false"),
        patch.object(
            upload_service,
            "_get_library_base",
            new=AsyncMock(return_value=Path("/library")),
        ),
    ):
        metadata = await upload_service.analyze_epub(epub_file, "test_book.epub", 12345)

        assert metadata is not None
        assert metadata["title"] == "Test Series V01"
        assert metadata["author"] == "Author Name"
        assert metadata["upload_id"] == 42
        assert metadata["identity_match"] is None
        assert "suggested_path" in metadata
        assert metadata["suggested_path"].endswith(".epub")


@pytest.mark.asyncio
async def test_upload_routes_response_contract(tmp_path: Path):
    """Verifica que upload_epub y upload_epub_bulk devuelvan la estructura esperada por el frontend Web."""
    from api.routes.upload_routes import UploadRoutes

    routes = UploadRoutes()
    epub_bytes = create_minimal_epub_bytes("Re:Zero", "Tappei Nagatsuki")

    mock_metadata = {
        "title": "Re:Zero 01",
        "author": "Tappei Nagatsuki",
        "series": "Re:Zero",
        "volume": 1.0,
        "suggested_path": "Re_Zero/Re_Zero - V01.epub",
        "upload_id": 99,
        "book_hash": "hash_rezero_01",
    }

    # Mock Request and UploadFile
    mock_request = MagicMock()
    user_data = {"user_id": 12345, "role": "admin", "can_upload_epub": True}

    upload_file = UploadFile(filename="ReZero_01.epub", file=io.BytesIO(epub_bytes))

    with patch(
        "services.upload_service.upload_service.analyze_epub",
        new=AsyncMock(return_value=mock_metadata),
    ):
        # 1. Single upload
        res = await routes.upload_epub(mock_request, upload_file, user_data)
        assert res["success"] is True
        assert res["upload_id"] == "99"
        assert res["metadata"] == mock_metadata

        # 2. Bulk upload
        bulk_files = [
            UploadFile(filename="ReZero_01.epub", file=io.BytesIO(epub_bytes))
        ]
        bulk_res = await routes.upload_epub_bulk(mock_request, bulk_files, user_data)
        assert isinstance(bulk_res, list)
        assert len(bulk_res) == 1
        assert bulk_res[0]["success"] is True
        assert bulk_res[0]["upload_id"] == "99"
        assert bulk_res[0]["metadata"] == mock_metadata


@pytest.mark.asyncio
async def test_analyze_epub_duplicate_detection(tmp_path: Path):
    """Verifica que un libro duplicado sea detectado y marcado en metadata['identity_match']."""
    epub_file = tmp_path / "dup_book.epub"
    epub_file.write_bytes(create_minimal_epub_bytes("Existing Book", "Author"))

    existing_book_mock = MagicMock()
    existing_book_mock.id = "hash_existing"
    existing_book_mock.filepath = "/library/Existing/Existing.epub"

    mock_record = MagicMock()
    mock_record.id = 55

    with (
        patch(
            "services.upload_service.enrich_metadata_from_epub",
            new=AsyncMock(
                return_value={"titulo_volumen": "Existing Book", "autor": "Author"}
            ),
        ),
        patch.object(
            upload_repo, "create_upload_record", new=AsyncMock(return_value=mock_record)
        ),
        patch(
            "services.upload_service.book_repo.get_by_hash",
            new=AsyncMock(return_value=existing_book_mock),
        ),
        patch(
            "services.upload_service.book_repo.get_one_by_attr",
            new=AsyncMock(return_value=None),
        ),
        patch("services.upload_service.get_setting", return_value="false"),
        patch.object(
            upload_service,
            "_get_library_base",
            new=AsyncMock(return_value=Path("/library")),
        ),
    ):
        metadata = await upload_service.analyze_epub(epub_file, "dup_book.epub", 12345)

        assert metadata is not None
        assert metadata["identity_match"] is not None
        assert metadata["identity_match"]["exists"] is True
        assert metadata["identity_match"]["path"] == "/library/Existing/Existing.epub"


@pytest.mark.asyncio
async def test_finalize_upload_local(tmp_path: Path):
    """Verifica que finalize_upload mueva el archivo al directorio de destino y limpie el registro temporal."""
    temp_epub = tmp_path / "temp_upload.epub"
    temp_epub.write_bytes(create_minimal_epub_bytes("Finalized Book", "Author"))

    lib_dir = tmp_path / "library"
    lib_dir.mkdir()

    meta = {
        "upload_id": 77,
        "title": "Finalized Book",
        "book_hash": "hash_fin",
        "book_type": "NL",
        "is_uncensored": 0,
        "color_mode": "bw",
        "description": "Test description",
    }

    with (
        patch.object(
            upload_service, "_get_library_base", new=AsyncMock(return_value=lib_dir)
        ),
        patch(
            "services.nextcloud_service.NextcloudService.is_active",
            new_callable=MagicMock(return_value=False),
        ),
        patch(
            "services.scanner_service.ScannerService.sync_path",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "services.upload_service.book_repo.get_by_filepath",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            upload_repo, "delete_upload_record", new=AsyncMock(return_value=True)
        ),
        patch("services.sync_service.SyncService.trigger_auto_sync", new=MagicMock()),
    ):
        success = await upload_service.finalize_upload(
            temp_epub, "Series_Name/Book_V01.epub", meta
        )

        assert success is True
        dest_file = lib_dir / "Series_Name/Book_V01.epub"
        assert dest_file.exists()
        assert not temp_epub.exists()


@pytest.mark.asyncio
async def test_duplicate_detection_by_uuid(tmp_path: Path):
    """Verifica detección de duplicados cuando el EPUB contiene un UUID existente."""
    epub_file = tmp_path / "uuid_book.epub"
    epub_file.write_bytes(create_minimal_epub_bytes("Book With UUID", "Author"))

    mock_record = MagicMock()
    mock_record.id = 88

    existing_book_mock = MagicMock()
    existing_book_mock.id = "uuid_hash_123"
    existing_book_mock.filepath = "/library/Series/Book.epub"
    existing_book_mock.series_info = None
    existing_book_mock.volume = 1.0

    with (
        patch(
            "services.upload_service.enrich_metadata_from_epub",
            new=AsyncMock(
                return_value={
                    "titulo_volumen": "Book With UUID",
                    "autor": "Author",
                    "uuid": "12345678-1234-5678-1234-567812345678",
                }
            ),
        ),
        patch.object(
            upload_repo, "create_upload_record", new=AsyncMock(return_value=mock_record)
        ),
        patch(
            "services.upload_service.book_repo.get_by_hash",
            new=AsyncMock(return_value=existing_book_mock),
        ),
        patch(
            "services.upload_service.book_repo.get_by_series_and_volume",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "services.upload_service.book_repo.get_one_by_attr",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "repositories.series_repository.series_repo.find_by_title_or_alias",
            new=AsyncMock(return_value=None),
        ),
        patch("services.upload_service.get_setting", return_value="false"),
        patch.object(
            upload_service,
            "_get_library_base",
            new=AsyncMock(return_value=Path("/library")),
        ),
    ):
        metadata = await upload_service.analyze_epub(epub_file, "uuid_book.epub", 12345)

        assert metadata is not None
        assert metadata["identity_match"] is not None
        assert metadata["identity_match"]["exists"] is True
        assert metadata["identity_match"]["path"] == "/library/Series/Book.epub"


@pytest.mark.asyncio
async def test_duplicate_detection_by_series_and_volume(tmp_path: Path):
    """Verifica detección de duplicados cuando el volumen ya existe para la serie."""
    epub_file = tmp_path / "series_vol_book.epub"
    epub_file.write_bytes(create_minimal_epub_bytes("Baka V01", "Kenji Inoue"))

    mock_record = MagicMock()
    mock_record.id = 99

    existing_book_mock = MagicMock()
    existing_book_mock.id = "hash_v01"
    existing_book_mock.filepath = "/library/Baka/V01.epub"
    existing_book_mock.series_info = MagicMock()
    existing_book_mock.series_info.name = "Baka to Test"
    existing_book_mock.volume = 1.0

    with (
        patch(
            "services.upload_service.enrich_metadata_from_epub",
            new=AsyncMock(
                return_value={
                    "titulo_serie": "Baka to Test",
                    "titulo_volumen": "Baka to Test V01",
                    "autor": "Kenji Inoue",
                    "volume_index": 1.0,
                }
            ),
        ),
        patch.object(
            upload_repo, "create_upload_record", new=AsyncMock(return_value=mock_record)
        ),
        patch(
            "services.upload_service.book_repo.get_by_hash",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "services.upload_service.book_repo.get_by_series_and_volume",
            new=AsyncMock(return_value=existing_book_mock),
        ),
        patch(
            "services.upload_service.book_repo.get_one_by_attr",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "repositories.series_repository.series_repo.find_by_title_or_alias",
            new=AsyncMock(return_value=None),
        ),
        patch("services.upload_service.get_setting", return_value="false"),
        patch.object(
            upload_service,
            "_get_library_base",
            new=AsyncMock(return_value=Path("/library")),
        ),
    ):
        metadata = await upload_service.analyze_epub(epub_file, "series_vol_book.epub", 12345)

        assert metadata is not None
        assert metadata["identity_match"] is not None
        assert metadata["identity_match"]["exists"] is True
        assert metadata["identity_match"]["volume"] == 1.0
        assert metadata["identity_match"]["series"] == "Baka to Test"
