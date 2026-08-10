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
        self.assertIn("not yet executed", audit)
        self.assertIn("user's confirmation", audit)
        self.assertIn("total-return and principal-risk checks", audit)

    def test_roadmap_blocks_m12_until_audit(self):
        roadmap = (PROJECT_ROOT / "docs" / "ROADMAP.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("docs/M12_ENTRY_AUDIT.md", roadmap)
        self.assertIn("Do not begin M12", roadmap)
        self.assertIn("03a9635", roadmap)


if __name__ == "__main__":
    unittest.main()
