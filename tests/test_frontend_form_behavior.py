"""全站 Streamlit 表單提交行為測試。"""

import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"


class TestFrontendFormBehavior(unittest.TestCase):
    def test_all_forms_disable_enter_to_submit(self) -> None:
        missing: list[str] = []
        form_count = 0

        for path in FRONTEND_ROOT.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if not isinstance(node.func, ast.Attribute) or node.func.attr != "form":
                    continue

                form_count += 1
                keyword = next(
                    (
                        item
                        for item in node.keywords
                        if item.arg == "enter_to_submit"
                    ),
                    None,
                )
                if (
                    keyword is None
                    or not isinstance(keyword.value, ast.Constant)
                    or keyword.value.value is not False
                ):
                    relative = path.relative_to(PROJECT_ROOT)
                    missing.append(f"{relative}:{node.lineno}")

        self.assertGreater(form_count, 0)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
