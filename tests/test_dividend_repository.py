"""ETF dividend Repository tests."""

import tempfile
import unittest
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.models.etf_analysis import (
    DividendComponentBasis,
    ETFDividendComponentImportRecord,
    ETFDividendImportRecord,
)
from backend.app.repositories.dividend_repository import (
    get_dividend_id,
    list_dividend_components,
    list_etf_dividends,
    upsert_dividend_component_records,
    upsert_dividend_dataset,
    upsert_dividend_records,
)


class TestDividendRepository(
    unittest.TestCase
):
    """Test dividend event and component persistence."""

    def setUp(self) -> None:
        """Create an isolated database."""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "dividend_repository.db"
        )

        initialize_database(
            self.database_path
        )

        connection = get_connection(
            self.database_path
        )

        try:
            connection.executemany(
                """
                INSERT INTO etf_master (
                    code,
                    name,
                    is_active,
                    is_bond
                )
                VALUES (?, ?, ?, ?);
                """,
                [
                    (
                        "0050",
                        "元大台灣50",
                        0,
                        0,
                    ),
                    (
                        "00918",
                        "大華優利高填息30",
                        0,
                        0,
                    ),
                ],
            )

            connection.commit()

        finally:
            connection.close()

    def tearDown(self) -> None:
        """Remove temporary data."""

        self.temp_directory.cleanup()

    def build_dividend(
        self,
        code: str = "0050",
        amount: str = "1.00",
        source_event_id: str = (
            "twse_etfortune_dividend:"
            "0050:2026-07-21"
        ),
        source_id: str = (
            "twse_etfortune_dividend"
        ),
    ) -> ETFDividendImportRecord:
        """Build one dividend event."""

        return ETFDividendImportRecord.model_validate(
            {
                "etf_code": code,
                "source_event_id": (
                    source_event_id
                ),
                "ex_dividend_date": (
                    "2026-07-21"
                ),
                "record_date": (
                    "2026-07-27"
                ),
                "payment_date": (
                    "2026-08-08"
                ),
                "amount_per_unit": amount,
                "currency": "TWD",
                "source_id": source_id,
            }
        )

    def build_component(
        self,
        code: str = "0050",
        event_id: str = (
            "twse_etfortune_dividend:"
            "0050:2026-07-21"
        ),
        component_code: str = (
            "EST_REALIZED_CAPITAL_GAIN"
        ),
        component_basis: str = "ESTIMATED",
        ratio_pct: str = "74",
        source_id: str = (
            "twse_etfortune_dividend"
        ),
    ) -> ETFDividendComponentImportRecord:
        """Build one dividend component."""

        return (
            ETFDividendComponentImportRecord
            .model_validate(
                {
                    "etf_code": code,
                    "dividend_source_event_id": (
                        event_id
                    ),
                    "component_code": (
                        component_code
                    ),
                    "component_basis": (
                        component_basis
                    ),
                    "ratio_pct": ratio_pct,
                    "source_id": source_id,
                }
            )
        )

    def test_new_dividend_is_inserted(
        self,
    ) -> None:
        """A new event is inserted."""

        summary = upsert_dividend_records(
            records=[
                self.build_dividend(),
            ],
            database_path=self.database_path,
        )

        self.assertEqual(
            summary.inserted_records,
            1,
        )

        self.assertEqual(
            summary.updated_records,
            0,
        )

    def test_existing_dividend_is_updated(
        self,
    ) -> None:
        """The same source event updates in place."""

        upsert_dividend_records(
            records=[
                self.build_dividend(),
            ],
            database_path=self.database_path,
        )

        summary = upsert_dividend_records(
            records=[
                self.build_dividend(
                    amount="1.25"
                ),
            ],
            database_path=self.database_path,
        )

        self.assertEqual(
            summary.inserted_records,
            0,
        )

        self.assertEqual(
            summary.updated_records,
            1,
        )

        rows = list_etf_dividends(
            etf_code="0050",
            database_path=self.database_path,
        )

        self.assertEqual(
            len(rows),
            1,
        )

        self.assertEqual(
            rows[0]["amount_per_unit"],
            1.25,
        )

    def test_estimated_and_actual_can_coexist(
        self,
    ) -> None:
        """Estimated gain and actual 76W remain separate."""

        event = self.build_dividend()

        components = [
            self.build_component(),
            self.build_component(
                component_code="76W",
                component_basis="ACTUAL",
                ratio_pct="100",
                source_id=(
                    "official_distribution_notice"
                ),
            ),
        ]

        summary = upsert_dividend_dataset(
            dividends=[event],
            components=components,
            database_path=self.database_path,
        )

        self.assertEqual(
            summary.dividends.inserted_records,
            1,
        )

        self.assertEqual(
            summary.components.inserted_records,
            2,
        )

        dividend_id = get_dividend_id(
            etf_code="0050",
            source_event_id=(
                event.source_event_id
            ),
            database_path=self.database_path,
        )

        self.assertIsNotNone(
            dividend_id
        )

        rows = list_dividend_components(
            dividend_id=dividend_id,
            database_path=self.database_path,
        )

        keys = {
            (
                row["component_basis"],
                row["component_code"],
            )
            for row in rows
        }

        self.assertEqual(
            keys,
            {
                (
                    "ESTIMATED",
                    "EST_REALIZED_CAPITAL_GAIN",
                ),
                (
                    "ACTUAL",
                    "76W",
                ),
            },
        )

    def test_same_component_from_different_sources(
        self,
    ) -> None:
        """The same actual code can retain two sources."""

        event = self.build_dividend()

        upsert_dividend_records(
            records=[event],
            database_path=self.database_path,
        )

        summary = (
            upsert_dividend_component_records(
                records=[
                    self.build_component(
                        component_code="76W",
                        component_basis="ACTUAL",
                        ratio_pct="100",
                        source_id="notice_a",
                    ),
                    self.build_component(
                        component_code="76W",
                        component_basis="ACTUAL",
                        ratio_pct="99",
                        source_id="notice_b",
                    ),
                ],
                database_path=(
                    self.database_path
                ),
            )
        )

        self.assertEqual(
            summary.inserted_records,
            2,
        )

    def test_component_is_updated_in_place(
        self,
    ) -> None:
        """One component key updates rather than duplicates."""

        event = self.build_dividend()

        upsert_dividend_records(
            records=[event],
            database_path=self.database_path,
        )

        upsert_dividend_component_records(
            records=[
                self.build_component(
                    ratio_pct="74"
                ),
            ],
            database_path=self.database_path,
        )

        summary = (
            upsert_dividend_component_records(
                records=[
                    self.build_component(
                        ratio_pct="75"
                    ),
                ],
                database_path=(
                    self.database_path
                ),
            )
        )

        self.assertEqual(
            summary.inserted_records,
            0,
        )

        self.assertEqual(
            summary.updated_records,
            1,
        )

    def test_missing_etf_is_rejected(
        self,
    ) -> None:
        """A dividend cannot reference an unknown ETF."""

        with self.assertRaises(
            KeyError
        ):
            upsert_dividend_records(
                records=[
                    self.build_dividend(
                        code="9999",
                        source_event_id=(
                            "official:9999:2026-Q3"
                        ),
                    ),
                ],
                database_path=(
                    self.database_path
                ),
            )

    def test_missing_parent_event_is_rejected(
        self,
    ) -> None:
        """A component requires an existing event."""

        with self.assertRaises(
            KeyError
        ):
            upsert_dividend_component_records(
                records=[
                    self.build_component(),
                ],
                database_path=(
                    self.database_path
                ),
            )

    def test_atomic_dataset_rolls_back(
        self,
    ) -> None:
        """A component failure rolls back its new event."""

        event = self.build_dividend()

        invalid_component = (
            self.build_component(
                event_id=(
                    "twse_etfortune_dividend:"
                    "0050:missing"
                )
            )
        )

        with self.assertRaises(
            KeyError
        ):
            upsert_dividend_dataset(
                dividends=[event],
                components=[
                    invalid_component,
                ],
                database_path=(
                    self.database_path
                ),
            )

        dividend_id = get_dividend_id(
            etf_code="0050",
            source_event_id=(
                event.source_event_id
            ),
            database_path=self.database_path,
        )

        self.assertIsNone(
            dividend_id
        )

    def test_duplicate_component_batch_is_rejected(
        self,
    ) -> None:
        """Duplicate incoming component keys are rejected."""

        event = self.build_dividend()

        upsert_dividend_records(
            records=[event],
            database_path=self.database_path,
        )

        component = self.build_component()

        with self.assertRaises(
            ValueError
        ):
            upsert_dividend_component_records(
                records=[
                    component,
                    component,
                ],
                database_path=(
                    self.database_path
                ),
            )

    def test_component_filters_work(
        self,
    ) -> None:
        """Basis and source filters return only matches."""

        event = self.build_dividend()

        upsert_dividend_dataset(
            dividends=[event],
            components=[
                self.build_component(),
                self.build_component(
                    component_code="76W",
                    component_basis="ACTUAL",
                    ratio_pct="100",
                    source_id="notice",
                ),
            ],
            database_path=self.database_path,
        )

        dividend_id = get_dividend_id(
            etf_code="0050",
            source_event_id=(
                event.source_event_id
            ),
            database_path=self.database_path,
        )

        rows = list_dividend_components(
            dividend_id=dividend_id,
            database_path=self.database_path,
            component_basis=(
                DividendComponentBasis.ACTUAL
            ),
            source_id="NOTICE",
        )

        self.assertEqual(
            len(rows),
            1,
        )

        self.assertEqual(
            rows[0]["component_code"],
            "76W",
        )


if __name__ == "__main__":
    unittest.main()
