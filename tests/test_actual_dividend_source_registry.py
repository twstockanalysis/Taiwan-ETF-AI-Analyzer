"""正式配息來源 Registry 測試。"""

import unittest

from backend.app.data_sources.actual_dividend_source_registry import (
    ActualDividendSourceMode,
    SourceDiscoveryKind,
    SourceRetrievalPolicy,
    TWSE_ETF_ISSUERS,
    get_missing_etf_issuer_keys,
    get_actual_dividend_source,
    list_etf_issuer_sources,
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

    def test_multi_issuer_discovery_capabilities_are_explicit(self) -> None:
        expected = {
            "cathay_actual_dividend_announcement": (
                SourceDiscoveryKind.JSON_API
            ),
            "ctbc_latest_etf_dividend_pdf": (
                SourceDiscoveryKind.DETERMINISTIC_URL
            ),
            "kgi_etf_dividend_announcement": (
                SourceDiscoveryKind.HTML_LIST
            ),
            "upam_etf_dividend_document": (
                SourceDiscoveryKind.HTML_LIST
            ),
            "franklin_etf_dividend_document": (
                SourceDiscoveryKind.HTML_LIST
            ),
            "jpmorgan_etf_dividend_document": (
                SourceDiscoveryKind.HTML_LIST
            ),
            "taishin_etf_dividend_document": (
                SourceDiscoveryKind.HTML_LIST
            ),
            "uob_etf_dividend_document": (
                SourceDiscoveryKind.HTML_LIST
            ),
            "alliancebernstein_etf_dividend_document": (
                SourceDiscoveryKind.JSON_API
            ),
        }

        for source_id, discovery_kind in expected.items():
            with self.subTest(source_id=source_id):
                source = get_actual_dividend_source(source_id)
                self.assertEqual(source.discovery_kind, discovery_kind)
                self.assertEqual(
                    source.retrieval_policy,
                    SourceRetrievalPolicy.EXPLICIT_NETWORK,
                )

    def test_unverified_issuers_do_not_become_verified_adapters(self) -> None:
        verified_ids = {
            item.source_id
            for item in list_verified_actual_dividend_adapters()
        }

        self.assertNotIn("ctbc_latest_etf_dividend_pdf", verified_ids)
        self.assertNotIn("kgi_etf_dividend_announcement", verified_ids)
        self.assertNotIn("upam_etf_dividend_document", verified_ids)

    def test_every_twse_etf_issuer_has_one_source_record(self) -> None:
        sources = list_etf_issuer_sources()

        self.assertEqual(get_missing_etf_issuer_keys(), ())
        self.assertEqual(len(TWSE_ETF_ISSUERS), 23)
        self.assertEqual(len(sources), len(TWSE_ETF_ISSUERS))
        self.assertEqual(
            {source.issuer_key for source in sources},
            set(TWSE_ETF_ISSUERS),
        )

    def test_pending_issuer_sources_are_not_actual_adapters(self) -> None:
        verified_keys = {
            source.issuer_key
            for source in list_verified_actual_dividend_adapters()
        }

        self.assertEqual(verified_keys, {"cathay"})

        for source in list_etf_issuer_sources():
            with self.subTest(issuer_key=source.issuer_key):
                self.assertEqual(
                    source.retrieval_policy,
                    SourceRetrievalPolicy.EXPLICIT_NETWORK,
                )
                if source.discovery_kind == SourceDiscoveryKind.PENDING_VERIFICATION:
                    self.assertEqual(
                        source.mode,
                        ActualDividendSourceMode.DISCOVERY_ONLY,
                    )

    def test_landing_page_kind_is_distinct_from_verified_discovery(self) -> None:
        self.assertNotEqual(
            SourceDiscoveryKind.OFFICIAL_LANDING_PAGE,
            SourceDiscoveryKind.HTML_LIST,
        )

    def test_no_issuer_remains_pending_without_official_entrypoint(self) -> None:
        pending = {
            source.issuer_key
            for source in list_etf_issuer_sources()
            if source.discovery_kind == SourceDiscoveryKind.PENDING_VERIFICATION
        }
        landing_pages = {
            source.issuer_key
            for source in list_etf_issuer_sources()
            if source.discovery_kind == SourceDiscoveryKind.OFFICIAL_LANDING_PAGE
        }

        self.assertEqual(pending, set())
        self.assertEqual(len(landing_pages), 12)


if __name__ == "__main__":
    unittest.main()
