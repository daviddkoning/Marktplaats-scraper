import time
import random
import threading
import queue
import sqlite3
import urllib.parse
import re
import asyncio
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Import async playwright instead of sync
from playwright.async_api import async_playwright

CATEGORIE_SLUGS = {
    "Antiek en Kunst": "antiek-en-kunst",
    "Audio, Tv en Foto": "audio-tv-en-foto",
    "Auto's": "auto-s",
    "Auto-onderdelen": "auto-onderdelen",
    "Boeken": "boeken",
    "Caravans en Kamperen": "caravans-en-kamperen",
    "Cd's en Dvd's": "cd-s-en-dvd-s",
    "Computers en Software": "computers-en-software",
    "Contacten en Berichten": "contacten-en-berichten",
    "Diensten en Vakmensen": "diensten-en-vakmensen",
    "Dieren en Toebehoren": "dieren-en-toebehoren",
    "Doe-het-zelf en Bouw": "doe-het-zelf-en-bouw",
    "Fietsen en Brommers": "fietsen-en-brommers",
    "Hobby en Vrije tijd": "hobby-en-vrije-tijd",
    "Huis en Inrichting": "huis-en-inrichting",
    "Huizen en Kamers": "huizen-en-kamers",
    "Kinderen en Baby's": "kinderen-en-baby-s",
    "Kleding | Dames": "kleding-dames",
    "Kleding | Heren": "kleding-heren",
    "Motoren": "motoren",
    "Muziek en Instrumenten": "muziek-en-instrumenten",
    "Postzegels en Munten": "postzegels-en-munten",
    "Sieraden, Tassen en Uiterlijk": "sieraden-tassen-en-uiterlijk",
    "Spelcomputers en Games": "spelcomputers-en-games",
    "Sport en Fitness": "sport-en-fitness",
    "Telecommunicatie": "telecommunicatie",
    "Tickets en Kaartjes": "tickets-en-kaartjes",
    "Tuin en Terras": "tuin-en-terras",
    "Vakantie": "vakantie",
    "Verzamelen": "verzamelen",
    "Watersport en Boten": "watersport-en-boten",
    "Witgoed en Apparatuur": "witgoed-en-apparatuur",
    "Zakelijke goederen": "zakelijke-goederen",
    "Diversen": "diversen",
}

DB_NAME = 'marktplaats_2.db'

# --- DATABASE FUNCTIONS ---

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deals (
            ad_id TEXT PRIMARY KEY,
            search_term TEXT,
            datum TEXT,
            title TEXT,
            price TEXT,
            link TEXT,
            categorie TEXT,
            kilometerstand INTEGER
        )
    ''')

    cursor.execute("PRAGMA table_info(deals)")
    kolommen = [row[1] for row in cursor.fetchall()]
    if "categorie" not in kolommen:
        cursor.execute("ALTER TABLE deals ADD COLUMN categorie TEXT")
        print("✅ Kolom 'categorie' toegevoegd aan bestaande 'deals' tabel.")

    if "kilometerstand" not in kolommen:
        cursor.execute("ALTER TABLE deals ADD COLUMN kilometerstand INTEGER")
        print("✅ Kolom 'kilometerstand' toegevoegd aan bestaande 'deals' tabel.")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scrape_log'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(scrape_log)")
        scrape_log_kolommen = [row[1] for row in cursor.fetchall()]
        if "min_prijs" not in scrape_log_kolommen:
            cursor.execute("DROP TABLE scrape_log")
            print("♻️  Oude 'scrape_log' tabel verwijderd om min_prijs filter toe te voegen.")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scrape_log (
            search_term TEXT,
            categorie TEXT,
            min_km INTEGER,
            max_km INTEGER,
            min_prijs REAL,
            last_scraped_at TEXT, 
            PRIMARY KEY (search_term, categorie, min_km, max_km, min_prijs)
        )
    ''')
    conn.commit()
    conn.close()
    print(f"✅ Database '{DB_NAME}' is ready and protected against duplicates!")

def save_to_db(ad_id, search_term, datum, title, price, link, categorie=None, kilometerstand=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
                   INSERT
                   OR IGNORE INTO deals
                       (ad_id, search_term, datum, title, price, link, categorie, kilometerstand)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ''', (ad_id, search_term, datum, title, price, link, categorie, kilometerstand))
    conn.commit()
    inserted = cursor.rowcount > 0
    conn.close()
    return inserted

def _mark_scraped(search_term, categorie=None, min_km=None, max_km=None, min_prijs=0):
    safe_min = min_km if min_km is not None else -1
    safe_max = max_km if max_km is not None else -1
    safe_prijs = min_prijs if min_prijs is not None else 0

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
                   INSERT INTO scrape_log (search_term, categorie, min_km, max_km, min_prijs, last_scraped_at)
                   VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(search_term, categorie, min_km, max_km, min_prijs) DO
                   UPDATE SET last_scraped_at = excluded.last_scraped_at
                   ''', (search_term, categorie, safe_min, safe_max, safe_prijs, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def _seconds_since_last_scrape(search_term, categorie=None, min_km=None, max_km=None, min_prijs=0):
    safe_min = min_km if min_km is not None else -1
    safe_max = max_km if max_km is not None else -1
    safe_prijs = min_prijs if min_prijs is not None else 0

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        'SELECT last_scraped_at FROM scrape_log WHERE search_term = ? AND categorie IS ? AND min_km = ? AND max_km = ? AND min_prijs = ?',
        (search_term, categorie, safe_min, safe_max, safe_prijs)
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    last = datetime.fromisoformat(row['last_scraped_at'])
    return (datetime.now() - last).total_seconds()


# --- PARSING & URL FUNCTIONS ---

MAANDEN_NL = {
    "jan": "01", "januari": "01", "feb": "02", "februari": "02", "mrt": "03", "maart": "03",
    "apr": "04", "april": "04", "mei": "05", "jun": "06", "juni": "06", "jul": "07", "juli": "07",
    "aug": "08", "augustus": "08", "sep": "09", "september": "09", "okt": "10", "oktober": "10",
    "nov": "11", "november": "11", "dec": "12", "december": "12",
}

DATUM_PATRONEN = re.compile(
    r'(vandaag|gisteren|\d{1,2}\s+(?:' + '|'.join(MAANDEN_NL.keys()) + r')(?:\s+\'?\d{2,4})?)',
    re.IGNORECASE
)

def find_datum_raw(ad):
    for el in ad.find_all(['span', 'p', 'div', 'time']):
        text = el.get_text(strip=True)
        if not text or len(text) > 30:
            continue
        if DATUM_PATRONEN.fullmatch(text.lower()):
            return text
    return None

def parse_datum_nl(raw_text):
    if not raw_text: return None
    text = raw_text.strip().lower()
    if "vandaag" in text: return datetime.now().strftime("%Y-%m-%d")
    if "gisteren" in text: return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    parts = text.replace("'", "").split()
    if len(parts) < 2: return None
    day = parts[0].zfill(2)
    month = MAANDEN_NL.get(parts[1])
    if not month: return None
    year = parts[2] if len(parts) >= 3 and parts[2].isdigit() else str(datetime.now().year)
    year = year if len(year) == 4 else f"20{year}"
    try:
        return datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None

def build_url(search_term, categorie=None, page=1, min_km=None, max_km=None, min_prijs=None, use_mileage_filter=False, postcode=None):
    encoded = urllib.parse.quote(search_term)
    
    # 1. URL Basis: with or without category slug
    if categorie:
        slug = CATEGORIE_SLUGS.get(categorie)
        if not slug:
            raise ValueError(f"Onbekende categorie: {categorie!r}")
        url = f"https://www.marktplaats.nl/l/{slug}/q/{encoded}/"
    else:
        url = f"https://www.marktplaats.nl/q/{encoded}/"
        
    # 2. Pagination
    if page > 1:
        url += f"p{page}/"
        
    # 3. Hash parameters
    hash_parts = []
    
    if postcode:
        hash_parts.append(f"postcode:{postcode}")
    
    # ONLY add PriceCentsFrom if min_prijs is strictly greater than 0
    if min_prijs is not None and min_prijs > 0:
        hash_parts.append(f"PriceCentsFrom:{int(min_prijs * 100)}")
        
    # ONLY add mileage filters for "Auto's" if the user has checked the mileage filter box
    if categorie == "Auto's" and use_mileage_filter:
        if min_km is not None and min_km > 0:
            hash_parts.append(f"mileageFrom:{min_km}")
        if max_km is not None:
            hash_parts.append(f"mileageTo:{max_km}")
        
    if hash_parts:
        url += "#" + "|".join(hash_parts)
            
    return url

# --- ASYNC PLAYWRIGHT SCRAPING FUNCTIONS ---

async def scrape_one_page(page, url, search_term, categorie=None):
    await page.goto(url, wait_until="domcontentloaded")

    try:
        await page.wait_for_selector("[class*='Listing']", timeout=5000)
    except Exception:
        pass

    html = await page.content()
    soup = BeautifulSoup(html, 'html.parser')

    main_container = soup.find('div', class_="hz-Page-element hz-Page-element--main")
    if not main_container:
        main_container = soup

    ads = main_container.find_all(['article', 'li'], class_=re.compile(r'Listing', re.I))

    saved_count = 0
    for ad in ads:
        try:
            title_element = ad.find(['span', 'h3'], class_=re.compile(r'title', re.I))
            title = title_element.text.strip().lower() if title_element else ""
            if not title or "gezocht" in title:
                continue

            price_element = ad.find(['div', 'span', 'p'], class_=re.compile(r'price', re.I))
            if not price_element:
                continue

            raw_price_text = price_element.text.strip().replace('\xa0', ' ')
            if any(term in raw_price_text.lower() for term in ["bieden", "gratis", "gereserveerd", "zie omschrijving", "n.o.t.k."]):
                continue

            price_match = re.search(r'€\s?[\d.,-]+', raw_price_text)
            if not price_match:
                continue
            price_text = price_match.group().strip()

            is_pro_class = ad.find(class_=re.compile(r'priority-product', re.I))
            is_pro_text = bool(re.search(r'top[\s-]*advertentie|dagtopper', ad.text, re.I)) if ad.text else False
            if is_pro_class or is_pro_text:
                continue

            link_element = ad.find('a', href=True)
            if not link_element:
                continue
            href = link_element['href']
            link = href if href.startswith('http') else "https://www.marktplaats.nl" + href
            ad_id = link.split('/')[-1].split('.')[0] if '/' in link else str(time.time())

            datum_raw = find_datum_raw(ad)
            datum = parse_datum_nl(datum_raw) or "Niet bekend"

            kilometerstand = None
            if categorie == "Auto's":
                km_element = ad.find(class_=re.compile(r'hz-attributes-nap-mileage', re.I))
                if km_element:
                    km_match = re.search(r'([\d.,]+)', km_element.text)
                    if km_match:
                        km_str = km_match.group(1).replace('.', '').replace(',', '')
                        try:
                            kilometerstand = int(km_str)
                        except ValueError:
                            pass
                if kilometerstand is None:
                    km_match_fallback = re.search(r'([\d.,]+)\s*km', ad.text, re.I)
                    if km_match_fallback:
                        km_str = km_match_fallback.group(1).replace('.', '').replace(',', '')
                        try:
                            kilometerstand = int(km_str)
                        except ValueError:
                            pass

            if save_to_db(ad_id, search_term, datum, title, price_text, link, categorie=categorie, kilometerstand=kilometerstand):
                saved_count += 1
        except Exception as e:
            continue

    return len(ads), saved_count


# --- WORKER & QUEUE LOGIC (Bridging Sync Queue to Async Playwright) ---

CACHE_TTL_SECONDS = 60 * 60

job_queue = queue.Queue()
job_status = {}
job_results = {}
_worker_started = False
_worker_started_lock = threading.Lock()
MAX_CONCURRENT_SCRAPERS = 4  # Deploys up to 4 scrapers simultaneously

def start_worker():
    """
    Spins up ONE background thread.
    That thread will manage the async Playwright browser and run jobs concurrently.
    """
    global _worker_started
    with _worker_started_lock:
        if _worker_started: return
        t = threading.Thread(target=_run_async_loop, daemon=True)
        t.start()
        _worker_started = True

def _run_async_loop():
    """Entry point for the background thread to start the asyncio event loop."""
    asyncio.run(_async_worker_manager())

async def _async_worker_manager():
    """
    Continuously pulls from the synchronous job_queue, deploying new headless
    scrapers concurrently up to MAX_CONCURRENT_SCRAPERS.
    """
    async with async_playwright() as p:
        # Launch Chromium once.
        browser = await p.chromium.launch(headless=True)
        # Use a Semaphore to limit parallel scraping contexts
        sem = asyncio.Semaphore(MAX_CONCURRENT_SCRAPERS)
        
        while True:
            try:
                # Non-blocking get from the standard Python queue
                job_data = job_queue.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.5)
                continue
            
            job_id, search_term, categorie, max_pages, min_km, max_km, min_prijs = job_data
            job_status[job_id] = "running"
            
            # Spawn a task for the job so the loop can immediately pull the next queue item
            asyncio.create_task(
                _process_job_async(sem, browser, job_id, search_term, categorie, max_pages, min_km, max_km, min_prijs)
            )

async def _process_job_async(sem, browser, job_id, search_term, categorie, max_pages, min_km, max_km, min_prijs):
    """Executes a single job within an isolated Playwright Context."""
    try:
        # Wait for a slot in the semaphore (limits concurrency)
        async with sem:
            total_saved = 0
            # Playwright Context: Acts like an isolated incognito window (very fast/lightweight)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                for page_num in range(1, max_pages + 1):
                    url = build_url(search_term, categorie=categorie, page=page_num, min_km=min_km, max_km=max_km, min_prijs=min_prijs)
                    ads_found, saved = await scrape_one_page(page, url, search_term, categorie=categorie)
                    total_saved += saved
                    
                    print(f"[{search_term} | {categorie} | Min Prijs: €{min_prijs}] page {page_num}: {ads_found} ads, {saved} new saved")

                    if ads_found == 0:
                        break

                    if page_num < max_pages:
                        await asyncio.sleep(random.uniform(1.0, 3.0))
            finally:
                await context.close()  # Always clean up memory

            _mark_scraped(search_term, categorie=categorie, min_km=min_km, max_km=max_km, min_prijs=min_prijs)
            job_results[job_id] = {"saved": total_saved, "search_term": search_term, "categorie": categorie}
            job_status[job_id] = "done"

    except Exception as e:
        print(f"⚠️ Worker task error: {e}")
        job_results[job_id] = {"error": str(e)}
        job_status[job_id] = "error"
    finally:
        job_queue.task_done()


def enqueue_search(search_term, categorie=None, max_pages=3, min_km=None, max_km=None, min_prijs=0):
    job_id = f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}-{search_term}"
    job_status[job_id] = "queued"
    job_queue.put((job_id, search_term, categorie, max_pages, min_km, max_km, min_prijs))
    return job_id

def wait_for_job(job_id, timeout=90, poll_interval=0.5):
    start = time.time()
    while time.time() - start < timeout:
        status = job_status.get(job_id)
        if status in ("done", "error"):
            return status, job_results.get(job_id)
        time.sleep(poll_interval)
    return "timeout", None

def ensure_fresh_data(search_term, categorie=None, max_pages=3, min_km=None, max_km=None, min_prijs=0, ttl_seconds=CACHE_TTL_SECONDS, timeout=90):
    search_term = search_term.strip().lower()
    categorie = categorie or None
    age = _seconds_since_last_scrape(search_term, categorie=categorie, min_km=min_km, max_km=max_km, min_prijs=min_prijs)

    if age is not None and age < ttl_seconds:
        return {"scraped": False, "reason": "cache_fresh", "age_seconds": round(age)}

    job_id = enqueue_search(search_term, categorie=categorie, max_pages=max_pages, min_km=min_km, max_km=max_km, min_prijs=min_prijs)
    status, result = wait_for_job(job_id, timeout=timeout)
    return {"scraped": True, "job_status": status, "result": result}
