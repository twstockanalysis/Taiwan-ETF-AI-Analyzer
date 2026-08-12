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
        self.assertIn("1e0a920", audit)
        self.assertIn("re-executed on merged main", audit)
        self.assertIn("total-return and principal-risk checks", audit)
        self.assertIn("M11-5A", audit)
        self.assertIn("M11-5B", audit)
        self.assertIn("owner-only", audit)
        self.assertIn("0-N", audit)
        self.assertIn("[ETF code] [held units]", audit)
        self.assertIn("stored official close", audit)
        self.assertIn("deferred until after M12", audit)
        self.assertIn("M12 may begin only after this refreshed gate is merged", audit)

    def test_audit_maps_actual_product_and_runtime_gaps(self):
        audit = (PROJECT_ROOT / "docs" / "M12_ENTRY_AUDIT.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("/target-analysis", audit)
        self.assertIn("/monthly-income", audit)
        self.assertIn("component rows:               1430", audit)
        self.assertIn("create_app()", audit)
        self.assertIn("`PARTIAL`", audit)
        self.assertIn("True M12 scope after M11-5", audit)
        self.assertIn("M12-1", audit)
        self.assertIn("M12-6", audit)
        self.assertIn("deployment-time schema initialization", audit)

    def test_roadmap_records_m11_5_complete_and_refresh_gate(self):
        roadmap = (PROJECT_ROOT / "docs" / "ROADMAP.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("docs/M12_ENTRY_AUDIT.md", roadmap)
        self.assertIn("M11-5 — Confirmed public cash-flow flow closure", roadmap)
        self.assertIn("dynamic `0-N` holding editor", roadmap)
        self.assertIn("M11-5 — Confirmed public cash-flow flow closure — Complete", roadmap)
        self.assertIn(
            "Begin M12 only after the refreshed 2026-08-12 audit gate is merged",
            roadmap,
        )
        self.assertIn("self-service account aliases", roadmap)
        self.assertIn("03a9635", roadmap)
        self.assertIn("explicitly confirmed", roadmap)

    def test_reaudit_closes_product_gaps_without_expanding_scope(self):
        audit = (PROJECT_ROOT / "docs" / "M12_ENTRY_AUDIT.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "Gross and after-tax cash flow by payment month | `DELIVERED`",
            audit,
        )
        self.assertIn(
            "Negative total-return, persistent-decline, recovery and peer warnings | `DELIVERED`",
            audit,
        )
        self.assertIn("No remaining product feature gap blocks M12 entry", audit)
        self.assertIn("no self-service account system", audit)
        self.assertIn("Do not combine self-service accounts", audit)


if __name__ == "__main__":
    unittest.main()
