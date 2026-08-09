"""前端 API Client 模組化架構契約測試。"""

import ast
import importlib
import unittest
from pathlib import Path

import frontend.api_client as api_client
from frontend.api import transport


PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_PACKAGE_PATH = PROJECT_ROOT / "frontend" / "api"
API_CLIENT_PATH = PROJECT_ROOT / "frontend" / "api_client.py"

EXPECTED_API_MODULES = {
    "comparison.py",
    "data_profile.py",
    "decision_profile.py",
    "dividend_quality.py",
    "dividends.py",
    "errors.py",
    "etfs.py",
    "health.py",
    "normalizers.py",
    "performance.py",
    "system_overview.py",
    "transport.py",
    "validators.py",
}


def parse_module(path: Path) -> ast.Module:
    """以 UTF-8-sig 解析 Python 模組。"""

    return ast.parse(
        path.read_text(encoding="utf-8-sig"),
        filename=str(path),
    )


class TestFrontendAPIArchitecture(unittest.TestCase):
    """防止前端 API Client 回退為單體模組。"""

    def test_expected_api_modules_exist(self) -> None:
        """所有已抽離的 API 模組都必須存在。"""

        module_names = {
            path.name
            for path in API_PACKAGE_PATH.glob("*.py")
        }

        self.assertTrue(
            EXPECTED_API_MODULES.issubset(module_names)
        )

    def test_api_client_is_import_only_facade(self) -> None:
        """相容 façade 不得重新累積實作。"""

        module = parse_module(API_CLIENT_PATH)
        disallowed_nodes = (
            ast.Assign,
            ast.AnnAssign,
            ast.AugAssign,
            ast.ClassDef,
            ast.FunctionDef,
            ast.AsyncFunctionDef,
        )

        self.assertFalse(
            any(
                isinstance(node, disallowed_nodes)
                for node in module.body
            )
        )

        for node in module.body:
            if isinstance(node, ast.ImportFrom):
                self.assertIsNotNone(node.module)
                self.assertTrue(
                    node.module.startswith("frontend.api.")
                )
            else:
                self.assertIsInstance(
                    node,
                    (ast.Expr, ast.Import),
                )

    def test_facade_reexports_source_objects(self) -> None:
        """舊入口必須直接重匯出來源模組物件。"""

        module = parse_module(API_CLIENT_PATH)

        for node in module.body:
            if not isinstance(node, ast.ImportFrom):
                continue

            source_module = importlib.import_module(node.module)

            for imported_name in node.names:
                public_name = (
                    imported_name.asname
                    or imported_name.name
                )

                with self.subTest(
                    module=node.module,
                    name=public_name,
                ):
                    self.assertIs(
                        getattr(api_client, public_name),
                        getattr(
                            source_module,
                            imported_name.name,
                        ),
                    )

    def test_api_modules_do_not_import_facade(self) -> None:
        """內部模組不得反向依賴相容 façade。"""

        for path in API_PACKAGE_PATH.glob("*.py"):
            module = parse_module(path)

            for node in ast.walk(module):
                imported_module = None

                if isinstance(node, ast.ImportFrom):
                    imported_module = node.module
                elif isinstance(node, ast.Import):
                    imported_module = ",".join(
                        name.name
                        for name in node.names
                    )

                with self.subTest(path=path.name):
                    self.assertNotEqual(
                        imported_module,
                        "frontend.api_client",
                    )

    def test_facade_preserves_httpx_mock_path(self) -> None:
        """舊 httpx mock 路徑必須控制 transport。"""

        self.assertIs(api_client.httpx, transport.httpx)


if __name__ == "__main__":
    unittest.main()
