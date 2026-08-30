"""GoodCat 原生 Streamlit 主題測試。"""

import tomllib
import unittest
from pathlib import Path

from frontend.ui.theme import (
    GOODCAT_DARK_PALETTE,
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
        light_theme = theme["light"]

        self.assertEqual(theme["base"], "light")
        self.assertEqual(
            light_theme["backgroundColor"],
            "#F7F7F4",
        )
        self.assertEqual(
            light_theme["textColor"],
            "#343740",
        )
        self.assertEqual(
            light_theme["primaryColor"],
            "#5B5E69",
        )
        self.assertEqual(
            light_theme["borderColor"],
            "#D9DADF",
        )
        self.assertEqual(
            light_theme[
                "secondaryBackgroundColor"
            ],
            "#FFFFFF",
        )
        self.assertEqual(
            light_theme["sidebar"][
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

    def test_goodcat_dark_palette_is_configured(
        self,
    ) -> None:
        with THEME_PATH.open("rb") as file:
            config = tomllib.load(file)

        dark_theme = config["theme"]["dark"]

        self.assertEqual(
            dark_theme["backgroundColor"],
            "#1E1B18",
        )
        self.assertEqual(
            dark_theme[
                "secondaryBackgroundColor"
            ],
            "#2A2724",
        )
        self.assertEqual(
            dark_theme["textColor"],
            "#FDFBF7",
        )
        self.assertEqual(
            dark_theme["primaryColor"],
            "#F59E0B",
        )
        self.assertEqual(
            dark_theme["borderColor"],
            "#3D3732",
        )
        self.assertEqual(
            dark_theme["sidebar"][
                "backgroundColor"
            ],
            "#211E1B",
        )
        self.assertEqual(
            GOODCAT_DARK_PALETTE["canvas"],
            "#1E1B18",
        )
        self.assertEqual(
            GOODCAT_DARK_PALETTE["secondary_text"],
            "#A8A29E",
        )


if __name__ == "__main__":
    unittest.main()
