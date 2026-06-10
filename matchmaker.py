#!/usr/bin/env python3
"""
TradeAI Matchmaker — global supply/demand matching prototype.

Data source: UN Comtrade public API (no key, preview tier, official
government-reported customs data).

Modes:
  buyers    — you are an exporter: find the best import markets for a product
  suppliers — you are an importer: find the best source countries for a product

Usage:
  python3 matchmaker.py --hs 0901 --mode buyers --country VNM [--year 2023]
  python3 matchmaker.py --hs 8517 --mode suppliers --country USA
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse

BASE = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
REF_REPORTERS = "https://comtradeapi.un.org/files/v1/app/reference/Reporters.json"
REF_PARTNERS = "https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json"
REF_HS = "https://comtradeapi.un.org/files/v1/app/reference/H6.json"
WITS_TRN = ("https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN"
            "/reporter/{rep}/partner/000/product/{hs6}/year/{year}/datatype/reported")
WITS_COUNTRIES = "https://wits.worldbank.org/API/V1/wits/datasource/trn/country/ALL"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")


def http_json(url: str, retries: int = 3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TradeAI-matchmaker/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def cached_json(name: str, url: str):
    path = os.path.join(CACHE_DIR, name)
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < 30 * 86400:
        with open(path) as f:
            return json.load(f)
    data = http_json(url)
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)
    return data


def load_countries():
    """id -> (iso3, name) for all reporter/partner areas."""
    out = {}
    for name, url in [("reporters.json", REF_REPORTERS), ("partners.json", REF_PARTNERS)]:
        data = cached_json(name, url)
        for row in data.get("results", data if isinstance(data, list) else []):
            cid = str(row.get("id"))
            iso = row.get("reporterCodeIsoAlpha3") or row.get("PartnerCodeIsoAlpha3") or ""
            label = row.get("text") or row.get("reporterDesc") or ""
            out[cid] = (iso, label)
    return out


def comtrade(params: dict):
    qs = urllib.parse.urlencode(params)
    data = http_json(f"{BASE}?{qs}")
    time.sleep(1.2)  # stay polite on the public tier
    return data.get("data", [])


def world_trade_by_country(hs: str, year: int, flow: str):
    """Per-country totals of `hs` trade with world: {code: {"v": usd, "kg": net_weight}}."""
    rows = comtrade({
        "reporterCode": "", "period": year, "cmdCode": hs,
        "flowCode": flow, "partnerCode": 0, "maxRecords": 500,
        "motCode": 0, "customsCode": "C00", "partner2Code": 0,
    })
    totals = {}
    for r in rows:
        code = str(r["reporterCode"])
        t = totals.setdefault(code, {"v": 0, "kg": 0})
        t["v"] += r.get("primaryValue") or 0
        t["kg"] += r.get("netWgt") or 0
    return totals


def country_partners(hs: str, year: int, reporter: str, flow: str):
    """One country's trade of `hs` broken down by partner country."""
    rows = comtrade({
        "reporterCode": reporter, "period": year, "cmdCode": hs,
        "flowCode": flow, "partnerCode": "", "maxRecords": 500,
        "motCode": 0, "customsCode": "C00", "partner2Code": 0,
    })
    out = {}
    for r in rows:
        p = str(r["partnerCode"])
        if p == "0":  # world aggregate
            continue
        out[p] = out.get(p, 0) + (r.get("primaryValue") or 0)
    return out


def hs_search(keyword: str, limit: int = 15):
    """Free-text product keyword -> candidate HS codes (Phase 2)."""
    data = cached_json("hs.json", REF_HS)
    rows = data.get("results", [])
    terms = [t.lower() for t in keyword.split()]
    hits = []
    for r in rows:
        cid, text = str(r.get("id", "")), (r.get("text") or "").lower()
        if not cid.isdigit():
            continue
        if all(t in text for t in terms):
            hits.append({"hs": cid, "description": r.get("text", "")})
    hits.sort(key=lambda h: (len(h["hs"]), h["hs"]))  # broader headings first
    return hits[:limit]


def wits_country_map():
    """ISO3 -> WITS/ISO numeric reporter code (real countries only)."""
    path = os.path.join(CACHE_DIR, "wits_countries.json")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < 30 * 86400:
        with open(path) as f:
            return json.load(f)
    import re
    req = urllib.request.Request(WITS_COUNTRIES, headers={"User-Agent": "TradeAI-matchmaker/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        xml = r.read().decode()
    out = {}
    for m in re.finditer(
            r'<wits:country countrycode="(\d+)"[^>]*isgroup="No"[^>]*>.*?'
            r'<wits:iso3Code>([A-Z]{3})</wits:iso3Code>', xml, re.S):
        out[m.group(2)] = m.group(1)
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump(out, f)
    return out


EU_MEMBERS = {
    "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA",
    "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD",
    "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE",
}


def mfn_tariff(iso3: str, hs6: str, year: int):
    """Market's MFN simple-average tariff (%) on an HS6 line, from WITS/TRAINS.

    Tries `year` then two prior years (tariff reporting lags trade data).
    EU members share the common external tariff, reported under "EUN".
    Returns {"rate": float, "year": int} or None.
    """
    import re
    iso3 = iso3.upper()
    if iso3 in EU_MEMBERS:
        iso3 = "EUN"
    rep = wits_country_map().get(iso3)
    if not rep:
        return None
    for y in (year, year - 1, year - 2):
        url = WITS_TRN.format(rep=rep, hs6=hs6, year=y)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TradeAI-matchmaker/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                xml = r.read().decode()
        except Exception:
            continue
        time.sleep(0.6)
        for obs in re.findall(r"<Obs ([^>]+)/>", xml):
            attrs = dict(re.findall(r'(\w+)="([^"]*)"', obs))
            if attrs.get("TARIFFTYPE") == "MFN" and "OBS_VALUE" in attrs:
                return {"rate": float(attrs["OBS_VALUE"]), "year": y}
    return None


def market_analysis(hs: str, year: int, me: str, mode: str,
                    top: int = 15, trend_years: int = 0,
                    tariff_hs6: str = None, countries: dict = None):
    """Core engine: ranked markets/sources, optionally with multi-year trend,
    unit prices ($/kg) and MFN tariff overlay.

    Returns list of dicts; when trend_years > 0 each row gains
    `history` {year: usd} and `cagr_pct`; when tariff_hs6 is set (buyers mode)
    each row gains `mfn_tariff_pct` / `tariff_year` for that HS6 line.
    """
    market_flow = "M" if mode == "buyers" else "X"
    my_flow = "X" if mode == "buyers" else "M"

    world = world_trade_by_country(hs, year, market_flow)
    mine = country_partners(hs, year, me, my_flow)
    world.pop(me, None)
    ranked = sorted(world.items(), key=lambda kv: -kv[1]["v"])[:top]

    history = {}
    if trend_years > 0:
        for y in range(year - trend_years, year):
            history[y] = world_trade_by_country(hs, y, market_flow)

    results = []
    for cid, tot in ranked:
        value, kg = tot["v"], tot["kg"]
        existing = mine.get(cid, 0)
        share = existing / value * 100 if value else 0
        row = {
            "code": cid,
            "market_usd": round(value), "current_trade_usd": round(existing),
            "penetration_pct": round(share, 2),
            "unit_price_usd_kg": round(value / kg, 2) if kg > 1000 else None,
            "opportunity": "NEW" if existing == 0 else ("GROW" if share < 5 else "ESTABLISHED"),
        }
        if trend_years > 0:
            row["history"] = {y: round(history[y].get(cid, {}).get("v", 0)) for y in history}
            row["history"][year] = round(value)
            first = history.get(year - trend_years, {}).get(cid, {}).get("v", 0)
            if first > 0 and value > 0:
                row["cagr_pct"] = round(((value / first) ** (1 / trend_years) - 1) * 100, 1)
            else:
                row["cagr_pct"] = None
        if tariff_hs6 and countries:
            iso3 = countries.get(cid, ("",))[0]
            t = mfn_tariff(iso3, tariff_hs6, year - 1) if iso3 else None
            row["mfn_tariff_pct"] = t["rate"] if t else None
            row["tariff_year"] = t["year"] if t else None
        results.append(row)
    return results


def iso_to_code(iso: str, countries: dict) -> str:
    iso = iso.upper()
    # Several ISO3 codes also match dissolved entities, e.g. VNM matches both
    # "Viet Nam" (704) and "Rep. of Vietnam (...1974)" (866) — skip historical
    # entries, recognizable by the "(...year)" suffix in their label.
    candidates = [
        cid for cid, (i3, label) in countries.items()
        if i3 == iso and "(..." not in label
    ]
    if candidates:
        return candidates[0]
    sys.exit(f"Unknown country ISO3 code: {iso}")


def fmt_usd(v: float) -> str:
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    if v >= 1e6:
        return f"${v/1e6:.1f}M"
    return f"${v/1e3:.0f}K"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hs", help="HS commodity code, e.g. 0901")
    ap.add_argument("--hs-search", help="free-text product keyword -> HS codes")
    ap.add_argument("--mode", choices=["buyers", "suppliers"])
    ap.add_argument("--country", help="Your country, ISO3 (VNM, USA...)")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--trend", type=int, default=0, metavar="N",
                    help="also fetch N prior years and compute CAGR")
    ap.add_argument("--tariff-hs6", metavar="HS6",
                    help="overlay each market's MFN tariff on this HS6 line (WITS/TRAINS)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    if args.hs_search:
        hits = hs_search(args.hs_search)
        if args.json:
            print(json.dumps(hits, indent=2, ensure_ascii=False))
        else:
            for h in hits:
                print(f"{h['hs']:<8} {h['description']}")
        return

    if not (args.hs and args.mode and args.country):
        ap.error("--hs, --mode and --country are required (or use --hs-search)")

    countries = load_countries()
    me = iso_to_code(args.country, countries)

    def cname(cid):
        iso, label = countries.get(str(cid), ("", f"#{cid}"))
        return f"{label} ({iso})" if iso else label

    results = market_analysis(args.hs, args.year, me, args.mode,
                              top=args.top, trend_years=args.trend,
                              tariff_hs6=args.tariff_hs6, countries=countries)
    for r in results:
        r["country"] = cname(r["code"])
        r["iso"] = countries.get(r["code"], ("",))[0]

    if args.json:
        print(json.dumps({
            "hs": args.hs, "year": args.year, "mode": args.mode,
            "country": args.country, "results": results,
        }, indent=2, ensure_ascii=False))
        return

    market_word = "import markets" if args.mode == "buyers" else "source countries"
    trend_col = f" {'CAGR':>6}" if args.trend else ""
    price_col = f" {'$/kg':>7}"
    tariff_col = f" {'MFN':>6}" if args.tariff_hs6 else ""
    print(f"\nTop {market_word} for HS {args.hs} — {args.year}, "
          f"viewpoint: {cname(me)} ({args.mode})\n")
    print(f"{'#':>2}  {'Country':<32} {'Market size':>12} {'Your trade':>12} "
          f"{'Share':>7}{trend_col}{price_col}{tariff_col}  Status")
    for i, r in enumerate(results, 1):
        cagr = ""
        if args.trend:
            cagr = f" {r['cagr_pct']:>5.1f}%" if r.get("cagr_pct") is not None else "    n/a"
        up = r.get("unit_price_usd_kg")
        price = f" {up:>7.2f}" if up is not None else f" {'n/a':>7}"
        tariff = ""
        if args.tariff_hs6:
            tp = r.get("mfn_tariff_pct")
            tariff = f" {tp:>5.1f}%" if tp is not None else f" {'n/a':>6}"
        print(f"{i:>2}  {r['country']:<32} {fmt_usd(r['market_usd']):>12} "
              f"{fmt_usd(r['current_trade_usd']):>12} {r['penetration_pct']:>6.1f}%"
              f"{cagr}{price}{tariff}  {r['opportunity']}")
    print("\nSource: UN Comtrade (official customs statistics); tariffs: WITS/TRAINS.")


if __name__ == "__main__":
    main()
