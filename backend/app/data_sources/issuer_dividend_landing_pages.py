"""尚待升級為代號查詢 Adapter 的投信官方配息／公告入口。"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IssuerDividendLandingPage:
    issuer_key: str
    url: str
    official_domains: tuple[str, ...]
    page_kind: str
    network_access: str = "DIRECT"


ISSUER_DIVIDEND_LANDING_PAGES: dict[str, IssuerDividendLandingPage] = {
    "yuanta": IssuerDividendLandingPage(
        "yuanta", "https://www.yuantaetfs.com/News/announcement",
        ("yuantaetfs.com", "www.yuantaetfs.com"), "ETF_ANNOUNCEMENTS",
    ),
    "upam": IssuerDividendLandingPage(
        "upam", "https://www.ezmoney.com.tw/ETF/",
        ("ezmoney.com.tw", "www.ezmoney.com.tw"), "ETF_HOME",
    ),
    "sinopac": IssuerDividendLandingPage(
        "sinopac", "https://sitc.sinopac.com/newweb/index.html",
        ("sitc.sinopac.com",), "FUND_ANNOUNCEMENTS",
    ),
    "mega": IssuerDividendLandingPage(
        "mega", "https://www.megafunds.com.tw/MEGA/etf/income.aspx",
        ("megafunds.com.tw", "www.megafunds.com.tw"), "ETF_DIVIDENDS",
    ),
    "first": IssuerDividendLandingPage(
        "first", "https://www.fsitc.com.tw/ImportantNotice.aspx",
        ("fsitc.com.tw", "www.fsitc.com.tw"), "FUND_ANNOUNCEMENTS",
    ),
    "fuh_hwa": IssuerDividendLandingPage(
        "fuh_hwa", "https://www.fhtrust.com.tw/ETF/annoucement_list?page=0",
        ("fhtrust.com.tw", "www.fhtrust.com.tw"), "ETF_ANNOUNCEMENTS",
    ),
    "taishin": IssuerDividendLandingPage(
        "taishin", "https://www.tsit.com.tw/ETF",
        ("tsit.com.tw", "www.tsit.com.tw"), "ETF_ANNOUNCEMENTS",
    ),
    "jko": IssuerDividendLandingPage(
        "jko", "https://jkoam.com/",
        ("jkoam.com", "www.jkoam.com"), "ETF_HOME",
    ),
    "franklin": IssuerDividendLandingPage(
        "franklin", "https://www.ftft.com.tw/WebMobile/News/Index",
        ("ftft.com.tw", "www.ftft.com.tw"), "FUND_ANNOUNCEMENTS",
    ),
    "uob": IssuerDividendLandingPage(
        "uob", "https://www.uobam.com.tw/",
        ("uobam.com.tw", "www.uobam.com.tw"), "ETF_HOME",
    ),
    "nomura": IssuerDividendLandingPage(
        "nomura", "https://www.nomurafunds.com.tw/ETFWEB/announcements/24",
        ("nomurafunds.com.tw", "www.nomurafunds.com.tw"), "ETF_ANNOUNCEMENTS",
    ),
    "esun": IssuerDividendLandingPage(
        "esun", "https://www.esunam.com/Service/LatestNews?tab=1",
        ("esunam.com", "www.esunam.com"), "FUND_ANNOUNCEMENTS",
    ),
    "union": IssuerDividendLandingPage(
        "union", "https://www.usitc.com.tw/CustCenter/InfoCenter?PType=2",
        ("usitc.com.tw", "www.usitc.com.tw"), "FUND_ANNOUNCEMENTS",
    ),
    "hnh": IssuerDividendLandingPage(
        "hnh", "https://www.hnitc.com.tw/www3/news/",
        (
            "hnitc.com.tw", "www.hnitc.com.tw",
            "hnfunds.com.tw", "www.hnfunds.com.tw",
        ),
        "FUND_ANNOUNCEMENTS",
    ),
    "allianz": IssuerDividendLandingPage(
        "allianz", "https://tw.allianzgi.com/zh-tw/announcement/product-announcement",
        ("allianzgi.com", "tw.allianzgi.com"), "FUND_ANNOUNCEMENTS",
    ),
    "blackrock": IssuerDividendLandingPage(
        "blackrock", "https://www.blackrock.com/tw/literature/fund-announcement",
        ("blackrock.com", "www.blackrock.com"), "FUND_DOCUMENTS", "PROTECTED",
    ),
    "jpmorgan": IssuerDividendLandingPage(
        "jpmorgan", "https://am.jpmorgan.com/tw/zh/asset-management/twetf/funds/announcements/",
        ("jpmorgan.com", "am.jpmorgan.com"), "ETF_ANNOUNCEMENTS",
    ),
    "alliancebernstein": IssuerDividendLandingPage(
        "alliancebernstein", "https://www.abfunds.com.tw/zh-tw/home.html",
        ("abfunds.com.tw", "www.abfunds.com.tw"), "FUND_ANNOUNCEMENTS",
    ),
}


def get_issuer_dividend_landing_page(
    issuer_key: str,
) -> IssuerDividendLandingPage:
    normalized = issuer_key.strip().lower()
    try:
        return ISSUER_DIVIDEND_LANDING_PAGES[normalized]
    except KeyError as error:
        raise KeyError(f"找不到投信官方公告入口：{normalized}") from error
