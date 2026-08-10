"""保護使用者要求的 M12 前置方向與功能重審門檻。"""

from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestM12EntryAudit(unittest.TestCase):
    def test_audit_records_post_m9_baseline_and_user_confirmation(self):
        audit = (PROJECT_ROOT / "docs" / "M12_ENTRY_AUDIT.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("03a9635", audit)
        self.assertIn("on 2026-08-10", audit)
        self.assertIn("explicitly confirmed by the user", audit)
        self.assertIn("total-return and principal-risk checks", audit)
        self.assertIn("M11-5A", audit)
        self.assertIn("M11-5B", audit)
        self.assertIn("owner-only", audit)
        self.assertIn("0-N", audit)
        self.assertIn("[ETF code] [held units]", audit)
        self.assertIn("stored official close", audit)
        self.assertIn("deferred until after M12", audit)
        self.assertIn("Do not begin\nM12 until M11-5", audit)

    def test_audit_maps_actual_product_and_runtime_gaps(self):
        audit = (PROJECT_ROOT / "docs" / "M12_ENTRY_AUDIT.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("/target-analysis", audit)
        self.assertIn("/monthly-income", audit)
        self.assertIn("ACTUAL component rows:        0", audit)
        self.assertIn("create_app()", audit)
        self.assertIn("`PARTIAL`", audit)
        self.assertIn("True M12 scope after M11-5", audit)

    def test_roadmap_allows_m11_5_after_merge_and_blocks_m12(self):
        roadmap = (PROJECT_ROOT / "docs" / "ROADMAP.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("docs/M12_ENTRY_AUDIT.md", roadmap)
        self.assertIn("M11-5 — Confirmed public cash-flow flow closure", roadmap)
        self.assertIn("dynamic `0-N` holding editor", roadmap)
        self.assertIn("Do not begin M12 until M11-5 is completed", roadmap)
        self.assertIn("self-service account aliases", roadmap)
        self.assertIn("03a9635", roadmap)
        self.assertIn("explicitly confirmed", roadmap)


if __name__ == "__main__":
    unittest.main()
