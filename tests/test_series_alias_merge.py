import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from models.library import LocalBook, SeriesAlias, SeriesMetadata
from services.library_service import LibraryService
from services.scanner.series_scanner import SeriesScanner


class TestSeriesAliasAndMerge(unittest.TestCase):
    def test_series_alias_instantiation(self):
        alias = SeriesAlias(series_id="test_hash_123", alias="Arifureta LN")
        self.assertEqual(alias.series_id, "test_hash_123")
        self.assertEqual(alias.alias, "Arifureta LN")

    def test_sync_series_aliases(self):
        async def _run():
            session = MagicMock()
            mock_res = MagicMock()
            mock_res.scalar_one_or_none.return_value = None
            session.execute = AsyncMock(return_value=mock_res)
            session.flush = AsyncMock()

            series = SeriesMetadata(
                id="hash_1",
                series_name="Main Series",
                series_spanish="Serie Principal",
                series_english="Main Series EN",
                name="Main Series Romaji",
            )
            candidate_titles = {"Main Series Alt", "Main Series Custom"}

            await SeriesScanner.sync_series_aliases(session, series, candidate_titles)
            self.assertTrue(session.add.called)

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
