"""國泰投信實際配息組成公告 Adapter。"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urlparse

from backend.app.data_sources.actual_dividend_notice import (
    ActualDividendNoticeInput,
)
from backend.app.data_sources.dividend_normalizer import (
    parse_roc_date,
)


SOURCE_ID = (
    "cathay_actual_dividend_announcement"
)

ISSUER_MARKER = (
    "國泰證券投資信託股份有限公司"
)

ACTUAL_MARKERS = (
    "實際配發金額組成如下",
    "實際配發金額組成",
)

ESTIMATED_REJECTION_MARKERS = (
    "預估收益分配組成",
    "預估配息組成",
    "估算配息組成",
    "以收益分配通知書為準",
)


class CathayAnnouncementRejected(
    ValueError
):
    """公告不符合 ACTUAL Adapter 接受政策。"""


class _CathayHTMLParser(HTMLParser):
    """擷取頁面純文字及表格列。"""

    def __init__(self) -> None:
        super().__init__(
            convert_charrefs=True
        )

        self.text_parts: list[str] = []
        self.rows: list[list[str]] = []
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[
            tuple[str, str | None]
        ],
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

        elif normalized_tag in {
            "br",
            "p",
            "div",
            "li",
            "h1",
            "h2",
            "h3",
        }:
            self.text_parts.append(
                "\n"
            )

    def handle_data(
        self,
        data: str,
    ) -> None:
        self.text_parts.append(
            data
        )

        if self._current_cell is not None:
            self._current_cell.append(
                data
            )

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

        elif normalized_tag in {
            "p",
            "div",
            "li",
            "h1",
            "h2",
            "h3",
        }:
            self.text_parts.append(
                "\n"
            )


def normalize_page_text(
    value: str,
) -> str:
    """正規化公告純文字與標點。"""

    normalized = (
        value.replace("\u3000", " ")
        .replace("︰", "：")
        .replace(":", "：")
    )

    lines = [
        re.sub(
            r"\s+",
            " ",
            line,
        ).strip()
        for line in normalized.splitlines()
    ]

    return "\n".join(
        line
        for line in lines
        if line
    )


def extract_announcement_content(
    html_text: str,
) -> tuple[
    str,
    list[list[str]],
]:
    """將 HTML 轉成純文字與表格列。"""

    if not html_text.strip():
        raise CathayAnnouncementRejected(
            "國泰公告內容為空白"
        )

    parser = _CathayHTMLParser()
    parser.feed(
        html_text
    )

    return (
        normalize_page_text(
            "".join(
                parser.text_parts
            )
        ),
        parser.rows,
    )


def extract_labeled_roc_date(
    page_text: str,
    labels: tuple[str, ...],
) -> object:
    """依欄位標籤擷取民國日期。"""

    label_pattern = "|".join(
        re.escape(label)
        for label in labels
    )

    match = re.search(
        (
            rf"(?:{label_pattern})"
            r"\s*[：:]?\s*"
            r"(\d{2,3}"
            r"(?:年\d{1,2}月\d{1,2}日"
            r"|[./-]\d{1,2}[./-]\d{1,2}))"
        ),
        page_text,
    )

    if match is None:
        raise CathayAnnouncementRejected(
            "公告缺少日期欄位："
            + "／".join(labels)
        )

    try:
        return parse_roc_date(
            match.group(1)
        )

    except ValueError as error:
        raise CathayAnnouncementRejected(
            str(error)
        ) from error


def extract_document_date(
    page_text: str,
):
    """擷取公告文件日期。"""

    match = re.search(
        (
            r"中華民國\s*"
            r"(\d{2,3}年"
            r"\d{1,2}月"
            r"\d{1,2}日)"
        ),
        page_text,
    )

    if match is None:
        raise CathayAnnouncementRejected(
            "公告缺少中華民國文件日期"
        )

    try:
        return parse_roc_date(
            match.group(1)
        )

    except ValueError as error:
        raise CathayAnnouncementRejected(
            str(error)
        ) from error


def parse_decimal(
    value: str,
    field_name: str,
) -> Decimal:
    """解析公告金額或比例。"""

    normalized = (
        value.strip()
        .replace(",", "")
        .replace("%", "")
    )

    try:
        result = Decimal(
            normalized
        )

    except InvalidOperation as error:
        raise CathayAnnouncementRejected(
            f"{field_name}格式錯誤："
            f"{value}"
        ) from error

    if result < 0:
        raise CathayAnnouncementRejected(
            f"{field_name}不得小於 0"
        )

    return result


def extract_component_table(
    rows: list[list[str]],
) -> tuple[
    list[dict[str, object]],
    Decimal,
]:
    """擷取正式所得代碼、金額、比例及合計。"""

    components: list[
        dict[str, object]
    ] = []

    total_amount: Decimal | None = None

    code_pattern = re.compile(
        r"^([0-9]{2}[A-Z])\s*(.+)$"
    )

    for cells in rows:
        if len(cells) < 3:
            continue

        label = re.sub(
            r"\s+",
            " ",
            cells[0],
        ).strip()

        if label == "合計":
            total_amount = parse_decimal(
                cells[1],
                "合計金額",
            )
            continue

        match = code_pattern.fullmatch(
            label
        )

        if match is None:
            continue

        component_code = (
            match.group(1).upper()
        )

        component_name = (
            match.group(2).strip()
        )

        components.append(
            {
                "component_code": (
                    component_code
                ),
                "component_name": (
                    component_name
                ),
                "amount_per_unit": (
                    parse_decimal(
                        cells[1],
                        (
                            f"{component_code} "
                            "每單位金額"
                        ),
                    )
                ),
                "ratio_pct": (
                    parse_decimal(
                        cells[2],
                        (
                            f"{component_code} "
                            "占比"
                        ),
                    )
                ),
            }
        )

    if not components:
        raise CathayAnnouncementRejected(
            "公告找不到正式所得代碼表格"
        )

    if total_amount is None:
        raise CathayAnnouncementRejected(
            "公告找不到配息合計金額"
        )

    return (
        components,
        total_amount,
    )


def build_cathay_source_document_id(
    source_url: str,
) -> str:
    """由公告 URL 建立穩定文件 ID。"""

    parsed = urlparse(
        source_url
    )

    match = re.search(
        r"/announcement/(\d+)",
        parsed.path,
    )

    if match is None:
        raise CathayAnnouncementRejected(
            "國泰公告網址缺少公告編號"
        )

    return (
        "cathay-announcement-"
        + match.group(1)
    )


def parse_cathay_actual_dividend_announcement(
    *,
    html_text: str,
    source_document_url: str,
    etf_code: str,
    source_document_id: str | None = None,
) -> ActualDividendNoticeInput:
    """解析明確標示實際配發組成的國泰公告。"""

    (
        page_text,
        rows,
    ) = extract_announcement_content(
        html_text
    )

    if ISSUER_MARKER not in page_text:
        raise CathayAnnouncementRejected(
            "公告缺少國泰投信發行人標記"
        )

    rejection_marker = next(
        (
            marker
            for marker in (
                ESTIMATED_REJECTION_MARKERS
            )
            if marker in page_text
        ),
        None,
    )

    if rejection_marker is not None:
        raise CathayAnnouncementRejected(
            "公告包含預估語意，不得建立 "
            "ACTUAL："
            f"{rejection_marker}"
        )

    if not any(
        marker in page_text
        for marker in ACTUAL_MARKERS
    ):
        raise CathayAnnouncementRejected(
            "公告未明確標示實際配發金額組成"
        )

    document_date = (
        extract_document_date(
            page_text
        )
    )

    ex_dividend_date = (
        extract_labeled_roc_date(
            page_text,
            (
                "除息交易日",
            ),
        )
    )

    record_date = (
        extract_labeled_roc_date(
            page_text,
            (
                "收益分配基準日",
            ),
        )
    )

    payment_date = (
        extract_labeled_roc_date(
            page_text,
            (
                "收益分配發放日",
            ),
        )
    )

    (
        components,
        total_amount,
    ) = extract_component_table(
        rows
    )

    resolved_document_id = (
        source_document_id.strip()
        if source_document_id
        else build_cathay_source_document_id(
            source_document_url
        )
    )

    return (
        ActualDividendNoticeInput
        .model_validate(
            {
                "source_id": SOURCE_ID,
                "source_document_id": (
                    resolved_document_id
                ),
                "source_document_url": (
                    source_document_url
                ),
                "source_document_date": (
                    document_date
                ),
                "information_basis": (
                    "ACTUAL"
                ),
                "etf_code": etf_code,
                "announcement_date": (
                    document_date
                ),
                "ex_dividend_date": (
                    ex_dividend_date
                ),
                "record_date": (
                    record_date
                ),
                "payment_date": (
                    payment_date
                ),
                "amount_per_unit": (
                    total_amount
                ),
                "currency": "TWD",
                "components": components,
            }
        )
    )
