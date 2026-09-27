#!/usr/bin/env python3
# Copyright (c) 2026  Joel Benway
# SPDX-License-Identifier: AGPL-3.0-or-later
# Please see end of file for extended copyright information

"""
CGSUSA Materials Manual PDF Downloader
======================================
Automates the downloading and organization of Catechesis of the Good Shepherd (CGSUSA)
materials manual PDFs into structured directories for catechists.

Directory structure produced:
  level <N>/
    <Section / Liturgical Theme>/
      <Material Presentation Name>/
        <files>.pdf
"""

__version__ = "1.0.0"

import os
import sys
import re
import time
import json
import getpass
import argparse
from urllib.parse import urljoin, urlparse, unquote
import requests
from bs4 import BeautifulSoup

from urllib3.util import Retry
from requests.adapters import HTTPAdapter

# When compiled with PyInstaller, sys.executable points to the .exe file
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_URL = "https://cgsusa.org"
LOGIN_URL = "https://cgsusa.org/connect/member-login/"
MEMBERS_URL = "https://cgsusa.org/members/"
SESSION_CACHE_FILE = os.path.join(APP_DIR, "cgsusa_session.json")

MANUAL_INFO = {
    "1": {
        "name": "Level 1",
        "index_url": "https://cgsusa.org/level-i-materials-manual/",
        "category_url": "https://cgsusa.org/category/level-i-materials-manual/",
        "category_id": 27,
        "folder_name": "level 1"
    },
    "2": {
        "name": "Level 2",
        "index_url": "https://cgsusa.org/level-ii-materials-manual/",
        "category_url": "https://cgsusa.org/category/level-ii-materials-manual/",
        "category_id": 28,
        "folder_name": "level 2"
    },
    "3": {
        "name": "Level 3",
        "index_url": "https://cgsusa.org/level-iii-materials-manual/",
        "category_url": "https://cgsusa.org/category/level-iii-materials-manual/",
        "category_id": 29,
        "folder_name": "level 3"
    }
}


def sanitize_filename(name: str) -> str:
    """Sanitize string for safe Windows folder and file names."""
    if not name:
        return "Untitled"
    # Decode common HTML entities
    name = re.sub(r'&#8211;', '-', name)
    name = re.sub(r'&#8217;', "'", name)
    name = re.sub(r'&#8216;', "'", name)
    name = re.sub(r'&#8220;', '"', name)
    name = re.sub(r'&#8221;', '"', name)
    name = re.sub(r'&#038;', '&', name)
    name = re.sub(r'&amp;', '&', name)
    name = re.sub(r'&quot;', '"', name)
    # Remove characters illegal in Windows filenames: \ / : * ? " < > |
    name = re.sub(r'[\\/:*?"<>|]', '-', name)
    # Collapse multiple spaces or dashes
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'-+', '-', name)
    return name.strip(' .-\t\r\n')


def get_session() -> requests.Session:
    """Create requests session with browser-like headers and retry logic."""
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    return session


def get_session_cache_path() -> str:
    """Find existing session cache or choose appropriate location."""
    local_path = os.path.abspath("cgsusa_session.json")
    if os.path.exists(local_path):
        return local_path
    app_path = os.path.join(APP_DIR, "cgsusa_session.json")
    if os.path.exists(app_path):
        return app_path
    return local_path


def save_session_cookies(session: requests.Session, filepath: str = None):
    """Save session cookies to a local JSON file."""
    if not filepath:
        filepath = get_session_cache_path()
    cookies_dict = session.cookies.get_dict()
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cookies_dict, f, indent=2)
        print(f"[*] Session saved locally to: {filepath}")
    except Exception as e:
        print(f"[!] Warning: Could not save session cookies: {e}")


def load_session_cookies(session: requests.Session, filepath: str = None) -> bool:
    """Load session cookies from local JSON file if present."""
    if not filepath:
        filepath = get_session_cache_path()
    if not os.path.exists(filepath):
        return False
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            cookies_dict = json.load(f)
        session.cookies.update(cookies_dict)
        print(f"[*] Loaded saved session from: {filepath}")
        return True
    except Exception as e:
        print(f"[!] Could not load session cache: {e}")
        return False


def verify_authenticated(session: requests.Session) -> bool:
    """Check if the session is currently authenticated on cgsusa.org."""
    try:
        resp = session.get(MEMBERS_URL, allow_redirects=True, timeout=15)
        # When logged in on CGSUSA, the login form with username-371087 is NOT present
        # and member content or logout links are visible.
        text = resp.text.lower()
        if "logout" in text or "wp-login.php?action=logout" in text:
            return True
        if "welcome members" in text and "username-371087" not in resp.text:
            return True
        return False
    except Exception as e:
        print(f"[!] Verification error: {e}")
        return False


def login_with_credentials(session: requests.Session, username: str, password: str) -> bool:
    """Perform Ultimate Member login on CGSUSA."""
    print(f"[*] Authenticating with cgsusa.org as {username}...")
    resp = session.get(LOGIN_URL, timeout=15)
    if resp.status_code != 200:
        print(f"[!] Failed to fetch login page: HTTP {resp.status_code}")
        return False

    soup = BeautifulSoup(resp.text, 'html.parser')
    form = soup.find('form')
    if not form:
        print("[!] Could not find login form on page.")
        return False

    action = form.get('action') or LOGIN_URL
    action_url = urljoin(BASE_URL, action)

    # Collect form defaults
    form_data = {}
    for inp in form.find_all('input'):
        name = inp.get('name')
        val = inp.get('value', '')
        if name:
            form_data[name] = val

    # Fill username and password into Ultimate Member fields
    user_field = 'username-371087'
    pass_field = 'user_password-371087'
    for k in form_data.keys():
        if k.startswith('username-'):
            user_field = k
        elif k.startswith('user_password-'):
            pass_field = k

    form_data[user_field] = username
    form_data[pass_field] = password

    post_resp = session.post(action_url, data=form_data, allow_redirects=True, timeout=20)
    post_soup = BeautifulSoup(post_resp.text, 'html.parser')
    err = post_soup.find(class_='um-field-error') or post_soup.find(class_='um-notice')
    if err:
        print(f"\n[!] Login failed: {err.get_text().strip()}\n")
        return False

    # Check if we are now logged in
    if verify_authenticated(session):
        print("[+] Login successful!")
        save_session_cookies(session)
        return True
    else:
        if "username-371087" in post_resp.text:
            print("\n[!] Login failed: Invalid email or password. Please try again.\n")
            return False
        print("[+] Login response received.")
        save_session_cookies(session)
        return True


def apply_cookie_string(session: requests.Session, cookie_str: str):
    """Set raw cookie string from browser into session."""
    parts = cookie_str.split(';')
    for part in parts:
        if '=' in part:
            k, v = part.strip().split('=', 1)
            session.cookies.set(k.strip(), v.strip(), domain='cgsusa.org')
    save_session_cookies(session)


def extract_materials_from_page(session: requests.Session, manual_info: dict) -> list:
    """
    Parse the Materials Manual index page to extract sections and material links.
    Returns list of dicts:
      [ { 'section': 'Incarnation Geography of Israel', 'title': '...', 'url': '...' }, ... ]
    """
    index_url = manual_info['index_url']
    print(f"[*] Scanning manual index: {index_url}...")
    materials = []
    seen_urls = set()

    try:
        resp = session.get(index_url, timeout=20)
    except Exception as e:
        print(f"[!] Error fetching {index_url}: {e}")
        resp = None

    if resp and resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Strategy 1: Divi Toggles / Accordions
        toggles = soup.find_all(class_='et_pb_toggle')
        if toggles:
            print(f"[*] Found {len(toggles)} toggle/accordion sections on index page.")
            for t in toggles:
                title_tag = t.find(class_='et_pb_toggle_title')
                section_name = title_tag.get_text().strip() if title_tag else "General"
                section_name = sanitize_filename(section_name)

                content_div = t.find(class_='et_pb_toggle_content') or t
                for a in content_div.find_all('a', href=True):
                    href = urljoin(BASE_URL, a['href'])
                    text = clean_material_title(a.get_text().strip())
                    if is_material_page_link(href, manual_info) and href not in seen_urls:
                        seen_urls.add(href)
                        materials.append({
                            'section': section_name,
                            'title': text or href.rstrip('/').split('/')[-1],
                            'url': href
                        })

        # Strategy 2: Headings followed by links in content area
        if not materials:
            main_content = soup.find(id='left-area') or soup.find(class_='entry-content') or soup.body
            current_section = "General"
            for elem in main_content.descendants:
                if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                    header_text = sanitize_filename(elem.get_text().strip())
                    if header_text and len(header_text) < 80 and not any(skip in header_text.lower() for skip in ['menu', 'sidebar', 'footer', 'navigation', 'search']):
                        current_section = header_text
                elif elem.name == 'a' and elem.has_attr('href'):
                    href = urljoin(BASE_URL, elem['href'])
                    text = clean_material_title(elem.get_text().strip())
                    if is_material_page_link(href, manual_info) and href not in seen_urls:
                        seen_urls.add(href)
                        materials.append({
                            'section': current_section,
                            'title': text or href.rstrip('/').split('/')[-1],
                            'url': href
                        })

    # Strategy 3: Always check Category Pagination Crawler to ensure no materials are missed
    print(f"[*] Checking category archives for any additional {manual_info['name']} materials...")
    category_materials = crawl_category_posts(session, manual_info)
    added_from_cat = 0
    for item in category_materials:
        if item['url'] not in seen_urls:
            seen_urls.add(item['url'])
            materials.append(item)
            added_from_cat += 1

    if added_from_cat > 0:
        print(f"[+] Added {added_from_cat} presentation(s) from category archives.")

    print(f"[+] Total presentations discovered for {manual_info['name']}: {len(materials)}")
    return materials


def is_material_page_link(href: str, manual_info: dict) -> bool:
    """Filter links to only presentation / material manual pages."""
    if not href.startswith('https://cgsusa.org/'):
        return False
    path = urlparse(href).path.lower().strip('/')
    if not path:
        return False
    
    # Exclude non-material pages
    excludes = [
        'wp-content', 'wp-admin', 'wp-login', 'cart', 'checkout', 'my-account',
        'category', 'tag', 'shop', 'donate', 'support', 'connect', 'contact',
        'discover', 'learn', 'feed', 'request-access', 'vendor', 'privacy-policy',
        'store-policies', 'leadership', 'guidestar', 'sitemap', 'member-login',
        'annual-meeting', 'faq', 'begin-cgs'
    ]
    if any(ex in path for ex in excludes):
        return False

    return True


def crawl_category_posts(session: requests.Session, manual_info: dict) -> list:
    """Crawl the WordPress category pages for the manual to find all material posts."""
    cat_url = manual_info['category_url']
    materials = []
    seen = set()
    page = 1
    while True:
        url = f"{cat_url}page/{page}/" if page > 1 else cat_url
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code == 404:
                break
            if resp.status_code != 200:
                break
        except Exception:
            break

        soup = BeautifulSoup(resp.text, 'html.parser')
        
        found_on_page = 0
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        for h in headings:
            a = h.find('a', href=True)
            if a:
                href = urljoin(BASE_URL, a['href'])
                raw_title = a.get_text().strip()
                if is_material_page_link(href, manual_info) and href not in seen:
                    seen.add(href)
                    found_on_page += 1
                    section = determine_section_from_title(raw_title)
                    clean_title = clean_material_title(raw_title)
                    materials.append({
                        'section': section,
                        'title': clean_title,
                        'url': href
                    })

        if found_on_page == 0:
            break

        page += 1
        time.sleep(0.3)

    return materials


def determine_section_from_title(title: str) -> str:
    """Heuristic to guess liturgical album/section from material title if unclassified."""
    title_lower = title.lower()
    if any(k in title_lower for k in ['geography', 'map', 'globe', 'israel', 'regions']):
        return "Incarnation Geography of Israel"
    if any(k in title_lower for k in ['prophecy', 'prophecies', 'isaiah', 'micah', 'nativity', 'annunciation', 'visitation', 'shepherds', 'magi', 'flight into egypt']):
        return "Incarnation Prophecies"
    if any(k in title_lower for k in ['baptism', 'font', 'white garment', 'candle', 'chrism', 'oil']):
        return "Baptism"
    if any(k in title_lower for k in ['altar', 'chalice', 'paten', 'eucharist', 'lavabo', 'cruet', 'vestment', 'chasuble', 'episcopal']):
        return "Eucharist"
    if any(k in title_lower for k in ['parable', 'mustard seed', 'pearl', 'leaven', 'treasure', 'good shepherd', 'found sheep']):
        return "Kingdom of God Parables"
    if any(k in title_lower for k in ['calendar', 'liturgical colors', 'advent', 'lent', 'easter', 'pentecost']):
        return "Liturgical Calendar"
    if any(k in title_lower for k in ['cenacle', 'last supper', 'city of jerusalem', 'empty tomb', 'crucifixion']):
        return "Paschal Mystery"
    if any(k in title_lower for k in ['bible', 'enthronement', 'prayer', 'psalm']):
        return "Prayer and Bible"
    return "General Materials"


def clean_material_title(title: str) -> str:
    """Remove prefixes like 'Level I - ' from material title."""
    title = sanitize_filename(title)
    cleaned = re.sub(r'^Level\s+[I|V|X|1|2|3]+\s*[-–—:]\s*', '', title, flags=re.IGNORECASE)
    return sanitize_filename(cleaned.strip())


def download_material_pdfs(session: requests.Session, material: dict, base_dir: str) -> int:
    """
    Fetch a material presentation page, find all PDFs, and download them
    into base_dir / <section> / <title> / <filename>.pdf
    Returns count of new PDFs downloaded.
    """
    target_dir = os.path.join(base_dir, material['section'], material['title'])
    os.makedirs(target_dir, exist_ok=True)

    try:
        resp = session.get(material['url'], timeout=20)
        if resp.status_code != 200:
            print(f"    [!] Failed to load page {material['url']} (HTTP {resp.status_code})")
            return 0
    except Exception as e:
        print(f"    [!] Error loading page {material['url']}: {e}")
        return 0

    soup = BeautifulSoup(resp.text, 'html.parser')
    pdf_links = []

    # Find explicit <a> links pointing to PDF files
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '.pdf' in href.lower() or ('uploads' in href and 'pdf' in href.lower()):
            full_url = urljoin(BASE_URL, href)
            link_name = a.get_text().strip()
            pdf_links.append((full_url, link_name))

    # Also search raw regex for any wp-content/uploads/.../*.pdf
    raw_matches = re.findall(r'https?://[^\s"\'<>]+\.pdf', resp.text, re.IGNORECASE)
    for m in raw_matches:
        if not any(m == p[0] for p in pdf_links):
            pdf_links.append((m, ''))

    if not pdf_links:
        print(f"    [-] No PDF attachments found on page.")
        return 0

    downloaded_count = 0
    for pdf_url, link_name in pdf_links:
        parsed = urlparse(pdf_url)
        raw_fname = unquote(os.path.basename(parsed.path))
        if not raw_fname or not raw_fname.lower().endswith('.pdf'):
            raw_fname = f"{sanitize_filename(link_name or material['title'])}.pdf"

        clean_fname = sanitize_filename(raw_fname)
        file_dest = os.path.join(target_dir, clean_fname)

        if os.path.exists(file_dest):
            local_size = os.path.getsize(file_dest)
            if local_size > 0:
                print(f"      [SKIP] Already downloaded ({local_size:,} bytes): {clean_fname}")
                continue

        success = False
        for attempt in range(1, 4):
            print(f"      [DOWNLOADING] {clean_fname}..." if attempt == 1 else f"      [RETRY {attempt}/3] {clean_fname}...")
            try:
                with session.get(pdf_url, stream=True, timeout=45) as r:
                    if r.status_code == 200:
                        with open(file_dest, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=32768):
                                if chunk:
                                    f.write(chunk)
                        dl_size = os.path.getsize(file_dest)
                        print(f"      [OK] Saved {clean_fname} ({dl_size:,} bytes)")
                        downloaded_count += 1
                        success = True
                        break
                    elif r.status_code == 404:
                        print(f"      [!] Not found (HTTP 404): {pdf_url}")
                        break
                    else:
                        print(f"      [!] Failed to download (HTTP {r.status_code}): {pdf_url}")
                        break
            except Exception as e:
                if attempt < 3:
                    print(f"      [!] Connection interrupted ({e}). Retrying in 2s...")
                    time.sleep(2)
                else:
                    print(f"      [!] Error downloading {clean_fname} after 3 attempts: {e}")
                if os.path.exists(file_dest):
                    try:
                        os.remove(file_dest)
                    except Exception:
                        pass

    return downloaded_count


def maybe_pause():
    """Keep console window open if running as an executable or in an interactive terminal."""
    if getattr(sys, 'frozen', False):
        try:
            input("\nPress Enter to exit...")
        except (EOFError, KeyboardInterrupt):
            pass


def main():
    parser = argparse.ArgumentParser(
        prog="cgsusa_manual_downloader",
        description="Download CGSUSA Materials Manual PDFs organized cleanly by directory for printing.",
        epilog="If no arguments are provided, all levels (Level 1, 2, and 3) are downloaded by default."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit."
    )
    parser.add_argument(
        "--level",
        choices=["1", "2", "3", "all"],
        default="all",
        help="Level to download: 1, 2, 3, or all (default: all)"
    )
    parser.add_argument("--email", help="CGSUSA member login email or username")
    parser.add_argument("--password", help="CGSUSA member login password")
    parser.add_argument("--cookie", help="Raw Cookie header string from browser session")
    parser.add_argument("--outdir", default=".", help="Base output directory (default: current directory)")
    parser.add_argument("--no-cache", action="store_true", help="Ignore saved session and force new login")
    parser.add_argument("--no-pause", action="store_true", help="Do not pause for keypress before exiting")

    args = parser.parse_args()

    print("=" * 65)
    print(f"   CGSUSA Materials Manual PDF Downloader v{__version__}")
    print("=" * 65)

    session = get_session()

    # Step 1: Check saved session
    authenticated = False
    if not args.no_cache and load_session_cookies(session):
        print("[*] Validating saved session...")
        if verify_authenticated(session):
            print("[+] Saved session is active and authenticated!")
            authenticated = True
        else:
            print("[-] Saved session has expired.")

    # Step 2: Cookie string override
    if not authenticated and args.cookie:
        print("[*] Applying provided cookie string...")
        apply_cookie_string(session, args.cookie)
        if verify_authenticated(session):
            print("[+] Successfully authenticated using cookie string!")
            authenticated = True
        else:
            print("[!] Provided cookie did not authenticate.")

    # Step 3: Interactive Login
    while not authenticated:
        username = args.email or os.environ.get("CGSUSA_EMAIL")
        password = args.password or os.environ.get("CGSUSA_PASSWORD")

        if not username:
            print("\nPlease enter your CGSUSA member login credentials:")
            username = input("  Email (or Username): ").strip()
        if not password:
            password = getpass.getpass("  Password: ").strip()

        if not username or not password:
            print("[!] Both email and password are required.")
            if not args.no_pause:
                maybe_pause()
            sys.exit(1)

        success = login_with_credentials(session, username, password)
        if success:
            authenticated = True
            break
        else:
            args.email = None
            args.password = None
            retry = input("Would you like to try again? (y/n): ").strip().lower()
            if retry != 'y':
                if not args.no_pause:
                    maybe_pause()
                sys.exit(1)

    # Step 4: Determine levels to process
    if args.level == "all":
        levels_to_process = ["1", "2", "3"]
    else:
        levels_to_process = [args.level]

    total_downloads = 0

    for lvl in levels_to_process:
        info = MANUAL_INFO[lvl]
        print(f"\n{'='*65}")
        print(f" Processing: {info['name']} Materials Manual")
        print(f"{'='*65}")

        lvl_dir = os.path.join(args.outdir, info['folder_name'])
        os.makedirs(lvl_dir, exist_ok=True)

        materials = extract_materials_from_page(session, info)
        if not materials:
            print(f"[!] No presentation pages found for {info['name']}.")
            continue

        print(f"\n[*] Processing downloads across {len(materials)} presentations...")
        for idx, mat in enumerate(materials, 1):
            print(f"\n[{idx}/{len(materials)}] {mat['section']} / {mat['title']}")
            count = download_material_pdfs(session, mat, lvl_dir)
            total_downloads += count
            time.sleep(0.4)

    print("\n" + "=" * 65)
    print(" ALL TASKS COMPLETE!")
    print(f" Total new PDFs downloaded: {total_downloads}")
    print(f" Files organized in: {os.path.abspath(args.outdir)}")
    print("=" * 65)

    if not args.no_pause:
        maybe_pause()


if __name__ == "__main__":
    main()

# This file is part of cgsusa-manual-downloader.
#
# cgsusa-manual-downloader is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# cgsusa-manual-downloader is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for
# more details.
#
# You should have received a copy of the GNU Affero General Public License along with
# cgsusa-manual-downloader. If not, see <https://www.gnu.org/licenses/>.

