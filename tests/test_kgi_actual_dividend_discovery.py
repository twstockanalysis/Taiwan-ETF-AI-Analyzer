"""凱基投信 ETF 收益分配公告發現測試。"""

import unittest
from unittest.mock import patch

from backend.app.data_sources.kgi_actual_dividend_discovery import (
    discover_kgi_actual_dividend_announcements,
    fetch_kgi_announcement_html,
    normalize_kgi_etf_code,
    parse_kgi_announcement_html,
)


def announcement(title: str, href: str, declared: str) -> str:
    return f"""
    <a href="{href}" name="announcement">
      <span class="AnnouncementNews-time">{declared}</span>
      <span name="announcementName">{title}</span>
      <span>ETF</span><span>配息</span>
    </a>
    """


class TestKgiActualDividendDiscovery(unittest.TestCase):
    def test_code_validation_blocks_form_injection(self) -> None:
        self.assertEqual(normalize_kgi_etf_code(" 00938 "), "00938")
        for value in ("00938&tag=x", "../00938", "00938.pdf", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_kgi_etf_code(value)

    def test_period_after_pdf_is_candidate(self) -> None:
        html = announcement(
            "00938 凱基台灣優選30 ETF基金115年第2次收益分配期後公告",
            "/Upload/Files/ManageUnitContentType2/00938 收益分配期後公告.pdf",
            "2026-05-15",
        )

        result = parse_kgi_announcement_html(
            html_text=html, etf_code="00938"
        )

        self.assertEqual(len(result.candidates), 1)
        candidate = result.candidates[0]
        self.assertEqual(candidate.declared_date.isoformat(), "2026-05-15")
        self.assertEqual(candidate.information_basis, "UNKNOWN")
        self.assertTrue(candidate.document_url.endswith(".pdf"))
        self.assertNotIn(" ", candidate.document_url)

    def test_period_before_and_no_distribution_are_rejected(self) -> None:
        html = "".join(
            [
                announcement(
                    "00938 收益分配期前公告",
                    "/Upload/00938-before.pdf",
                    "2026-08-03",
                ),
                announcement(
                    "00938 不予收益分配公告",
                    "/Upload/00938-none.pdf",
                    "2026-05-02",
                ),
            ]
        )

        result = parse_kgi_announcement_html(
            html_text=html, etf_code="00938"
        )

        self.assertEqual(result.candidates, ())
        self.assertEqual(len(result.rejections), 2)
        self.assertIn("期前", result.rejections[0].reason)
        self.assertIn("不予分配", result.rejections[1].reason)

    def test_other_etf_and_non_pdf_are_rejected(self) -> None:
        html = "".join(
            [
                announcement(
                    "00915 收益分配期後公告",
                    "/Upload/00915-after.pdf",
                    "2026-05-15",
                ),
                announcement(
                    "00938 收益分配期後公告",
                    "/Home/Notice/00938",
                    "2026-05-15",
                ),
            ]
        )

        result = parse_kgi_announcement_html(
            html_text=html, etf_code="00938"
        )

        self.assertEqual(result.candidates, ())
        self.assertEqual(len(result.rejections), 2)

    def test_document_limit_is_bounded(self) -> None:
        with self.assertRaises(ValueError):
            parse_kgi_announcement_html(
                html_text="<div>empty</div>",
                etf_code="00938",
                max_documents=101,
            )

    def test_injected_html_does_not_require_network(self) -> None:
        result = discover_kgi_actual_dividend_announcements(
            etf_code="00938",
            html_text=announcement(
                "00938 收益分配期後公告",
                "/Upload/00938-after.pdf",
                "2026-05-15",
            ),
        )
        self.assertEqual(len(result.candidates), 1)

    def test_network_requires_explicit_permission(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            fetch_kgi_announcement_html(etf_code="00938")

    @patch(
        "backend.app.data_sources.kgi_actual_dividend_discovery.httpx.post"
    )
    def test_fetch_uses_official_bounded_form(self, mock_post) -> None:
        response = mock_post.return_value
        response.url = "https://www.kgifund.com.tw/Home/ArticleVC"
        response.headers = {"content-type": "text/html; charset=utf-8"}
        response.content = b"<div>ok</div>"
        response.text = "<div>ok</div>"

        value = fetch_kgi_announcement_html(
            etf_code="00938", allow_network=True
        )

        self.assertEqual(value, "<div>ok</div>")
        request = mock_post.call_args
        self.assertEqual(
            request.kwargs["data"],
            {"tags": "ETF", "keyword": "00938", "functionId": "1708"},
        )

    @patch(
        "backend.app.data_sources.kgi_actual_dividend_discovery.httpx.post"
    )
    def test_fetch_rejects_external_redirect(self, mock_post) -> None:
        response = mock_post.return_value
        response.url = "https://example.com/result"
        response.headers = {"content-type": "text/html"}
        response.content = b"<div>bad</div>"

        with self.assertRaisesRegex(ValueError, "不在允許網域"):
            fetch_kgi_announcement_html(
                etf_code="00938", allow_network=True
            )


if __name__ == "__main__":
    unittest.main()
