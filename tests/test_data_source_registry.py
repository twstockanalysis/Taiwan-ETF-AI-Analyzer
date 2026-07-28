"""ETF 資料來源 Registry 測試。"""

import unittest

from backend.app.data_sources.registry import (
    DATA_SOURCES,
    Market,
    get_data_source,
    list_enabled_sources,
)


class TestDataSourceRegistry(unittest.TestCase):
    """測試 ETF 資料來源設定。"""

    def test_source_ids_are_unique(self) -> None:
        """確認資料來源識別碼不重複。"""

        source_ids = [
            source.source_id
            for source in DATA_SOURCES.values()
        ]

        self.assertEqual(
            len(source_ids),
            len(set(source_ids)),
        )

    def test_twse_openapi_exists(self) -> None:
        """確認 TWSE OpenAPI 已登錄。"""

        source = get_data_source(
            "twse_openapi"
        )

        self.assertEqual(
            source.market,
            Market.TWSE,
        )
        self.assertTrue(
            source.allow_legacy_x509
        )
        self.assertIsNotNone(
            source.specification_url
        )

    def test_tpex_openapi_exists(self) -> None:
        """確認 TPEx OpenAPI 已登錄。"""

        source = get_data_source(
            "tpex_openapi"
        )

        self.assertEqual(
            source.market,
            Market.TPEX,
        )
        self.assertTrue(
            source.allow_legacy_x509
        )
        self.assertIsNotNone(
            source.specification_url
        )

    def test_source_id_is_case_insensitive(
        self,
    ) -> None:
        """確認來源識別碼查詢不區分大小寫。"""

        source = get_data_source(
            " TWSE_OPENAPI "
        )

        self.assertEqual(
            source.source_id,
            "twse_openapi",
        )

    def test_unknown_source_raises_error(
        self,
    ) -> None:
        """確認不存在的來源會拋出錯誤。"""

        with self.assertRaises(KeyError):
            get_data_source(
                "unknown"
            )

    def test_only_enabled_sources_are_listed(
        self,
    ) -> None:
        """確認只回傳啟用來源。"""

        sources = list_enabled_sources()

        self.assertTrue(
            all(
                source.enabled
                for source in sources
            )
        )

        self.assertEqual(
            len(sources),
            2,
        )


if __name__ == "__main__":
    unittest.main()