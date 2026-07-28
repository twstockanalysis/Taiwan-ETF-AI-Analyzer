"""顯示目前啟用的 ETF 資料來源。"""

from backend.app.data_sources.registry import (
    list_enabled_sources,
)


def main() -> None:
    """列出目前啟用的資料來源。"""

    sources = list_enabled_sources()

    print("目前啟用的 ETF 資料來源")
    print("-" * 70)

    for source in sources:
        print(f"來源 ID：{source.source_id}")
        print(f"名稱：{source.display_name}")
        print(f"市場：{source.market}")
        print(f"型態：{source.source_type}")
        print(f"優先順序：{source.priority}")
        print(f"Base URL：{source.base_url}")
        print("-" * 70)

    print(f"啟用來源數量：{len(sources)}")


if __name__ == "__main__":
    main()