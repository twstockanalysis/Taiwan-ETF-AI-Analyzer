"""下載官方 OpenAPI 並探索 ETF 相關端點。"""

from backend.app.data_sources.openapi import (
    download_openapi_snapshot,
    find_endpoint_candidates,
    resolve_base_url,
)
from backend.app.data_sources.registry import (
    list_enabled_openapi_sources,
)


SEARCH_KEYWORDS = (
    "ETF",
    "指數股票型基金",
    "交易所交易基金",
    "基金",
    "受益憑證",
)


def main() -> None:
    """下載規格並顯示 ETF 候選端點。"""

    sources = (
        list_enabled_openapi_sources()
    )

    print("開始檢查官方 OpenAPI")
    print("=" * 80)

    for source in sources:
        print(f"來源：{source.display_name}")
        print(f"來源 ID：{source.source_id}")
        print(
            f"規格網址："
            f"{source.specification_url}"
        )

        try:
            document, snapshot = (
                download_openapi_snapshot(
                    source
                )
            )

        except Exception as error:
            print(
                f"下載失敗："
                f"{type(error).__name__}: "
                f"{error}"
            )
            print("=" * 80)
            continue

        specification_version = (
            document.get("openapi")
            or document.get("swagger")
        )

        base_url = resolve_base_url(
            document
        )

        candidates = find_endpoint_candidates(
            document=document,
            keywords=SEARCH_KEYWORDS,
        )

        print(
            f"規格版本："
            f"{specification_version}"
        )
        print(
            f"實際 Base URL：{base_url}"
        )
        print(
            f"全部端點數量："
            f"{snapshot.path_count}"
        )
        print(
            f"候選端點數量："
            f"{len(candidates)}"
        )
        print(
            f"規格快照："
            f"{snapshot.document_path}"
        )
        print(
            f"SHA-256："
            f"{snapshot.checksum_sha256}"
        )

        if not candidates:
            print(
                "沒有找到 ETF 相關候選端點。"
            )

        for candidate in candidates:
            print("-" * 80)
            print(
                f"{candidate.method} "
                f"{candidate.path}"
            )
            print(
                f"摘要：{candidate.summary}"
            )
            print(
                f"標籤："
                f"{', '.join(candidate.tags)}"
            )
            print(
                f"Operation ID："
                f"{candidate.operation_id}"
            )

        print("=" * 80)


if __name__ == "__main__":
    main()