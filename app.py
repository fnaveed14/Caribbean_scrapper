"""
Caribbean Regional Report — Data Scraper & Monitor
Run: streamlit run app.py
"""

import streamlit as st
import requests
import json
import time
import os
import hashlib
from datetime import datetime, date
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Caribbean Data Scraper",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CACHE_FILE = DATA_DIR / "scrape_cache.json"
HISTORY_FILE = DATA_DIR / "scrape_history.json"
SNAPSHOT_FILE = DATA_DIR / "latest_snapshot.json"

# ── Source catalogue ───────────────────────────────────────────────────────────
# Each entry: id, theme, countries, label, url, check_pattern (text to look for),
#             data_type (what field it updates), source_org, notes
SOURCES = [

    # ── THEME 1: Migrant Stocks & Demographics ────────────────────────────────
    {
        "id": "undesa_migrant_stock",
        "theme": "Migrant Stocks & Demographics",
        "countries": ["ALL"],
        "label": "UNDESA International Migrant Stock",
        "url": "https://www.un.org/development/desa/pd/content/international-migrant-stock",
        "check_patterns": ["2024", "migrant stock", "update", "revision"],
        "data_fields": ["Total Migrant Stock", "Male", "Female", "Net Migration"],
        "source_org": "UNDESA",
        "notes": "Global estimates; look for the 2024 revision release.",
    },
    {
        "id": "cbs_aruba_population",
        "theme": "Migrant Stocks & Demographics",
        "countries": ["Aruba"],
        "label": "CBS Aruba — Population & Migration Tables",
        "url": "https://cbs.aw/wp/index.php/category/population/",
        "check_patterns": ["2024", "2025", "foreign-born", "migration", "population"],
        "data_fields": ["Total Migrant Stock", "Male", "Female", "Children 0-19", "Elderly >60"],
        "source_org": "CBS Aruba",
        "notes": "Annual population tables incl. foreign-born by nationality and sex.",
    },
    {
        "id": "stats_barbados_census",
        "theme": "Migrant Stocks & Demographics",
        "countries": ["Barbados"],
        "label": "Barbados Statistical Service — Census 2020",
        "url": "https://stats.gov.bb/",
        "check_patterns": ["census", "2024", "2025", "migration", "population"],
        "data_fields": ["Total Migrant Stock", "Male", "Female"],
        "source_org": "Barbados Statistical Service",
        "notes": "2020 census published 2024; contains foreign-born population by CoB.",
    },
    {
        "id": "sib_belize_census",
        "theme": "Migrant Stocks & Demographics",
        "countries": ["Belize"],
        "label": "SIB Belize — 2022 Population & Housing Census",
        "url": "https://sib.org.bz/census/2022-census/",
        "check_patterns": ["census", "2022", "2024", "2025", "migration", "foreign"],
        "data_fields": ["Total Migrant Stock", "Male", "Female"],
        "source_org": "Statistical Institute of Belize",
        "notes": "2022 census fully published; includes migration tables.",
    },
    {
        "id": "cbs_curacao_population",
        "theme": "Migrant Stocks & Demographics",
        "countries": ["Curaçao"],
        "label": "CBS Curaçao — Population by Nationality (SIM)",
        "url": "https://www.cbs.cw/publications/population",
        "check_patterns": ["2024", "2025", "nationality", "population", "migration"],
        "data_fields": ["Total Migrant Stock", "Male", "Female"],
        "source_org": "CBS Curaçao",
        "notes": "SIM register data; annual updates. Check for 2024 edition.",
    },
    {
        "id": "eso_cayman_population",
        "theme": "Migrant Stocks & Demographics",
        "countries": ["Cayman Islands"],
        "label": "ESO Cayman Islands — Population Statistics",
        "url": "https://www.eso.ky/",
        "check_patterns": ["2024", "2025", "population", "migration", "work permit"],
        "data_fields": ["Total Migrant Stock", "Total Population in latest Census"],
        "source_org": "Economics and Statistics Office (Cayman)",
        "notes": "ESO publishes annual population statistics including residents by nationality.",
    },
    {
        "id": "stats_jamaica",
        "theme": "Migrant Stocks & Demographics",
        "countries": ["Jamaica"],
        "label": "STATIN Jamaica — Population & Migration",
        "url": "https://statinja.gov.jm/",
        "check_patterns": ["census", "2022", "2024", "migration", "population", "foreign"],
        "data_fields": ["Total Migrant Stock", "Net Migration"],
        "source_org": "STATIN Jamaica",
        "notes": "Jamaica 2022 census — check for final migration tables.",
    },
    {
        "id": "stats_bahamas",
        "theme": "Migrant Stocks & Demographics",
        "countries": ["The Bahamas"],
        "label": "Department of Statistics Bahamas",
        "url": "https://statistics.bahamas.gov.bs/",
        "check_patterns": ["2022", "2024", "census", "migration", "population"],
        "data_fields": ["Total Migrant Stock", "Total Population in latest Census"],
        "source_org": "Dept. of Statistics Bahamas",
        "notes": "2022 census conducted; check for migration tables.",
    },
    {
        "id": "cso_tt",
        "theme": "Migrant Stocks & Demographics",
        "countries": ["Trinidad and Tobago"],
        "label": "CSO Trinidad and Tobago",
        "url": "https://cso.gov.tt/",
        "check_patterns": ["2024", "2025", "migration", "population", "census"],
        "data_fields": ["Total Migrant Stock", "Net Migration", "Total Population in latest Census"],
        "source_org": "CSO Trinidad and Tobago",
        "notes": "Census and continuous population data.",
    },
    {
        "id": "abs_suriname",
        "theme": "Migrant Stocks & Demographics",
        "countries": ["Suriname"],
        "label": "ABS Suriname — Population Statistics",
        "url": "https://www.statistics-suriname.org/",
        "check_patterns": ["2023", "2024", "2025", "migration", "population", "bevolking"],
        "data_fields": ["Total Migrant Stock", "Net Migration"],
        "source_org": "ABS Suriname",
        "notes": "Check for 2022/23 population data.",
    },
    {
        "id": "cbs_nl_bes",
        "theme": "Migrant Stocks & Demographics",
        "countries": ["Saba", "Sint Eustatius"],
        "label": "CBS Netherlands — BES Islands Statistics",
        "url": "https://www.cbs.nl/en-gb/our-services/methods/definitions/bes-islands",
        "check_patterns": ["2024", "2025", "BES", "Saba", "Sint Eustatius", "population"],
        "data_fields": ["Total Migrant Stock", "Total Population in latest Census"],
        "source_org": "CBS Netherlands",
        "notes": "Saba and Sint Eustatius statistics covered by CBS Netherlands.",
    },
    {
        "id": "worldbank_population",
        "theme": "Migrant Stocks & Demographics",
        "countries": ["ALL"],
        "label": "World Bank — Population Estimates & Projections",
        "url": "https://databank.worldbank.org/source/population-estimates-and-projections",
        "check_patterns": ["2024", "2025", "Caribbean", "population"],
        "data_fields": ["Total Population in latest Census", "Net Migration"],
        "source_org": "World Bank",
        "notes": "Cross-check population denominators for % calculations.",
    },

    # ── THEME 2: Vulnerable Populations ──────────────────────────────────────
    {
        "id": "unhcr_refugee_stats",
        "theme": "Vulnerable Populations",
        "countries": ["ALL"],
        "label": "UNHCR Refugee Statistics Portal — All Caribbean",
        "url": "https://www.unhcr.org/refugee-statistics/",
        "check_patterns": ["2024", "2025", "refugees", "asylum", "Caribbean"],
        "data_fields": ["Refugees and Asylum Seekers (UNHCR)", "Male", "Female", "Children <18"],
        "source_org": "UNHCR",
        "notes": "Filter by country of asylum for each territory. Updates mid-year and end-year.",
    },
    {
        "id": "r4v_platform",
        "theme": "Vulnerable Populations",
        "countries": ["Aruba", "Curaçao", "Trinidad and Tobago", "Guyana", "Belize",
                      "Barbados", "Sint Maarten", "Suriname"],
        "label": "R4V — Venezuelan Refugees & Migrants in the Region",
        "url": "https://www.r4v.info/en",
        "check_patterns": ["2024", "2025", "Venezuela", "refugees", "migrants", "Caribbean"],
        "data_fields": ["R4V (only for Venezuela)", "Total Number of Vulnerable Populations"],
        "source_org": "R4V Platform",
        "notes": "R4V updates quarterly. Check for latest Caribbean-specific factsheet.",
    },
    {
        "id": "dtm_iom_caribbean",
        "theme": "Vulnerable Populations",
        "countries": ["Trinidad and Tobago", "Guyana", "Sint Maarten", "Suriname",
                      "Belize", "Jamaica"],
        "label": "IOM DTM — Latin America and Caribbean",
        "url": "https://dtm.iom.int/latin-america-and-caribbean",
        "check_patterns": ["2024", "2025", "Caribbean", "displacement", "mobility"],
        "data_fields": ["Total Number of Vulnerable Populations", "Government Data"],
        "source_org": "IOM DTM",
        "notes": "DTM mobility tracking reports for the Caribbean sub-region.",
    },
    {
        "id": "unhcr_tt",
        "theme": "Vulnerable Populations",
        "countries": ["Trinidad and Tobago"],
        "label": "UNHCR Trinidad and Tobago Country Page",
        "url": "https://www.unhcr.org/countries/trinidad-and-tobago",
        "check_patterns": ["2024", "2025", "Venezuela", "refugees", "asylum"],
        "data_fields": ["Refugees and Asylum Seekers (UNHCR)", "R4V (only for Venezuela)"],
        "source_org": "UNHCR",
        "notes": "Largest Venezuelan population in Caribbean; UNHCR publishes detailed T&T data.",
    },
    {
        "id": "unhcr_guyana",
        "theme": "Vulnerable Populations",
        "countries": ["Guyana"],
        "label": "UNHCR Guyana Country Page",
        "url": "https://www.unhcr.org/countries/guyana",
        "check_patterns": ["2024", "2025", "refugees", "asylum", "Venezuela"],
        "data_fields": ["Refugees and Asylum Seekers (UNHCR)"],
        "source_org": "UNHCR",
        "notes": "Check for updated 2024 data.",
    },

    # ── THEME 3: Intraregional Mobility ──────────────────────────────────────
    {
        "id": "cbs_aruba_migration_flows",
        "theme": "Intraregional Mobility",
        "countries": ["Aruba"],
        "label": "CBS Aruba — Immigration & Emigration by Country of Birth/Sex",
        "url": "https://cbs.aw/wp/index.php/category/population/",
        "check_patterns": ["2024", "2025", "immigration", "emigration", "migration"],
        "data_fields": ["Emigration", "Male-Emigrants", "Female-Emigrants",
                        "Immigration", "Male-Immigrants", "Female-Immigrants"],
        "source_org": "CBS Aruba",
        "notes": "CBS Aruba publishes quarterly and annual immigration/emigration tables.",
    },
    {
        "id": "cbs_curacao_mobility",
        "theme": "Intraregional Mobility",
        "countries": ["Curaçao"],
        "label": "CBS Curaçao — Emigration & Immigration by Country",
        "url": "https://www.cbs.cw/publications/population",
        "check_patterns": ["2020", "2021", "2022", "2023", "2024", "emigration", "immigration"],
        "data_fields": ["Emigration", "Male-Emigrants", "Female-Emigrants",
                        "Immigration", "Male-Immigrants", "Female-Immigrants"],
        "source_org": "CBS Curaçao",
        "notes": "Data last available to 2019 in prior round. Check for 2020–2024 updates.",
    },
    {
        "id": "undesa_bilateral",
        "theme": "Intraregional Mobility",
        "countries": ["ALL"],
        "label": "UNDESA — Bilateral Migration Stock Data",
        "url": "https://www.un.org/development/desa/pd/content/international-migrant-stock",
        "check_patterns": ["bilateral", "2024", "origin", "destination"],
        "data_fields": ["Emigration", "Immigration"],
        "source_org": "UNDESA",
        "notes": "Bilateral stock data can proxy flow patterns for countries without flow data.",
    },
    {
        "id": "idb_migration_permits",
        "theme": "Intraregional Mobility",
        "countries": ["ALL"],
        "label": "IDB — Migration Flows in LAC: Statistics on Permits",
        "url": "https://publications.iadb.org/en/migration-flows-latin-america-caribbean-statistics-permits-migrants",
        "check_patterns": ["2024", "2025", "permits", "Caribbean", "migration"],
        "data_fields": ["Immigration"],
        "source_org": "Inter-American Development Bank",
        "notes": "IDB updates this series annually — check for 2024/2025 edition.",
    },

    # ── THEME 4: Remittances ──────────────────────────────────────────────────
    {
        "id": "knomad_remittance_brief",
        "theme": "Remittances",
        "countries": ["ALL"],
        "label": "World Bank KNOMAD — Migration & Development Brief (latest)",
        "url": "https://www.knomad.org/publication/migration-development-brief",
        "check_patterns": ["2024", "2025", "remittance", "Caribbean", "brief"],
        "data_fields": ["Inflows (US$ million)", "Outflows (US$ million)",
                        "Inflows % of GDP", "Outflows % of GDP"],
        "source_org": "World Bank KNOMAD",
        "notes": "Brief 42 expected mid-2025 covering 2024 data. Download the Excel file.",
    },
    {
        "id": "idb_remittances_lac",
        "theme": "Remittances",
        "countries": ["ALL"],
        "label": "IDB — Remittances to Latin America and the Caribbean 2024",
        "url": "https://publications.iadb.org/en/remittances-latin-america-and-caribbean-2024",
        "check_patterns": ["2024", "2025", "remittances", "Caribbean"],
        "data_fields": ["Inflows (US$ million)"],
        "source_org": "Inter-American Development Bank",
        "notes": "IDB publishes annual LAC remittances report covering Caribbean territories.",
    },
    {
        "id": "eccb_bop",
        "theme": "Remittances",
        "countries": ["Antigua and Barbuda", "Dominica", "Grenada", "Saint Kitts and Nevis",
                      "Saint Lucia", "Saint Vincent and the Grenadines"],
        "label": "Eastern Caribbean Central Bank — Balance of Payments",
        "url": "https://www.eccb-centralbank.org/statistics",
        "check_patterns": ["2024", "2025", "remittances", "balance of payments", "transfers"],
        "data_fields": ["Inflows (US$ million)", "Outflows (US$ million)"],
        "source_org": "ECCB",
        "notes": "ECCB covers all OECS members — one-stop source for remittance flows.",
    },
    {
        "id": "boj_remittances",
        "theme": "Remittances",
        "countries": ["Jamaica"],
        "label": "Bank of Jamaica — Remittance Statistics 2024",
        "url": "https://boj.org.jm/statistics/external-sector/",
        "check_patterns": ["2024", "2025", "remittances", "transfers"],
        "data_fields": ["Inflows (US$ million)"],
        "source_org": "Bank of Jamaica",
        "notes": "BOJ publishes monthly and annual remittance data. Jamaica is top recipient.",
    },
    {
        "id": "central_bank_barbados",
        "theme": "Remittances",
        "countries": ["Barbados"],
        "label": "Central Bank of Barbados — Balance of Payments",
        "url": "https://www.centralbank.org.bb/statistics",
        "check_patterns": ["2024", "2025", "remittances", "transfers", "BOP"],
        "data_fields": ["Inflows (US$ million)", "Outflows (US$ million)"],
        "source_org": "Central Bank of Barbados",
        "notes": "Official source for remittance flows.",
    },
    {
        "id": "central_bank_belize",
        "theme": "Remittances",
        "countries": ["Belize"],
        "label": "Central Bank of Belize — Balance of Payments 2024",
        "url": "https://www.centralbank.org.bz/statistics",
        "check_patterns": ["2024", "2025", "remittances", "transfers"],
        "data_fields": ["Inflows (US$ million)", "Outflows (US$ million)"],
        "source_org": "Central Bank of Belize",
        "notes": "Official BOP data including remittances.",
    },
    {
        "id": "cbcs_curacao_sxm",
        "theme": "Remittances",
        "countries": ["Curaçao", "Sint Maarten"],
        "label": "Central Bank Curaçao & Sint Maarten — BOP",
        "url": "https://www.centralbank.cw/statistics",
        "check_patterns": ["2024", "2025", "remittances", "transfers", "BOP"],
        "data_fields": ["Inflows (US$ million)", "Outflows (US$ million)"],
        "source_org": "CBCS",
        "notes": "CBCS covers both Curaçao and Sint Maarten.",
    },
    {
        "id": "central_bank_tt",
        "theme": "Remittances",
        "countries": ["Trinidad and Tobago"],
        "label": "Central Bank of Trinidad and Tobago — BOP",
        "url": "https://www.central-bank.org.tt/statistics",
        "check_patterns": ["2024", "2025", "remittances", "transfers"],
        "data_fields": ["Inflows (US$ million)", "Outflows (US$ million)"],
        "source_org": "CBTT",
        "notes": "Official remittances data from balance of payments.",
    },
    {
        "id": "bank_guyana_bop",
        "theme": "Remittances",
        "countries": ["Guyana"],
        "label": "Bank of Guyana — BOP Statistics",
        "url": "https://www.bankofguyana.org.gy/bog/statistics",
        "check_patterns": ["2024", "2025", "remittances", "transfers"],
        "data_fields": ["Inflows (US$ million)", "Outflows (US$ million)"],
        "source_org": "Bank of Guyana",
        "notes": "Official remittances data.",
    },
    {
        "id": "cbtt_bahamas",
        "theme": "Remittances",
        "countries": ["The Bahamas"],
        "label": "Central Bank of the Bahamas — BOP",
        "url": "https://www.centralbankbahamas.com/statistics",
        "check_patterns": ["2024", "2025", "remittances", "transfers"],
        "data_fields": ["Inflows (US$ million)"],
        "source_org": "Central Bank of the Bahamas",
        "notes": "Official remittances data.",
    },
    {
        "id": "cima_cayman",
        "theme": "Remittances",
        "countries": ["Cayman Islands"],
        "label": "Cayman Islands Monetary Authority — BOP",
        "url": "https://www.cima.ky/statistics",
        "check_patterns": ["2024", "2025", "remittances", "transfers", "BOP"],
        "data_fields": ["Outflows (US$ million)"],
        "source_org": "CIMA",
        "notes": "Cayman Islands has the largest outflow in the dataset (~US$604M).",
    },

    # ── THEME 5: Regular Pathways ─────────────────────────────────────────────
    {
        "id": "cip_antigua",
        "theme": "Regular Pathways",
        "countries": ["Antigua and Barbuda"],
        "label": "Antigua CIP — Citizenship by Investment Statistics",
        "url": "https://cip.gov.ag/",
        "check_patterns": ["2024", "2025", "citizenship", "applications", "nationality"],
        "data_fields": ["Total Number of Work Permits", "Country of Origin",
                        "Number of Work Permits by Nationality"],
        "source_org": "CIP Antigua and Barbuda",
        "notes": "CIP publishes quarterly statistics on applications by country of origin.",
    },
    {
        "id": "idb_permits_2024",
        "theme": "Regular Pathways",
        "countries": ["ALL"],
        "label": "IDB — Migration Flows LAC: Statistics on Permits 2024",
        "url": "https://publications.iadb.org/en/migration-flows-latin-america-caribbean-statistics-permits-migrants",
        "check_patterns": ["2024", "2025", "permits", "Caribbean", "work"],
        "data_fields": ["Total Number of Work Permits", "Residence Permits",
                        "Temporary Residence Permit", "Permanent Residence Permits"],
        "source_org": "IDB",
        "notes": "IDB updates this series annually. Check for 2024 edition.",
    },
    {
        "id": "sib_belize_labour",
        "theme": "Regular Pathways",
        "countries": ["Belize"],
        "label": "SIB Belize — Labour Force Survey 2024",
        "url": "https://sib.org.bz/statistics/labour-force/",
        "check_patterns": ["2024", "2025", "labour", "work permit", "foreign"],
        "data_fields": ["Total Number of Work Permits", "Male", "Female"],
        "source_org": "Statistical Institute of Belize",
        "notes": "LFS captures work permit holders; annual survey.",
    },
    {
        "id": "grenada_cbi",
        "theme": "Regular Pathways",
        "countries": ["Grenada"],
        "label": "Grenada CBI — Citizenship by Investment Statistics",
        "url": "https://www.finance.gd/",
        "check_patterns": ["2024", "2025", "citizenship", "investment", "applications"],
        "data_fields": ["Total Number of Work Permits"],
        "source_org": "Grenada Ministry of Finance",
        "notes": "Grenada publishes quarterly CBI statistics.",
    },
    {
        "id": "ciu_skn",
        "theme": "Regular Pathways",
        "countries": ["Saint Kitts and Nevis"],
        "label": "SKN Citizenship by Investment Unit",
        "url": "https://ciu.gov.kn/",
        "check_patterns": ["2024", "2025", "citizenship", "investment", "applications"],
        "data_fields": ["Total Number of Work Permits"],
        "source_org": "SKN CIU",
        "notes": "Citizenship by Investment Unit publishes statistics.",
    },
    {
        "id": "cip_sl",
        "theme": "Regular Pathways",
        "countries": ["Saint Lucia"],
        "label": "Saint Lucia CIP Statistics",
        "url": "https://www.cipsaintlucia.com/",
        "check_patterns": ["2024", "2025", "citizenship", "investment", "applications"],
        "data_fields": ["Total Number of Work Permits"],
        "source_org": "Saint Lucia CIP",
        "notes": "Check for 2024 citizenship investment data.",
    },
    {
        "id": "eso_cayman_labour",
        "theme": "Regular Pathways",
        "countries": ["Cayman Islands"],
        "label": "ESO Cayman Islands — Labour Market Report",
        "url": "https://www.eso.ky/",
        "check_patterns": ["2024", "2025", "work permit", "labour", "employment"],
        "data_fields": ["Total Number of Work Permits", "Male", "Female"],
        "source_org": "ESO Cayman Islands",
        "notes": "ESO publishes labour market statistics including work permit holders.",
    },
    {
        "id": "dimas_curacao",
        "theme": "Regular Pathways",
        "countries": ["Curaçao"],
        "label": "DIMAS Curaçao — Residence Permits Statistics",
        "url": "https://www.gobiernu.cw/dimas",
        "check_patterns": ["2024", "2025", "residence", "permit", "verblijf"],
        "data_fields": ["Residence Permits", "Temporary Residence Permit",
                        "Permanent Residence Permits"],
        "source_org": "DIMAS Curaçao",
        "notes": "DIMAS is the immigration authority for Curaçao.",
    },
    {
        "id": "r4v_permits",
        "theme": "Regular Pathways",
        "countries": ["ALL"],
        "label": "R4V — Regularisation & Permits for Venezuelans",
        "url": "https://www.r4v.info/en/permits",
        "check_patterns": ["2024", "2025", "permits", "regularisation", "Venezuela"],
        "data_fields": ["Residence Permits", "Temporary Residence Permit"],
        "source_org": "R4V",
        "notes": "R4V tracks regularisation pathways for Venezuelan migrants across the region.",
    },
]

COUNTRIES = [
    "Anguilla", "Antigua and Barbuda", "Aruba", "Barbados", "Belize",
    "British Virgin Islands", "Cayman Islands", "Curaçao", "Dominica", "Grenada",
    "Guyana", "Jamaica", "Montserrat", "Saba", "Saint Kitts and Nevis",
    "Saint Lucia", "Saint Vincent and the Grenadines", "Sint Eustatius",
    "Sint Maarten", "Suriname", "The Bahamas", "Trinidad and Tobago",
    "Turks and Caicos Islands", "United States Virgin Islands",
]

THEMES = [
    "Migrant Stocks & Demographics",
    "Vulnerable Populations",
    "Intraregional Mobility",
    "Remittances",
    "Regular Pathways",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")


def content_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def scrape_source(source: dict, timeout: int = 15) -> dict:
    """Fetch a URL, check for update patterns, return result dict."""
    result = {
        "id": source["id"],
        "url": source["url"],
        "label": source["label"],
        "theme": source["theme"],
        "countries": source["countries"],
        "source_org": source["source_org"],
        "data_fields": source["data_fields"],
        "notes": source["notes"],
        "scraped_at": datetime.now().isoformat(),
        "status": "unknown",
        "http_code": None,
        "matched_patterns": [],
        "page_title": "",
        "snippet": "",
        "content_hash": "",
        "hash_changed": False,
        "new_year_detected": False,
        "detected_years": [],
        "error": None,
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(source["url"], headers=headers, timeout=timeout,
                            allow_redirects=True)
        result["http_code"] = resp.status_code

        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "lxml")

            # Title
            title_tag = soup.find("title")
            result["page_title"] = title_tag.get_text(strip=True) if title_tag else ""

            # Visible text for pattern matching
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            visible = soup.get_text(separator=" ", strip=True)
            visible_lower = visible.lower()

            # Content hash — detect if page changed since last run
            h = content_hash(visible[:50000])
            result["content_hash"] = h

            # Match check patterns
            for pat in source["check_patterns"]:
                if pat.lower() in visible_lower:
                    result["matched_patterns"].append(pat)

            # Detect year mentions (2024/2025)
            for year in ["2025", "2024", "2023"]:
                if year in visible:
                    result["detected_years"].append(year)

            result["new_year_detected"] = "2025" in result["detected_years"] or \
                                          "2024" in result["detected_years"]

            # Snippet — first 300 chars of meaningful text
            result["snippet"] = visible[:300].strip()

            n_matched = len(result["matched_patterns"])
            if n_matched >= 3:
                result["status"] = "updated"
            elif n_matched >= 1:
                result["status"] = "check"
            else:
                result["status"] = "no_match"

        elif resp.status_code in (403, 429):
            result["status"] = "blocked"
            result["error"] = f"HTTP {resp.status_code} — site blocked automated requests"
        else:
            result["status"] = "error"
            result["error"] = f"HTTP {resp.status_code}"

    except requests.exceptions.Timeout:
        result["status"] = "timeout"
        result["error"] = "Request timed out"
    except requests.exceptions.ConnectionError as e:
        result["status"] = "error"
        result["error"] = f"Connection error: {str(e)[:80]}"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)[:120]

    return result


def compare_with_previous(new_result: dict, cache: dict) -> dict:
    """Flag if content hash changed since last run."""
    prev = cache.get(new_result["id"])
    if prev and prev.get("content_hash") and new_result.get("content_hash"):
        new_result["hash_changed"] = (
            prev["content_hash"] != new_result["content_hash"]
            and new_result["content_hash"] != ""
        )
    return new_result


# ── Status display helpers ────────────────────────────────────────────────────
STATUS_CONFIG = {
    "updated":   {"icon": "✅", "label": "Data likely updated",    "color": "#3B6D11"},
    "check":     {"icon": "🔍", "label": "Partial match — check",  "color": "#BA7517"},
    "no_match":  {"icon": "⚠️",  "label": "No update detected",     "color": "#888780"},
    "blocked":   {"icon": "🚫", "label": "Site blocked scraper",   "color": "#A32D2D"},
    "timeout":   {"icon": "⏱️",  "label": "Timeout",               "color": "#BA7517"},
    "error":     {"icon": "❌", "label": "Error",                  "color": "#A32D2D"},
    "unknown":   {"icon": "❓", "label": "Not yet scraped",        "color": "#888780"},
}


def status_badge(status: str) -> str:
    cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["unknown"])
    return f"{cfg['icon']} {cfg['label']}"


# ── Sidebar ───────────────────────────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown("## 🌊 Caribbean Data Scraper")
        st.markdown("**IOM RCO Caribbean — 2025 Report Update**")
        st.divider()

        st.markdown("### Filters")
        sel_theme = st.selectbox("Theme", ["All themes"] + THEMES)
        sel_country = st.selectbox("Country / Territory", ["All countries"] + COUNTRIES)

        st.divider()
        st.markdown("### Run Scraper")
        timeout = st.slider("Request timeout (sec)", 5, 30, 15)
        delay = st.slider("Delay between requests (sec)", 0.5, 3.0, 1.0, step=0.5)

        run_all = st.button("▶ Scrape ALL sources", type="primary", use_container_width=True)
        run_filtered = st.button("▶ Scrape filtered only", use_container_width=True)

        st.divider()
        st.markdown("### Export")
        export_btn = st.button("📥 Export results to Excel", use_container_width=True)

        st.divider()
        cache = load_json(CACHE_FILE, {})
        if cache:
            last_times = [v.get("scraped_at", "") for v in cache.values() if v.get("scraped_at")]
            if last_times:
                last = max(last_times)[:16].replace("T", " ")
                st.caption(f"Last run: {last}")
        st.caption(f"{len(cache)} sources cached")

    return sel_theme, sel_country, timeout, delay, run_all, run_filtered, export_btn


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    sel_theme, sel_country, timeout, delay, run_all, run_filtered, export_btn = sidebar()

    st.title("🌊 Caribbean Regional Report — Data Source Monitor")
    st.markdown(
        "Monitors official and international data sources across **5 themes** and "
        "**24 territories** for the IOM RCO Caribbean annual report. "
        "Run the scraper to check which sources have new 2024/2025 data."
    )

    cache = load_json(CACHE_FILE, {})
    history = load_json(HISTORY_FILE, [])

    # ── Filter sources ─────────────────────────────────────────────────────────
    def source_matches(src):
        theme_ok = (sel_theme == "All themes") or (src["theme"] == sel_theme)
        country_ok = (
            sel_country == "All countries"
            or "ALL" in src["countries"]
            or sel_country in src["countries"]
        )
        return theme_ok and country_ok

    filtered_sources = [s for s in SOURCES if source_matches(s)]
    sources_to_run = SOURCES if run_all else filtered_sources

    # ── Summary metrics ────────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    cached_results = [cache.get(s["id"], {}) for s in SOURCES]
    statuses = [r.get("status", "unknown") for r in cached_results]

    col1.metric("Total sources", len(SOURCES))
    col2.metric("✅ Updated", statuses.count("updated"))
    col3.metric("🔍 Check", statuses.count("check"))
    col4.metric("⚠️ No match", statuses.count("no_match"))
    col5.metric("❌ Errors", statuses.count("error") + statuses.count("timeout") + statuses.count("blocked"))

    st.divider()

    # ── Run scraper ────────────────────────────────────────────────────────────
    if run_all or run_filtered:
        n = len(sources_to_run)
        st.info(f"Scraping {n} sources… this will take about {n * delay:.0f}–{n * (delay+5):.0f} seconds.")

        progress_bar = st.progress(0)
        status_text = st.empty()
        results_live = []

        for i, src in enumerate(sources_to_run):
            status_text.text(f"[{i+1}/{n}] {src['label'][:70]}…")
            result = scrape_source(src, timeout=timeout)
            result = compare_with_previous(result, cache)
            cache[src["id"]] = result
            results_live.append(result)
            progress_bar.progress((i + 1) / n)
            time.sleep(delay)

        save_json(CACHE_FILE, cache)

        # Append to history
        run_entry = {
            "run_at": datetime.now().isoformat(),
            "n_sources": n,
            "n_updated": sum(1 for r in results_live if r["status"] == "updated"),
            "n_check": sum(1 for r in results_live if r["status"] == "check"),
            "n_error": sum(1 for r in results_live if r["status"] in ("error", "timeout", "blocked")),
        }
        history.append(run_entry)
        save_json(HISTORY_FILE, history)

        status_text.success(f"Done! {run_entry['n_updated']} sources show updated data, "
                            f"{run_entry['n_check']} need manual check.")
        st.rerun()

    # ── Results table ──────────────────────────────────────────────────────────
    st.subheader(f"Source Status — {sel_theme} / {sel_country}")

    if not cache:
        st.warning("No scrape results yet. Click **▶ Scrape ALL sources** in the sidebar to begin.")
    else:
        tabs = st.tabs(THEMES)
        for tab, theme in zip(tabs, THEMES):
            with tab:
                theme_sources = [s for s in SOURCES if s["theme"] == theme and source_matches(s)]
                if not theme_sources:
                    st.caption("No sources match current country filter.")
                    continue

                for src in theme_sources:
                    res = cache.get(src["id"], {})
                    status = res.get("status", "unknown")
                    cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["unknown"])

                    changed_flag = "🔔 **Page content changed since last run!**" if res.get("hash_changed") else ""
                    years_found = ", ".join(res.get("detected_years", [])) or "—"
                    matched = ", ".join(res.get("matched_patterns", [])) or "none"

                    with st.expander(
                        f"{cfg['icon']} {src['label']}  —  "
                        f"{'  '.join(src['countries'][:3])}{'…' if len(src['countries'])>3 else ''}",
                        expanded=(status in ("updated", "check") or res.get("hash_changed"))
                    ):
                        c1, c2 = st.columns([2, 1])
                        with c1:
                            st.markdown(f"**Organisation:** {src['source_org']}")
                            st.markdown(f"**URL:** [{src['url']}]({src['url']})")
                            st.markdown(f"**Data fields:** {', '.join(src['data_fields'])}")
                            st.markdown(f"**Notes:** {src['notes']}")
                            if changed_flag:
                                st.warning(changed_flag)
                        with c2:
                            st.markdown(f"**Status:** {status_badge(status)}")
                            st.markdown(f"**Years detected:** {years_found}")
                            st.markdown(f"**Matched keywords:** {matched}")
                            if res.get("http_code"):
                                st.markdown(f"**HTTP:** {res['http_code']}")
                            if res.get("scraped_at"):
                                st.markdown(f"**Checked:** {res['scraped_at'][:16].replace('T',' ')}")
                            if res.get("error"):
                                st.error(res["error"])

                        if res.get("snippet"):
                            st.markdown("**Page snippet:**")
                            st.code(res["snippet"][:400], language=None)

    # ── Export ─────────────────────────────────────────────────────────────────
    if export_btn:
        rows = []
        for src in SOURCES:
            res = cache.get(src["id"], {})
            for country in (COUNTRIES if "ALL" in src["countries"] else src["countries"]):
                rows.append({
                    "Theme": src["theme"],
                    "Country": country,
                    "Source": src["label"],
                    "Organisation": src["source_org"],
                    "URL": src["url"],
                    "Data Fields": "; ".join(src["data_fields"]),
                    "Status": res.get("status", "not scraped"),
                    "Years Detected": ", ".join(res.get("detected_years", [])),
                    "Matched Keywords": ", ".join(res.get("matched_patterns", [])),
                    "Content Changed": res.get("hash_changed", False),
                    "HTTP Code": res.get("http_code", ""),
                    "Last Checked": res.get("scraped_at", "")[:16],
                    "Notes": src["notes"],
                    "Error": res.get("error", ""),
                })
        df = pd.DataFrame(rows)
        excel_path = DATA_DIR / f"caribbean_scraper_export_{date.today()}.xlsx"
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Source Status")
            for theme in THEMES:
                tdf = df[df["Theme"] == theme]
                if not tdf.empty:
                    tdf.to_excel(writer, index=False, sheet_name=theme[:31])
        st.success(f"Exported to `{excel_path}`")
        with open(excel_path, "rb") as f:
            st.download_button(
                "⬇ Download Excel",
                f.read(),
                file_name=excel_path.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # ── Run history ────────────────────────────────────────────────────────────
    if history:
        st.divider()
        st.subheader("Run History")
        hist_df = pd.DataFrame(history[-20:])
        hist_df["run_at"] = hist_df["run_at"].str[:16].str.replace("T", " ")
        st.dataframe(hist_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
