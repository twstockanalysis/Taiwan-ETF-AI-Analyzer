"""Streamlit 前端共用互動元件。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

import streamlit as st

from frontend.navigation import (
    build_detail_query_params,
)


PaginationAction = Literal[
    "previous",
    "next",
    "none",
]


def render_etf_detail_links(
    items: list[dict[str, Any]],
    *,
    caption: str,
    label_builder: Callable[
        [dict[str, Any]],
        str,
    ],
    code_field: str,
    name_field: str,
    source: str,
    source_query_params: dict[str, str],
) -> None:
    """以全寬連結顯示 ETF 資料列。"""

    st.caption(caption)

    for item in items:
        code = str(
            item[code_field]
        ).strip().upper()

        name = str(
            item[name_field]
        ).strip()

        st.page_link(
            "page_scripts/etf_detail_page.py",
            label=label_builder(item),
            icon=":material/chevron_right:",
            icon_position="right",
            help=(
                f"查看 {code} {name} 詳細資料"
            ),
            width="stretch",
            query_params=(
                build_detail_query_params(
                    code=code,
                    source=source,
                    source_query_params=(
                        source_query_params
                    ),
                )
            ),
        )


def render_pagination_controls(
    *,
    current_page: int,
    total_pages: int,
    previous_key: str,
    next_key: str,
) -> PaginationAction:
    """顯示一致的上一頁、頁次與下一頁控制。"""

    if current_page < 1:
        raise ValueError(
            "current_page 必須大於 0"
        )

    if total_pages < 1:
        raise ValueError(
            "total_pages 必須大於 0"
        )

    (
        previous_column,
        page_column,
        next_column,
    ) = st.columns(
        [
            1,
            2,
            1,
        ]
    )

    with previous_column:
        previous_clicked = st.button(
            "← 上一頁",
            disabled=(
                current_page <= 1
            ),
            key=previous_key,
        )

    with page_column:
        st.write(
            f"第 {current_page} 頁，"
            f"共 {total_pages} 頁"
        )

    with next_column:
        next_clicked = st.button(
            "下一頁 →",
            disabled=(
                current_page >= total_pages
            ),
            key=next_key,
        )

    if previous_clicked:
        return "previous"

    if next_clicked:
        return "next"

    return "none"
