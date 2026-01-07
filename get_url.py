#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from playwright.sync_api import sync_playwright
from datetime import datetime
from urllib.parse import urlparse
import json
import time
import sys

# ==========================================================
# URL Normalisierung (ROBUST)
# ==========================================================

def normalize_domain(url):
    """
    https://megakino1.to/favicon.ico?t=123
    -> megakino1.to
    """
    if not url:
        return None

    try:
        parsed = urlparse(url)

        # Falls Playwright eine URL ohne Schema liefert
        if not parsed.netloc and parsed.path:
            return parsed.path.split("/")[0]

        return parsed.netloc
    except Exception:
        return None


# ==========================================================
# MegaKino URL Finder
# ==========================================================

def get_megakino_domain():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            )
        )

        page = context.new_page()
        found_url = None

        # ------------------ Network Intercept ------------------

        def on_request(req):
            nonlocal found_url
            url = req.url

            if (
                not found_url
                and "megakino.live" not in url
                and any(tld in url for tld in [".to", ".sx", ".ws", ".cc", ".tv"])
            ):
                found_url = url
                print("🎯 RAW URL:", url)

        page.on("request", on_request)

        # ------------------ Navigation ------------------

        print("🌐 Lade megakino.live …")
        page.goto("https://megakino.live", wait_until="networkidle")

        page.wait_for_selector("#goBtn", timeout=30000)
        time.sleep(2)

        page.click("#goBtn", force=True)

        # Warten auf Redirect
        for _ in range(40):
            if found_url:
                break
            time.sleep(0.5)

        browser.close()

        if not found_url:
            raise Exception("Keine Redirect-URL gefunden")

        domain = normalize_domain(found_url)

        if not domain:
            raise Exception("URL konnte nicht normalisiert werden")

        print("✅ DOMAIN:", domain)
        return domain


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("🎬 MegaKino Domain Finder")
        print("=" * 60)

        domain = get_megakino_domain()

        timestamp = datetime.utcnow().isoformat() + "Z"

        data = {
            "url": domain,
            "timestamp": timestamp,
            "success": True
        }

        print("\n💾 Schreibe Dateien …")

        # TXT
        with open("megakino-url.txt", "w", encoding="utf-8") as f:
            f.write(domain + "\n")

        # JSON
        with open("megakino-url.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # README
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(f"""# 🎬 MegaKino Domain

## ✅ Aktuelle Domain

**{domain}**

### Details
- 🌐 Domain: `{domain}`
- 🕐 Aktualisiert: `{timestamp}`

---

Automatisch ermittelt via GitHub Actions.
""")

        print("✓ megakino-url.txt")
        print("✓ megakino-url.json")
        print("✓ README.md")

        print("\n✅ SUCCESS")
        print("🎯 Final Domain:", domain)

        sys.exit(0)

    except Exception as e:
        print("\n❌ FEHLER:", e)

        error_data = {
            "url": None,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "success": False
        }

        with open("megakino-url.json", "w", encoding="utf-8") as f:
            json.dump(error_data, f, indent=2)

        with open("megakino-url.txt", "w", encoding="utf-8") as f:
            f.write("ERROR: " + str(e) + "\n")

        sys.exit(1)
