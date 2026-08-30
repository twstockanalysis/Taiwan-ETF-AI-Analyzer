"""GoodCat 品牌素材與共用元件測試。"""

import unittest
from unittest.mock import patch

from PIL import Image

from frontend.ui.goodcat import (
    GOODCAT_PRESENTATIONS,
    GoodCatState,
    get_goodcat_presentation,
    render_beginner_card,
    render_goodcat_companion,
)


class TestFrontendGoodCat(unittest.TestCase):
    """驗證角色狀態、透明素材與文字替代。"""

    def test_all_states_have_transparent_assets(
        self,
    ) -> None:
        self.assertEqual(
            set(GOODCAT_PRESENTATIONS),
            set(GoodCatState),
        )

        for presentation in (
            GOODCAT_PRESENTATIONS.values()
        ):
            self.assertTrue(
                presentation.asset_path.is_file()
            )
            self.assertTrue(
                presentation.accessibility_text
            )

            with Image.open(
                presentation.asset_path
            ) as image:
                self.assertEqual(
                    image.format,
                    "PNG",
                )
                self.assertIn("A", image.mode)
                alpha = image.getchannel("A")
                self.assertEqual(
                    alpha.getextrema()[0],
                    0,
                )

    def test_state_lookup_accepts_lowercase(
        self,
    ) -> None:
        presentation = (
            get_goodcat_presentation(
                "ready"
            )
        )

        self.assertEqual(
            presentation.state,
            GoodCatState.READY,
        )

    def test_attentive_state_uses_alert_v3_asset(
        self,
    ) -> None:
        attentive = GOODCAT_PRESENTATIONS[
            GoodCatState.ATTENTIVE
        ]
        idle = GOODCAT_PRESENTATIONS[
            GoodCatState.IDLE
        ]

        self.assertEqual(
            attentive.asset_path.name,
            "goodcat-attentive-v3.png",
        )
        self.assertEqual(attentive.label, "正在等主人")
        self.assertEqual(
            idle.asset_path.name,
            "goodcat-idle.png",
        )

    def test_unknown_state_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            get_goodcat_presentation(
                "sleeping"
            )

    @patch(
        "frontend.ui.goodcat.st.markdown"
    )
    @patch(
        "frontend.ui.goodcat.st.caption"
    )
    @patch(
        "frontend.ui.goodcat.st.image"
    )
    @patch(
        "frontend.ui.goodcat.st.container"
    )
    def test_companion_uses_clean_visible_copy(
        self,
        mock_container,
        mock_image,
        mock_caption,
        mock_markdown,
    ) -> None:
        render_goodcat_companion(
            GoodCatState.CAUTION,
            "資料不足，先看看原因。",
            key="test-goodcat",
        )

        self.assertGreaterEqual(
            mock_container.call_count,
            2,
        )
        image_call = mock_image.call_args
        self.assertIsNone(
            image_call.kwargs["caption"]
        )
        mock_caption.assert_called_once_with(
            "先注意這件事"
        )
        mock_markdown.assert_called_once_with(
            "**資料不足，先看看原因。**"
        )

    @patch(
        "frontend.ui.goodcat.st.caption"
    )
    @patch(
        "frontend.ui.goodcat.st.write"
    )
    @patch(
        "frontend.ui.goodcat.st.subheader"
    )
    @patch(
        "frontend.ui.goodcat.st.container"
    )
    def test_beginner_card_uses_native_elements(
        self,
        mock_container,
        mock_subheader,
        mock_write,
        mock_caption,
    ) -> None:
        render_beginner_card(
            "先看每月目標",
            "輸入每個目標月想領多少。",
            caption="金額可以之後再調整。",
            icon=":material/calendar_month:",
        )

        mock_container.assert_called_once_with(
            border=True,
            key=None,
        )
        mock_subheader.assert_called_once_with(
            ":material/calendar_month: "
            "先看每月目標"
        )
        mock_write.assert_called_once_with(
            "輸入每個目標月想領多少。"
        )
        mock_caption.assert_called_once_with(
            "金額可以之後再調整。"
        )


if __name__ == "__main__":
    unittest.main()
