"""喵窩私人入口介面測試。"""

import unittest

from streamlit.testing.v1 import AppTest


class TestFrontendOwnerAccessUI(unittest.TestCase):
    """確認私人入口只在主人主動開啟後顯示。"""

    def test_token_card_is_hidden_until_nest_opens(self) -> None:
        app = AppTest.from_string(
            """
from frontend.owner_access import render_owner_access_trigger
render_owner_access_trigger("http://127.0.0.1:8000")
""",
            default_timeout=10,
        )
        app.run()

        self.assertEqual(len(app.exception), 0)
        self.assertIn("喵窩", [item.label for item in app.button])
        self.assertEqual(len(app.text_input), 0)

        nest_button = next(
            item for item in app.button
            if item.label == "喵窩"
        )
        nest_button.click().run()

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.text_input), 1)
        self.assertEqual(app.text_input[0].label, "喵窩通行碼")
        self.assertIn("進入", [item.label for item in app.button])

        page_text = "\n".join(
            [item.value for item in app.subheader]
            + [item.value for item in app.caption]
        )
        self.assertNotIn("Owner-only 功能", page_text)
        self.assertNotIn("Owner token", page_text)


if __name__ == "__main__":
    unittest.main()
