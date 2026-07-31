"""Streamlit 共用互動元件測試。"""

import unittest
from unittest.mock import (
    MagicMock,
    patch,
)

from frontend.ui.components import (
    render_etf_detail_links,
    render_pagination_controls,
)


class TestFrontendComponents(
    unittest.TestCase
):
    """驗證共用資料列與分頁元件。"""

    @patch(
        "frontend.ui.components.st.page_link"
    )
    @patch(
        "frontend.ui.components.st.caption"
    )
    def test_etf_detail_links_preserve_source_state(
        self,
        mock_caption,
        mock_page_link,
    ) -> None:
        """確認共用資料列保留來源頁 URL 狀態。"""

        render_etf_detail_links(
            [
                {
                    "code": "0050",
                    "name": "元大台灣50",
                },
            ],
            caption="欄位說明",
            label_builder=(
                lambda item: (
                    f"{item['code']} "
                    f"{item['name']}"
                )
            ),
            code_field="code",
            name_field="name",
            source="etf-search",
            source_query_params={
                "keyword": "元大",
                "page": "2",
            },
        )

        mock_caption.assert_called_once_with(
            "欄位說明"
        )

        mock_page_link.assert_called_once()

        call = mock_page_link.call_args

        self.assertEqual(
            call.args[0],
            "page_scripts/etf_detail_page.py",
        )

        self.assertEqual(
            call.kwargs["width"],
            "stretch",
        )

        self.assertEqual(
            call.kwargs["query_params"],
            {
                "code": "0050",
                "from": "etf-search",
                "keyword": "元大",
                "page": "2",
            },
        )

    @patch(
        "frontend.ui.components.st.write"
    )
    @patch(
        "frontend.ui.components.st.button"
    )
    @patch(
        "frontend.ui.components.st.columns"
    )
    def test_pagination_returns_previous_action(
        self,
        mock_columns,
        mock_button,
        mock_write,
    ) -> None:
        """確認分頁元件只回傳使用者操作。"""

        columns = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
        ]

        mock_columns.return_value = columns
        mock_button.side_effect = [
            True,
            False,
        ]

        action = render_pagination_controls(
            current_page=2,
            total_pages=5,
            previous_key="previous",
            next_key="next",
        )

        self.assertEqual(
            action,
            "previous",
        )

        mock_write.assert_called_once_with(
            "第 2 頁，共 5 頁"
        )

        self.assertEqual(
            mock_button.call_args_list[
                0
            ].kwargs["disabled"],
            False,
        )

        self.assertEqual(
            mock_button.call_args_list[
                1
            ].kwargs["disabled"],
            False,
        )

    def test_pagination_rejects_invalid_pages(
        self,
    ) -> None:
        """確認非法頁次不會進入 Streamlit 繪製。"""

        with self.assertRaises(
            ValueError
        ):
            render_pagination_controls(
                current_page=0,
                total_pages=1,
                previous_key="previous",
                next_key="next",
            )


if __name__ == "__main__":
    unittest.main()
