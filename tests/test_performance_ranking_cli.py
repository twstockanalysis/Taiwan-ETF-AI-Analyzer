"""ETF 績效排行榜 CLI 測試。"""

import unittest
from unittest.mock import patch

from backend.app.data_sources.check_performance_ranking import (
    build_argument_parser,
    main,
)
from backend.app.models.etf_analysis import (
    PerformancePeriod,
)


class TestPerformanceRankingCLI(
    unittest.TestCase
):
    """測試排行榜期間參數。"""

    def test_default_period_is_six_months(
        self,
    ) -> None:
        """確認排行榜預設為六個月。"""

        arguments = (
            build_argument_parser()
            .parse_args([])
        )

        self.assertEqual(
            arguments.period,
            "6M",
        )

    def test_period_can_be_selected(
        self,
    ) -> None:
        """確認可指定三個月排行榜。"""

        arguments = (
            build_argument_parser()
            .parse_args(
                [
                    "--period",
                    "3M",
                ]
            )
        )

        self.assertEqual(
            arguments.period,
            "3M",
        )

    @patch(
        "backend.app.data_sources."
        "check_performance_ranking."
        "count_latest_performance_ranking",
        return_value=0,
    )
    @patch(
        "backend.app.data_sources."
        "check_performance_ranking."
        "list_latest_performance_ranking",
        return_value=[],
    )
    @patch(
        "backend.app.data_sources."
        "check_performance_ranking."
        "build_argument_parser"
    )
    def test_main_forwards_selected_period(
        self,
        mock_build_parser,
        mock_list_ranking,
        mock_count_ranking,
    ) -> None:
        """確認 CLI 將期間傳給 Repository。"""

        mock_build_parser.return_value.parse_args.return_value = (
            type(
                "Arguments",
                (),
                {
                    "period": "1Y",
                    "limit": 10,
                    "active": "all",
                    "include_bond": False,
                },
            )()
        )

        with patch("builtins.print"):
            main()

        mock_list_ranking.assert_called_once_with(
            period_code=(
                PerformancePeriod.ONE_YEAR
            ),
            is_active=None,
            is_bond=False,
            limit=10,
        )

        mock_count_ranking.assert_called_once_with(
            period_code=(
                PerformancePeriod.ONE_YEAR
            ),
            is_active=None,
            is_bond=False,
        )


if __name__ == "__main__":
    unittest.main()
