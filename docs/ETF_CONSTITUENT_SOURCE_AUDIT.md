# ETF Constituent Source Audit

## Scope and status meanings

The acceptance baseline is the 23-issuer universe in the TWSE ETF issuer
filter. Representative product codes and product types were cross-checked
against the TWSE `t187ap47_L` official fund master on 2026-08-13.

- `AUTOMATED`: a complete official payload is parsed, validated and persisted.
- `FULL_DISCLOSURE_VERIFIED`: the official issuer page exposes complete
  holdings or a PCF, but this repository does not yet automate it.
- `ENTRYPOINT_VERIFIED`: the official product or PCF application exists, but a
  stable complete response and ETF-code mapping still need verification.
- `NOT_APPLICABLE`: the issuer currently has no equity constituent portfolio.

Finding an official page is not equivalent to automation. Only `AUTOMATED`
sources may be imported without additional issuer-specific work. The current
registry has no entrypoint-only issuer: all applicable issuers returned a
complete official holdings or PCF response during this audit, and thirteen sources
now have production adapters.

## Issuer matrix

| Issuer | Example | Status | Locator | Finding |
|---|---:|---|---|---|
| Yuanta | 0050 | `AUTOMATED` | ETF code in path | Complete official `PCF/Daily` adapter |
| Fubon | 006208 | `AUTOMATED` | ETF-code query | PCF-to-assets adapter |
| SinoPac | 00930 | `AUTOMATED` | ETF code in path | Official PCF adapter |
| Mega | 00932 | `AUTOMATED` | Internal fund ID | Catalog mapping plus holdings adapter |
| Cathay | 00878 | `FULL_DISCLOSURE_VERIFIED` | Internal fund code | Official holdings tab |
| First | 00408A | `FULL_DISCLOSURE_VERIFIED` | Internal fund ID | Official asset-weight table |
| Fuh Hwa | 00929 | `AUTOMATED` | Internal fund ID | Catalog mapping plus asset Excel adapter |
| Capital | 00923 | `FULL_DISCLOSURE_VERIFIED` | Internal fund ID | Current HTML response fails the 90% runtime completeness gate |
| Taishin | 00987A | `AUTOMATED` | ETF code in path | Official holdings adapter |
| CTBC | 00891 | `AUTOMATED` | ETF-code query | Official PCF adapter |
| UPAM | 00939 | `FULL_DISCLOSURE_VERIFIED` | Internal fund code | Complete holdings table |
| JKO | 00693U | `NOT_APPLICABLE` | Futures ETF only | Current products are commodity futures trusts |
| Franklin Templeton SinoAm | 00905 | `AUTOMATED` | Internal fund ID | Official catalog and holdings API adapter |
| KGI | 00915 | `FULL_DISCLOSURE_VERIFIED` | Internal fund ID | Complete holdings table |
| UOB | 00918 | `AUTOMATED` | Internal fund ID | Event mapping plus official PCF adapter |
| Nomura | 00944 | `AUTOMATED` | ETF code in request body | Official `GetFundAssets` adapter |
| E.SUN | 009803 | `AUTOMATED` | Internal fund ID | Overview mapping plus official `GetFundAssets` adapter |
| Union | 009804 | `FULL_DISCLOSURE_VERIFIED` | Form selection | Complete holdings table |
| HN | 009808 | `FULL_DISCLOSURE_VERIFIED` | ETFID query plus short-lived system token | Official OpenAPI PCF response |
| Allianz | 00984A | `FULL_DISCLOSURE_VERIFIED` | Antiforgery plus internal fund ID | Official overview and `GetFundAssets` responses |
| BlackRock | 009813 | `FULL_DISCLOSURE_VERIFIED` | Internal product ID | Complete holdings verified; official automation is access-protected |
| J.P. Morgan | 00989A | `AUTOMATED` | ISIN slug | Autocomplete mapping plus official product-data PCF adapter |
| AllianceBernstein | 00404A | `AUTOMATED` | Share-class ISIN | ETF catalog mapping plus reconciled holdings adapter |

Canonical URLs and machine-readable notes live in
`backend/app/data_sources/constituent_source_registry.py`.

## Live API validation evidence

The dynamic sources that required request discovery were exercised against
their official production endpoints on 2026-08-13 and 2026-08-14:

- Nomura `Fund/GetFundAssets` returned 50 stock rows for `00944` and a
  `2026/08/13` data date.
- E.SUN `GetETFOverview` mapped `009803` to internal `FundNo=50`, and
  `GetFundAssets` returned 50 stock rows for `2026/08/13`.
- HN's official OpenAPI defines `GET /Stk/PcfData` with the `ETFID` query.
  Its public short-lived system-token flow returned 60 stock rows plus one
  futures row for `009808`, dated `2026-08-13`.
- Allianz's official OpenAPI defines the antiforgery flow and
  `POST /api/Fund/GetFundAssets`. The overview mapped `00984A` to `E0001`;
  the holdings response returned 122 stock rows plus one futures row for
  `2026/08/13`.
- AllianceBernstein's ETF catalog mapped `00404A` to `TW00000404A5`; its
  holdings API returned 54 equities totaling `89.487277%`. This exactly matched
  the official equity asset total, while the same response separately reported
  futures and options exposure.
- J.P. Morgan's official autocomplete response mapped both current Taiwan ETFs
  to their ISINs. Its product-data response returned 64 equity rows each for
  `00401A` (`92.4829%`) and `00989A` (`98.3042%`), dated `2026-08-13`.
- BlackRock's previously verified complete product holdings remain visible to
  interactive users, but the product page and tested official CSV variants
  returned HTTP 403 on `2026-08-14`. No adapter is enabled while automated
  access remains protected.

These observations prove source availability and request mapping. They are not
runtime guarantees: production adapters must still enforce schema, identity,
date, coverage and failure-mode checks before persisting snapshots.

## External market-data APIs

The published Fugle Market Data endpoints provide instruments, quotes,
snapshots, historical prices and technical indicators. Shioaji provides
contracts, quotes, scanners, trading and account data. Neither published API
currently exposes an ETF-to-constituent list with portfolio weights. They may
still be useful later for price history or read-only account synchronization,
but they are not substitutes for issuer portfolio disclosure.

## Next implementation order

1. Direct ETF-code sources: completed for SinoPac, Taishin, CTBC, Fubon and
   Nomura, including identity, date and minimum-coverage validation.
2. Stable internal-ID discovery: completed for Mega, Fuh Hwa, UOB and E.SUN.
   Franklin Templeton SinoAm is also complete. Revisit Cathay, First and KGI
   when their application responses expose complete stock rows; resolve
   Capital's truncated server response before enabling persistence.
3. Stable product-ID or ISIN discovery: completed for J.P. Morgan and
   AllianceBernstein. Revisit BlackRock only when an officially accessible
   catalog and complete holdings response can be verified without bypassing
   access protection.
4. Session-aware sources: HN's short-lived public system token and Allianz's
   antiforgery cookie/header pair.
5. Form-backed sources such as Union, followed by the remaining issuer-specific
   parsers.
6. Add freshness and multi-issuer coverage gates before calculated overlap is
   allowed to affect assessment scoring.
