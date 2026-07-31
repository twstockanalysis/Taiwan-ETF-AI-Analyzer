"""Streamlit 共用狀態元件測試。"""

import unittest
from unittest.mock import patch

from frontend.ui.states import (
    render_api_error,
    render_empty_state,
)


class TestFrontendStates(
    unittest.TestCase
):
    """驗證共用空白與錯誤狀態。"""

    @patch(
        "frontend.ui.states.st.caption"
    )
    @patch(
        "frontend.ui.states.st.info"
    )
    def test_empty_state_can_include_hint(
        self,
        mock_info,
        mock_caption,
    ) -> None:
        """確認空白狀態與操作提示一致。"""

        render_empty_state(
            "查無資料",
            hint="調整查詢條件",
        )

        mock_info.assert_called_once_with(
            "查無資料"
        )

        mock_caption.assert_called_once_with(
            "調整查詢條件"
        )

    @patch(
        "frontend.ui.states.st.info"
    )
    @patch(
        "frontend.ui.states.st.code"
    )
    @patch(
        "frontend.ui.states.st.error"
    )
    def test_api_error_keeps_detail(
        self,
        mock_error,
        mock_code,
        mock_info,
    ) -> None:
        """確認 API 錯誤保留可診斷內容。"""

        render_api_error(
            "載入失敗",
            RuntimeError("connection failed"),
            hint="確認 FastAPI",
        )

        mock_error.assert_called_once_with(
            "載入失敗"
        )

        mock_code.assert_called_once_with(
            "connection failed",
            language=None,
        )

        mock_info.assert_called_once_with(
            "確認 FastAPI"
        )


if __name__ == "__main__":
    unittest.main()
