"""V3-1 公開現金流基線服務測試。"""

from datetime import date
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from backend.app.models.public_planner import PublicPlannerRequest
from backend.app.services.public_planner import analyze_public_planner_baseline


class TestPublicPlannerBaseline(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "public-planner.db"
        initialize_database(self.database_path)
        connection = get_connection(self.database_path)
        connection.execute(
            """
            INSERT INTO etf_master (code, name, is_active, is_bond)
            VALUES ('0056', '元大高股息', 0, 0);
            """
        )
        connection.commit()
        connection.close()

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def _insert_market_facts(self) -> None:
        connection = get_connection(self.database_path)
        connection.execute(
            """
            INSERT INTO etf_daily_close (
                etf_code, trade_date, close_price, source_id
            ) VALUES ('0056', '2026-01-01', 20, 'twse_stock_day');
            """
        )
        connection.executemany(
            """
            INSERT INTO etf_dividend (
                etf_code, source_event_id, payment_date,
                amount_per_unit, currency, source_id
            ) VALUES ('0056', ?, ?, 1.5, 'TWD', 'TEST');
            """,
            [
                ("event-2023", "2023-01-01"),
                ("event-2024", "2024-01-01"),
                ("event-2025", "2025-01-01"),
                ("event-2026", "2026-01-01"),
            ],
        )
        connection.commit()
        connection.close()

    def test_zero_holdings_is_known_zero_baseline(self) -> None:
        result = analyze_public_planner_baseline(
            PublicPlannerRequest(
                target_after_tax_cash_twd=3000,
                target_months=[12, 1, 1],
                existing_holdings=[],
            ),
            self.database_path,
            as_of_date=date(2026, 1, 1),
        )

        self.assertEqual(result.status, "AVAILABLE")
        self.assertEqual(result.target_months, [1, 12])
        self.assertEqual(result.total_current_value, Decimal("0"))
        self.assertEqual(result.monthly_cash_flow[0].after_tax_cash, Decimal("0"))
        self.assertEqual(result.monthly_cash_flow[0].shortfall, Decimal("3000"))
        self.assertEqual(result.monthly_cash_flow[1].shortfall, Decimal("0"))

    def test_holdings_use_official_close_and_payment_month_history(self) -> None:
        self._insert_market_facts()
        result = analyze_public_planner_baseline(
            PublicPlannerRequest(
                target_after_tax_cash_twd=200,
                target_months=[1],
                existing_holdings=[{"etf_code": "0056", "held_units": 100}],
                history_years=3,
                cash_deduction_rate_pct=10,
            ),
            self.database_path,
            as_of_date=date(2026, 1, 1),
        )

        self.assertEqual(result.status, "AVAILABLE")
        self.assertEqual(result.total_current_value, Decimal("2000.00"))
        self.assertEqual(result.holdings[0].price_source_id, "twse_stock_day")
        january = result.monthly_cash_flow[0]
        self.assertEqual(january.gross_cash, Decimal("150.00"))
        self.assertEqual(january.after_tax_cash, Decimal("135.00"))
        self.assertEqual(january.shortfall, Decimal("65.00"))
        self.assertNotIn(
            "INSUFFICIENT_PERFORMANCE_HISTORY",
            {item.code for item in result.issues},
        )

    def test_missing_market_data_remains_null_and_partial(self) -> None:
        result = analyze_public_planner_baseline(
            PublicPlannerRequest(
                target_after_tax_cash_twd=100,
                target_months=[1],
                existing_holdings=[{"etf_code": "0056", "held_units": 10}],
            ),
            self.database_path,
            as_of_date=date(2026, 1, 1),
        )

        self.assertEqual(result.status, "PARTIAL")
        self.assertIsNone(result.total_current_value)
        self.assertIsNone(result.monthly_cash_flow[0].gross_cash)
        self.assertIsNone(result.monthly_cash_flow[0].shortfall)
        self.assertIn("MISSING_REFERENCE_PRICE", {item.code for item in result.issues})
        self.assertIn("MISSING_DIVIDEND_DATA", {item.code for item in result.issues})

    def test_undated_dividend_blocks_month_assignment(self) -> None:
        self._insert_market_facts()
        connection = get_connection(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO etf_dividend (
                    etf_code, source_event_id, announcement_date, payment_date,
                    amount_per_unit, currency, source_id
                ) VALUES (
                    '0056', 'undated-event', '2025-12-01', NULL,
                    2, 'TWD', 'TEST'
                );
                """
            )
            connection.commit()
        finally:
            connection.close()

        result = analyze_public_planner_baseline(
            PublicPlannerRequest(
                target_after_tax_cash_twd=100,
                target_months=[1],
                existing_holdings=[{"etf_code": "0056", "held_units": 10}],
            ),
            self.database_path,
            as_of_date=date(2026, 1, 1),
        )

        self.assertEqual(result.status, "PARTIAL")
        self.assertIsNone(result.monthly_cash_flow[0].gross_cash)
        self.assertIn("MISSING_PAYMENT_DATE", {item.code for item in result.issues})


if __name__ == "__main__":
    unittest.main()
