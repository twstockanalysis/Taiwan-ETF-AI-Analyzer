"""TWSE ETF e添富配息清單下載、解析與快照。"""

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import httpx

from backend.app.config.settings import RAW_DATA_DIR
from backend.app.data_sources.openapi import (
    create_ssl_context,
)
from backend.app.data_sources.registry import (
    DataSource,
    get_data_source,
)


SOURCE_ID = "twse_etfortune_dividend"

REQUIRED_PAGE_MARKERS = (
    "證券代號",
    "除息交易日",
    "收益分配發放日",
)


@dataclass(
    frozen=True,
    slots=True,
)
class TWSEDividendPageRow:
    """TWSE 配息頁面中的單一事件列。"""

    etf_code: str
    etf_name: str
    ex_dividend_date_text: str
    record_date_text: str
    payment_date_text: str
    amount_per_unit_text: str
    detail_text: str


@dataclass(
    frozen=True,
    slots=True,
)
class RawHtmlSnapshot:
    """HTML 原始快照結果。"""

    source_id: str
    downloaded_at: datetime
    data_path: Path
    metadata_path: Path
    checksum_sha256: str


class _TableRowParser(HTMLParser):
    """將 HTML table 轉成純文字列。"""

    def __init__(self) -> None:
        super().__init__(
            convert_charrefs=True
        )
        self.rows: list[list[str]] = []
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        del attrs

        normalized_tag = tag.lower()

        if normalized_tag == "tr":
            self._current_row = []

        elif (
            normalized_tag in {"td", "th"}
            and self._current_row is not None
        ):
            self._current_cell = []

    def handle_data(
        self,
        data: str,
    ) -> None:
        if self._current_cell is not None:
            self._current_cell.append(data)

    def handle_endtag(
        self,
        tag: str,
    ) -> None:
        normalized_tag = tag.lower()

        if (
            normalized_tag in {"td", "th"}
            and self._current_cell is not None
            and self._current_row is not None
        ):
            cell_text = re.sub(
                r"\s+",
                " ",
                "".join(
                    self._current_cell
                ),
            ).strip()

            self._current_row.append(
                cell_text
            )

            self._current_cell = None

        elif (
            normalized_tag == "tr"
            and self._current_row is not None
        ):
            if any(self._current_row):
                self.rows.append(
                    self._current_row
                )

            self._current_row = None
            self._current_cell = None


def get_dividend_source() -> DataSource:
    """取得 TWSE ETF e添富配息資料來源。"""

    return get_data_source(
        SOURCE_ID
    )


def validate_twse_dividend_html(
    html_text: str,
) -> None:
    """驗證頁面是否具有必要欄位。"""

    if not html_text.strip():
        raise ValueError(
            "TWSE 配息頁面內容為空白"
        )

    missing_markers = [
        marker
        for marker in REQUIRED_PAGE_MARKERS
        if marker not in html_text
    ]

    if missing_markers:
        raise ValueError(
            "TWSE 配息頁面缺少必要欄位："
            + ", ".join(missing_markers)
        )


def fetch_twse_dividend_html(
    timeout_seconds: float = 30.0,
) -> str:
    """下載 TWSE ETF e添富配息清單 HTML。"""

    source = get_dividend_source()

    if not source.base_url:
        raise ValueError(
            "TWSE 配息來源缺少網址"
        )

    ssl_context = create_ssl_context(
        allow_legacy_x509=(
            source.allow_legacy_x509
        ),
    )

    response = httpx.get(
        source.base_url,
        timeout=timeout_seconds,
        follow_redirects=True,
        verify=ssl_context,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": (
                "TW-ETF-AI-Analyzer/0.1 "
                "(official-data-downloader)"
            ),
        },
    )

    response.raise_for_status()

    html_text = response.text

    validate_twse_dividend_html(
        html_text
    )

    return html_text


def extract_twse_dividend_rows(
    html_text: str,
) -> list[TWSEDividendPageRow]:
    """從 TWSE 配息頁面擷取事件列。

    詳細組成資訊可能位於事件列本身，或位於其後的
    展開列；本函式會將下一個 ETF 事件前的文字合併。
    """

    validate_twse_dividend_html(
        html_text
    )

    parser = _TableRowParser()
    parser.feed(html_text)

    event_pattern = re.compile(
        r"^[0-9A-Z]{4,10}$"
    )

    event_indexes = [
        index
        for index, cells in enumerate(
            parser.rows
        )
        if (
            len(cells) >= 6
            and event_pattern.fullmatch(
                cells[0].strip().upper()
            )
        )
    ]

    rows: list[TWSEDividendPageRow] = []

    for position, row_index in enumerate(
        event_indexes
    ):
        cells = parser.rows[row_index]

        next_event_index = (
            event_indexes[position + 1]
            if position + 1 < len(
                event_indexes
            )
            else len(parser.rows)
        )

        detail_parts = [
            text
            for text in cells[6:]
            if text
        ]

        for extra_row in parser.rows[
            row_index + 1:next_event_index
        ]:
            detail_parts.extend(
                text
                for text in extra_row
                if text
            )

        rows.append(
            TWSEDividendPageRow(
                etf_code=(
                    cells[0].strip().upper()
                ),
                etf_name=cells[1].strip(),
                ex_dividend_date_text=(
                    cells[2].strip()
                ),
                record_date_text=(
                    cells[3].strip()
                ),
                payment_date_text=(
                    cells[4].strip()
                ),
                amount_per_unit_text=(
                    cells[5].strip()
                ),
                detail_text=" ".join(
                    detail_parts
                ),
            )
        )

    if not rows:
        raise ValueError(
            "TWSE 配息頁面找不到可辨識的 ETF 事件列"
        )

    return rows


def save_twse_dividend_html_snapshot(
    html_text: str,
    output_root: Path | None = None,
    downloaded_at: datetime | None = None,
) -> RawHtmlSnapshot:
    """保存 TWSE 配息 HTML 與中繼資料。"""

    validate_twse_dividend_html(
        html_text
    )

    source = get_dividend_source()

    if downloaded_at is None:
        downloaded_at = datetime.now(
            timezone.utc
        )

    if output_root is None:
        output_root = (
            RAW_DATA_DIR / "dividends"
        )

    timestamp = downloaded_at.strftime(
        "%Y%m%dT%H%M%SZ"
    )

    source_directory = (
        output_root / source.source_id
    )

    source_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    data_bytes = html_text.encode(
        "utf-8"
    )

    checksum = hashlib.sha256(
        data_bytes
    ).hexdigest()

    data_path = (
        source_directory
        / (
            f"{source.source_id}_"
            f"{timestamp}.html"
        )
    )

    metadata_path = (
        source_directory
        / (
            f"{source.source_id}_"
            f"{timestamp}.meta.json"
        )
    )

    data_path.write_bytes(
        data_bytes
    )

    metadata = {
        "source_id": source.source_id,
        "display_name": source.display_name,
        "source_url": source.base_url,
        "downloaded_at": (
            downloaded_at.isoformat()
        ),
        "checksum_sha256": checksum,
        "data_path": str(data_path),
    }

    metadata_text = json.dumps(
        metadata,
        ensure_ascii=False,
        indent=2,
    )

    metadata_path.write_text(
        metadata_text,
        encoding="utf-8",
    )

    (
        source_directory / "latest.html"
    ).write_bytes(
        data_bytes
    )

    (
        source_directory
        / "latest.meta.json"
    ).write_text(
        metadata_text,
        encoding="utf-8",
    )

    return RawHtmlSnapshot(
        source_id=source.source_id,
        downloaded_at=downloaded_at,
        data_path=data_path,
        metadata_path=metadata_path,
        checksum_sha256=checksum,
    )
