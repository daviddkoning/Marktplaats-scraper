import sqlite3
import statistics
import re
import time 
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import scraper_service_3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
	"https://dealsfinder.nl",
	"https://www.dealsfinder.nl",
	"https://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEBUG = True

@app.on_event("startup")
def on_startup():
    scraper_service_3.setup_database()
    scraper_service_3.start_worker()


def get_db_connection():
    conn = sqlite3.connect("marktplaats_2.db", timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn

def schoon_prijs_op(prijs_text):
    if not prijs_text:
        return None

    prijs = prijs_text.lower().strip()

    non_numeric = ["bieden", "gratis", "gereserveerd", "zie omschrijving", "n.o.t.k."]
    if any(term in prijs for term in non_numeric):
        return None

    prijs = prijs.replace(',-', ',00')

    match = re.search(r'[\d.,]+', prijs)
    if not match:
        return None

    getal_str = match.group()

    if '.' in getal_str and ',' in getal_str:
        getal_str = getal_str.replace('.', '').replace(',', '.')
    elif ',' in getal_str:
        getal_str = getal_str.replace(',', '.')
    elif '.' in getal_str:
        parts = getal_str.split('.')
        if len(parts[-1]) == 3:
            getal_str = getal_str.replace('.', '')

    try:
        val = float(getal_str)
        return val if val > 0 else None
    except ValueError:
        return None


@app.get("/api/categorieen")
def categorieen():
    return {"categorieen": sorted(scraper_service_3.CATEGORIE_SLUGS.keys())}


@app.get("/api/stats")
def bereken_statistieken(
        term: str = Query(..., min_length=1),
        categorie: Optional[str] = Query(None),
        min_km: Optional[int] = Query(None),
        max_km: Optional[int] = Query(None),
        min_prijs: float = Query(0),
        start = time.perf_counter(),
):

    if categorie and categorie not in scraper_service_3.CATEGORIE_SLUGS:
        return {"error": f"Onbekende categorie: '{categorie}'."}

    scrape_info = scraper_service_3.ensure_fresh_data(
        term,
        categorie=categorie,
        max_pages=3,
        min_km=min_km,
        max_km=max_km,
        min_prijs=min_prijs
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT price FROM deals WHERE search_term = ?"
    params = [term.lower()]

    if categorie:
        query += " AND categorie = ?"
        params.append(categorie)

        if categorie == "Auto's":
            if min_km is not None:
                query += " AND kilometerstand >= ?"
                params.append(min_km)
            if max_km is not None:
                query += " AND kilometerstand <= ?"
                params.append(max_km)

    cursor.execute(query, params)
    rijen = cursor.fetchall()
    conn.close()

    prijzen_all = []

    for rij in rijen:
        prijs = schoon_prijs_op(rij["price"])
        if prijs is not None and prijs >= min_prijs:
            prijzen_all.append(prijs)

    if len(prijzen_all) == 0:
        if min_prijs > 0:
            return {"error": f"Geen advertenties gevonden met een minimale prijs van €{min_prijs}."}
        if categorie == "Auto's" and (min_km is not None or max_km is not None):
            return {"error": "Geen auto's gevonden voor deze zoekterm binnen de opgegeven kilometerstand."}
        return {"error": "Geen (geldige) prijzen gevonden voor deze zoekterm."}

    gemiddelde = round(statistics.mean(prijzen_all), 2)
    stdev = round(statistics.stdev(prijzen_all), 2) if len(prijzen_all) > 1 else 0.0
    gemiddelde_standaarddeviatie = (stdev / gemiddelde) * 100 if gemiddelde > 0 else 0

    def as_euro(bedrag):
        return f"€{bedrag:.2f}".replace('.', ',')

    prijs_range = f"{as_euro(max(0, gemiddelde - stdev))} - {as_euro(gemiddelde + stdev)}"

    # Histogram data berekenen met enkele grenswaarden
    histogram = []
    min_p = min(prijzen_all)
    max_p = max(prijzen_all)
    bin_count = min(10, len(set(prijzen_all)))

    if bin_count < 2 or min_p == max_p:
        histogram = [{"label": f"€{round(min_p)}", "aantal": len(prijzen_all)}]
    else:
        bin_width = (max_p - min_p) / bin_count
        balkjes = [0] * bin_count
        for p in prijzen_all:
            idx = int((p - min_p) / bin_width)
            if idx == bin_count:
                idx -= 1
            balkjes[idx] += 1

        for i in range(bin_count):
            lower = min_p + i * bin_width
            histogram.append({
                "label": f"€{round(lower)}",
                "aantal": balkjes[i]
            })

    return {
        "term": term,
        "categorie": categorie,
        "aantal": len(prijzen_all),
        "min_prijs": min_p,
        "max_prijs": max_p,
        "max_prijs_label": f"€{round(max_p)}",  # Extra label om de grafiek rechts af te sluiten
        "gemiddelde": gemiddelde,
        "mediaan": round(statistics.median(prijzen_all), 2),
        "standaarddeviatie": stdev,
        "prijs_range": prijs_range,
        "gemiddelde_standaard_deviatie": gemiddelde_standaarddeviatie,
        "histogram": histogram,
        "scrape_info": scrape_info,
        "server_s": (time.perf_counter() - start) 
    }
