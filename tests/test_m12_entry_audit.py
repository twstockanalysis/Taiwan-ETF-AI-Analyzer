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
        self.assertIn("executed on 2026-08-10", audit)
        self.assertIn("awaiting the user's explicit confirmation", audit)
        self.assertIn("total-return and principal-risk checks", audit)
        self.assertIn("M11-5A", audit)
        self.assertIn("M11-5B", audit)
        self.assertIn("owner-only", audit)
        self.assertIn("do not begin M11-5 implementation", audit)

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

    def test_roadmap_blocks_m12_until_audit(self):
        roadmap = (PROJECT_ROOT / "docs" / "ROADMAP.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("docs/M12_ENTRY_AUDIT.md", roadmap)
        self.assertIn("Do not begin M11-5 or M12", roadmap)
        self.assertIn("03a9635", roadmap)
        self.assertIn("awaiting the user's explicit", roadmap)


if __name__ == "__main__":
    unittest.main()
