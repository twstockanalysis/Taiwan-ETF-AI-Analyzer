"""正式配息來源 Registry 測試。"""

import unittest

from backend.app.data_sources.actual_dividend_source_registry import (
    ActualDividendSourceMode,
    SourceRetrievalPolicy,
    get_actual_dividend_source,
    list_verified_actual_dividend_adapters,
)


class TestActualDividendSourceRegistry(
    unittest.TestCase
):
    """驗證正式來源狀態與下載政策。"""

    def test_cathay_adapter_is_verified(
        self,
    ) -> None:
        """國泰公告 Adapter 已列為驗證來源。"""

        source = get_actual_dividend_source(
            "cathay_actual_dividend_announcement"
        )

        self.assertEqual(
            source.mode,
            (
                ActualDividendSourceMode
                .VERIFIED_ADAPTER
            ),
        )

        self.assertEqual(
            source.retrieval_policy,
            (
                SourceRetrievalPolicy
                .EXPLICIT_NETWORK
            ),
        )

        self.assertIn(
            "www.cathaysite.com.tw",
            source.official_domains,
        )
        self.assertIn(
            "cwapi.cathaysite.com.tw",
            source.official_domains,
        )

    def test_twse_estimated_source_is_not_verified(
        self,
    ) -> None:
        """TWSE 預估組成不列為 ACTUAL Adapter。"""

        source = get_actual_dividend_source(
            "twse_etfortune_dividend"
        )

        self.assertEqual(
            source.mode,
            (
                ActualDividendSourceMode
                .DISCOVERY_ONLY
            ),
        )

        verified_ids = {
            item.source_id
            for item in (
                list_verified_actual_dividend_adapters()
            )
        }

        self.assertNotIn(
            source.source_id,
            verified_ids,
        )


if __name__ == "__main__":
    unittest.main()
