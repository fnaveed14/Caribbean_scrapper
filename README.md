# 🌊 Caribbean Regional Report — Data Scraper

IOM RCO Caribbean | 2025 Report Update Tool

Monitors **37 official and international data sources** across **5 themes** and **24 territories**,
detecting whether new 2024/2025 data is available so you can update the report.

---

## Quick Start

### Mac / Linux
1. Open Terminal
2. `cd` into this folder
3. Run: `bash run.sh`

Or make it executable once and double-click:
```bash
chmod +x run.sh
```

### Windows
Double-click `run.bat`

The first run installs packages into a local `.venv` folder (~1 minute).
After that, it launches in seconds.

---

## What it does

Each time you run the scraper it:

1. **Visits each source URL** (national stats offices, UNHCR, R4V, World Bank KNOMAD, IDB, central banks…)
2. **Checks for update signals** — looks for 2024/2025 year mentions and theme-specific keywords
3. **Detects page changes** — compares a content hash to the previous run so you know if *anything* changed
4. **Shows a status** for each source:
   - ✅ Updated — strong keyword matches, likely new data
   - 🔍 Check — partial match, worth a manual look
   - ⚠️ No match — page loaded but no update signals
   - 🚫 Blocked — site blocked the automated request (visit manually)
   - ❌ Error — connection problem

---

## Themes covered

| Theme | Sources |
|-------|---------|
| Migrant Stocks & Demographics | UNDESA, CBS Aruba, SIB Belize, CBS Curaçao, STATIN Jamaica, Barbados Stats, Bahamas Stats, CSO T&T, ABS Suriname, CBS Netherlands (BES), World Bank |
| Vulnerable Populations | UNHCR (all countries), R4V Platform, IOM DTM |
| Intraregional Mobility | CBS Aruba, CBS Curaçao, UNDESA bilateral, IDB permits |
| Remittances | World Bank KNOMAD, IDB, ECCB, Bank of Jamaica, Central Banks (Barbados, Belize, T&T, Guyana, Bahamas, Curaçao/SXM), CIMA Cayman |
| Regular Pathways | CIP Antigua, IDB permits, SIB Belize LFS, Grenada CBI, SKN CIU, Saint Lucia CIP, ESO Cayman, DIMAS Curaçao, R4V permits |

---

## Files

```
caribbean_scraper/
├── app.py               ← main Streamlit app
├── requirements.txt     ← Python dependencies
├── run.sh               ← Mac/Linux launcher
├── run.bat              ← Windows launcher
└── data/
    ├── scrape_cache.json     ← latest results (auto-created)
    ├── scrape_history.json   ← run history log (auto-created)
    └── *.xlsx                ← exports you generate
```

---

## Export

Click **📥 Export results to Excel** in the sidebar to download a multi-sheet Excel file with:
- Master sheet with all sources × countries
- One sheet per theme

---

## Tips

- **Blocked sources** — some government sites block scrapers. For these, visit the URL manually using the link shown in the app.
- **Run regularly** — the scraper saves a content hash each run, so if a page changes between runs you'll see 🔔 Page content changed.
- **Adjust timeout** — slow connections? Increase the timeout slider in the sidebar.
- **Filter** — use the theme and country dropdowns to scrape only the sources relevant to what you're currently updating.

---

## Requirements

- Python 3.9 or newer
- Internet connection
- `run.sh` / `run.bat` handles everything else automatically
