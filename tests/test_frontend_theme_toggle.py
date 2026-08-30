"""GoodCat 白天與深夜模式切換測試。"""

import unittest
from unittest.mock import patch

from frontend.ui.theme_toggle import (
    THEME_TOGGLE_CSS,
    THEME_TOGGLE_JS,
    render_theme_toggle,
)


class TestFrontendThemeToggle(unittest.TestCase):
    def test_component_uses_streamlit_v2_and_native_theme_menu(self) -> None:
        self.assertIn("export default function", THEME_TOGGLE_JS)
        self.assertIn("stMainMenuButton", THEME_TOGGLE_JS)
        self.assertIn("stMainMenuItem-theme-", THEME_TOGGLE_JS)
        self.assertNotIn("window.Streamlit", THEME_TOGGLE_JS)
        self.assertNotIn("postMessage", THEME_TOGGLE_JS)
        self.assertIn("var(--st-text-color)", THEME_TOGGLE_CSS)
        self.assertIn("var(--st-primary-color)", THEME_TOGGLE_CSS)

        self.assertIn("pageIsDark", THEME_TOGGLE_JS)
        self.assertIn('setTriggerValue("changed", nextTarget)', THEME_TOGGLE_JS)
        self.assertIn(
            'pageIsDark() ? "Light" : "Dark"',
            THEME_TOGGLE_JS,
        )

    @patch("frontend.ui.theme_toggle._THEME_TOGGLE")
    def test_toggle_mounts_as_content_width_button(
        self,
        mock_component,
    ) -> None:
        render_theme_toggle()

        self.assertEqual(
            mock_component.call_args.kwargs["width"],
            "content",
        )
        self.assertEqual(
            mock_component.call_args.kwargs["height"],
            "content",
        )
        self.assertTrue(
            callable(
                mock_component.call_args.kwargs["on_changed_change"]
            )
        )


if __name__ == "__main__":
    unittest.main()
