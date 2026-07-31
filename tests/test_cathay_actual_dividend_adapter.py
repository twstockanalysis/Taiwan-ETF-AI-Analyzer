"""國泰實際配息組成公告 Adapter 測試。"""

import unittest
from decimal import Decimal
from pathlib import Path

from backend.app.data_sources.cathay_actual_dividend_adapter import (
    CathayAnnouncementRejected,
    build_cathay_source_document_id,
    parse_cathay_actual_dividend_announcement,
)
from backend.app.data_sources.actual_dividend_source_registry import (
    get_actual_dividend_source,
)
from backend.app.data_sources.official_source_document import (
    validate_official_source_url,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "cathay_actual_dividend_5141.html"
)

SOURCE_URL = (
    "https://www.cathaysite.com.tw/"
    "announcement/5141"
)


class TestCathayActualDividendAdapter(
    unittest.TestCase
):
    """驗證正式語意、日期與所得代碼。"""

    def load_html(self) -> str:
        """讀取經驗證公告 Fixture。"""

        return FIXTURE_PATH.read_text(
            encoding="utf-8"
        )

    def test_actual_announcement_is_parsed(
        self,
    ) -> None:
        """正式公告轉為 M8-4A 標準 Notice。"""

        notice = (
            parse_cathay_actual_dividend_announcement(
                html_text=self.load_html(),
                source_document_url=(
                    SOURCE_URL
                ),
                etf_code="00878",
            )
        )

        self.assertEqual(
            notice.source_document_id,
            "cathay-announcement-5141",
        )

        self.assertEqual(
            notice.source_document_date
            .isoformat(),
            "2023-08-15",
        )

        self.assertEqual(
            notice.ex_dividend_date
            .isoformat(),
            "2023-08-16",
        )

        self.assertEqual(
            notice.record_date.isoformat(),
            "2023-08-22",
        )

        self.assertEqual(
            notice.payment_date.isoformat(),
            "2023-09-11",
        )

        self.assertEqual(
            notice.amount_per_unit,
            Decimal("0.35"),
        )

        component_map = {
            component.component_code: (
                component
            )
            for component in (
                notice.components
            )
        }

        self.assertEqual(
            set(component_map),
            {
                "54C",
                "76W",
            },
        )

        self.assertEqual(
            component_map["76W"]
            .ratio_pct,
            Decimal("97.14"),
        )

        self.assertEqual(
            component_map["54C"]
            .amount_per_unit,
            Decimal("0.01"),
        )

    def test_estimated_marker_is_rejected(
        self,
    ) -> None:
        """公告含預估語意時不得產生 ACTUAL。"""

        html_text = self.load_html().replace(
            "實際配發金額組成如下",
            "預估收益分配組成占比如下",
        )

        with self.assertRaisesRegex(
            CathayAnnouncementRejected,
            "預估語意",
        ):
            parse_cathay_actual_dividend_announcement(
                html_text=html_text,
                source_document_url=(
                    SOURCE_URL
                ),
                etf_code="00878",
            )

    def test_missing_actual_marker_is_rejected(
        self,
    ) -> None:
        """未明確寫實際組成時拒絕。"""

        html_text = self.load_html().replace(
            "實際配發金額組成如下",
            "配發金額組成如下",
        )

        with self.assertRaisesRegex(
            CathayAnnouncementRejected,
            "未明確標示",
        ):
            parse_cathay_actual_dividend_announcement(
                html_text=html_text,
                source_document_url=(
                    SOURCE_URL
                ),
                etf_code="00878",
            )

    def test_document_id_uses_announcement_number(
        self,
    ) -> None:
        """公告編號形成穩定文件 ID。"""

        self.assertEqual(
            build_cathay_source_document_id(
                SOURCE_URL
            ),
            "cathay-announcement-5141",
        )

    def test_non_official_domain_is_rejected(
        self,
    ) -> None:
        """官方 Adapter 不接受其他網域。"""

        source = get_actual_dividend_source(
            "cathay_actual_dividend_announcement"
        )

        with self.assertRaisesRegex(
            ValueError,
            "不在允許網域",
        ):
            validate_official_source_url(
                source,
                (
                    "https://example.com/"
                    "announcement/5141"
                ),
            )


if __name__ == "__main__":
    unittest.main()
