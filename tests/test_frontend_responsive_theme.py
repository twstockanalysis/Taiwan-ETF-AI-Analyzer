"""Streamlit 響應式字體設定測試。"""

import unittest
from unittest.mock import patch

from frontend.ui.theme import (
    GLOBAL_STYLE_MARKER,
    GLOBAL_STYLES,
    apply_global_styles,
)


class TestFrontendResponsiveTheme(
    unittest.TestCase
):
    """測試全站可讀性 CSS 契約。"""

    def test_styles_prevent_metric_ellipsis(
        self,
    ) -> None:
        """確認 Metric 數值不使用省略號截斷。"""

        self.assertIn(
            GLOBAL_STYLE_MARKER,
            GLOBAL_STYLES,
        )
        self.assertIn(
            '[data-testid="stMetricValue"]',
            GLOBAL_STYLES,
        )
        self.assertIn(
            "text-overflow: clip",
            GLOBAL_STYLES,
        )
        self.assertIn(
            "font-size: 0.9rem",
            GLOBAL_STYLES,
        )

    @patch(
        "frontend.ui.theme.st.markdown"
    )
    def test_styles_use_safe_streamlit_injection(
        self,
        mock_markdown,
    ) -> None:
        """確認 CSS 由單一函式注入。"""

        apply_global_styles()

        mock_markdown.assert_called_once_with(
            GLOBAL_STYLES,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    unittest.main()
