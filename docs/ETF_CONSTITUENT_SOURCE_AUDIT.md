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
complete official holdings or PCF response during this audit, and six sources
now have production adapters.

## Issuer matrix

| Issuer | Example | Status | Locator | Finding |
|---|---:|---|---|---|
| Yuanta | 0050 | `AUTOMATED` | ETF code in path | Complete official `PCF/Daily` adapter |
| Fubon | 006208 | `AUTOMATED` | ETF-code query | PCF-to-assets adapter |
| SinoPac | 00930 | `AUTOMATED` | ETF code in path | Official PCF adapter |
| Mega | 00932 | `FULL_DISCLOSURE_VERIFIED` | Internal fund ID | Complete holdings page |
| Cathay | 00878 | `FULL_DISCLOSURE_VERIFIED` | Internal fund code | Official holdings tab |
| First | 00408A | `FULL_DISCLOSURE_VERIFIED` | Internal fund ID | Official asset-weight table |
| Fuh Hwa | 00929 | `FULL_DISCLOSURE_VERIFIED` | Internal fund ID | Complete holdings page |
| Capital | 00923 | `FULL_DISCLOSURE_VERIFIED` | Internal fund ID | Complete buyback holdings |
| Taishin | 00987A | `AUTOMATED` | ETF code in path | Official holdings adapter |
| CTBC | 00891 | `AUTOMATED` | ETF-code query | Official PCF adapter |
| UPAM | 00939 | `FULL_DISCLOSURE_VERIFIED` | Internal fund code | Complete holdings table |
| JKO | 00693U | `NOT_APPLICABLE` | Futures ETF only | Current products are commodity futures trusts |
| Franklin Templeton SinoAm | 00905 | `FULL_DISCLOSURE_VERIFIED` | Internal fund ID | Official holdings tab |
| KGI | 00915 | `FULL_DISCLOSURE_VERIFIED` | Internal fund ID | Complete holdings table |
| UOB | 00918 | `FULL_DISCLOSURE_VERIFIED` | Internal fund ID | Official PCF page |
| Nomura | 00944 | `AUTOMATED` | ETF code in request body | Official `GetFundAssets` adapter |
| E.SUN | 009803 | `FULL_DISCLOSURE_VERIFIED` | Internal fund ID | Overview mapping plus official `GetFundAssets` response |
| Union | 009804 | `FULL_DISCLOSURE_VERIFIED` | Form selection | Complete holdings table |
| HN | 009808 | `FULL_DISCLOSURE_VERIFIED` | ETFID query plus short-lived system token | Official OpenAPI PCF response |
| Allianz | 00984A | `FULL_DISCLOSURE_VERIFIED` | Antiforgery plus internal fund ID | Official overview and `GetFundAssets` responses |
| BlackRock | 009813 | `FULL_DISCLOSURE_VERIFIED` | Internal product ID | Complete holdings table |
| J.P. Morgan | 00989A | `FULL_DISCLOSURE_VERIFIED` | ISIN slug | Complete multi-page holdings |
| AllianceBernstein | 00404A | `FULL_DISCLOSURE_VERIFIED` | Share-class ISIN | Official holdings and basket responses |

Canonical URLs and machine-readable notes live in
`backend/app/data_sources/constituent_source_registry.py`.

## Live API validation evidence

The dynamic sources that required request discovery were exercised against
their official production endpoints on 2026-08-13:

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
- AllianceBernstein's official API returned complete domestic holdings for
  share-class ISIN `TW00000404A5`, plus the matching `2026-08-13` basket.

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
2. Stable internal-ID or ISIN discovery: Mega, Cathay, First, Fuh Hwa,
   Capital, Franklin Templeton SinoAm, KGI, UOB, E.SUN, BlackRock, J.P. Morgan
   and AllianceBernstein.
3. Session-aware sources: HN's short-lived public system token and Allianz's
   antiforgery cookie/header pair.
4. Form-backed sources such as Union, followed by the remaining issuer-specific
   parsers.
5. Add freshness and multi-issuer coverage gates before calculated overlap is
   allowed to affect assessment scoring.
