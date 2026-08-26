"""GoodCat 原生 Streamlit 主題測試。"""

import tomllib
import unittest
from pathlib import Path

from frontend.ui.theme import (
    GOODCAT_PALETTE,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
THEME_PATH = (
    PROJECT_ROOT
    / ".streamlit"
    / "config.toml"
)


class TestFrontendNativeTheme(unittest.TestCase):
    """驗證 V4 淺色品牌 Token。"""

    def test_goodcat_light_palette_is_configured(
        self,
    ) -> None:
        with THEME_PATH.open("rb") as file:
            config = tomllib.load(file)

        theme = config["theme"]

        self.assertEqual(theme["base"], "light")
        self.assertEqual(
            theme["backgroundColor"],
            "#F7F7F4",
        )
        self.assertEqual(
            theme["textColor"],
            "#343740",
        )
        self.assertEqual(
            theme["primaryColor"],
            "#5B5E69",
        )
        self.assertEqual(
            theme["borderColor"],
            "#D9DADF",
        )
        self.assertEqual(
            theme[
                "secondaryBackgroundColor"
            ],
            "#FFFFFF",
        )
        self.assertEqual(
            theme["sidebar"][
                "backgroundColor"
            ],
            "#EEEFEF",
        )

        self.assertEqual(
            GOODCAT_PALETTE["soft_pink"],
            "#DFA5B4",
        )
        self.assertEqual(
            GOODCAT_PALETTE[
                "secondary_text"
            ],
            "#6F737C",
        )


if __name__ == "__main__":
    unittest.main()
