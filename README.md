# TradeAI Matchmaker — Global Supply/Demand Matching

AI tool that matches supply and demand across industries and product
categories globally, connecting buyers/importers with sellers/exporters.

## Status: Phase 1 prototype (working)

`matchmaker.py` answers two core questions from official customs data:

- **buyers** mode — "I export product X from country Y: which markets should
  I target?" Ranks the world's import markets for the HS code, overlays your
  country's current exports to each, and flags each market `NEW` (no
  presence), `GROW` (<5% penetration) or `ESTABLISHED`.
- **suppliers** mode — "I import product X into country Y: where should I
  source from?" Ranks the world's exporters and shows how much you already
  buy from each.

```bash
python3 matchmaker.py --hs 0901 --mode buyers --country VNM --year 2023
python3 matchmaker.py --hs 9403 --mode suppliers --country USA
python3 matchmaker.py --hs 8517 --mode buyers --country VNM --json   # machine-readable
```

## Data sources (trustworthy by design)

| Source | What | Access |
|---|---|---|
| **UN Comtrade** (used now) | Official customs statistics reported by ~200 governments | Public API, free preview tier; free API key raises limits |
| WTO Stats / Tariff data | Tariffs, trade policy | Free API — Phase 2 |
| ITC Trade Map / Export Potential Map (UN/WTO joint agency) | Trade indicators, **verified company directories** | Free registration — Phase 2 |
| World Bank WITS | Mirror of Comtrade + tariffs (GDP, logistics index) | Free API — Phase 2 |
| National chambers of commerce, EuroCham/AmCham, VCCI, trade promotion agencies (VIETRADE, JETRO, KOTRA…) | Vetted member/company lists | Per-source — Phase 3 |

Everything is government- or IGO-published; no scraped marketplace data, so
results are defensible in front of a client.

## Architecture / Roadmap

```
Phase 1 (done)    Market matching engine
                  HS code + country + direction → ranked markets/sources
                  with penetration analysis (UN Comtrade)

Phase 2           Insight layer
                  - Trends: 5-year CAGR per market, unit-price benchmarks
                  - Tariff overlay (WTO/WITS): effective duty per market pair
                  - HS-code finder: free-text product → HS candidates
                  - Claude-generated market briefs: combine the numbers into
                    a written analysis per query

Phase 3           Counterparty lists
                  - ITC Trade Map company directories per HS+country
                  - Chamber-of-commerce member lists, trade-fair exhibitor
                    lists, national exporter registries
                  - Scoring: size, history, certifications → ranked
                    shortlist of potential suppliers/clients per query

Phase 4           Product wrapper
                  - Query via WhatsApp ("tìm buyer cà phê ở EU") → agent
                    runs engine, replies with brief + shortlist file
                  - Watchlists: alert when a market's imports jump
```

## Known caveats (prototype)

- Public Comtrade preview caps at 500 rows/query — fine for top-N rankings,
  use a free API key for full detail.
- Mirror discrepancies: country A's reported imports from B can exceed B's
  reported exports (valuation CIF vs FOB, routing) — shares >100% can appear;
  Phase 2 will reconcile mirror flows.
- Company-level matching (actual buyer/seller names) needs Phase 3 sources;
  customs data is country-level only.
