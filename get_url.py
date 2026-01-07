#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from playwright.sync_api import sync_playwright
from datetime import datetime
from urllib.parse import urlparse
import json
import time
import sys

# ==========================================================
# KONFIGURATION
# ==========================================================
STARTER_URL = "https://megakino.live"
WORKFLOW_URL = "https://github.com/mr-evil1/megakino/actions/workflows/get-megakino-url.yml"

# ==========================================================
# URL Normalisierung
# ==========================================================

def normalize_domain(url):
    """
    Extrahiert die reine Domain aus einer URL.
    Beispiel: https://megakino1.to/favicon.ico -> megakino1.to
    """
    if not url:
        return None

    try:
        parsed = urlparse(url)
        if parsed.netloc:
            return parsed.netloc
        # Fallback falls Schema fehlt
        return parsed.path.split("/")[0]
    except Exception:
        return None


# ==========================================================
# MegaKino Domain Finder
# ==========================================================

def get_megakino_domain():
    with sync_playwright() as p:
        # Browser-Instanz starten
        browser = p.chromium.launch(
            headless=True,  # Auf GitHub Actions muss dies True sein
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

        # Request-Interception um Redirects abzufangen
        def on_request(req):
            nonlocal found_url
            url = req.url
            # Prüfen auf typische Streaming-TLDs, die nicht der Starter sind
            if (
                not found_url
                and "megakino.live" not in url
                and any(tld in url for tld in [".to", ".sx", ".ws", ".cc", ".tv"])
            ):
                found_url = url
                print(f"🎯 RAW URL gefunden: {url}")

        page.on("request", on_request)

        print(f"🌐 Lade Starter-URL: {STARTER_URL}")
        try:
            page.goto(STARTER_URL, wait_until="networkidle", timeout=60000)

            # Warten auf den Button und klicken
            page.wait_for_selector("#goBtn", timeout=30000)
            time.sleep(2)
            page.click("#goBtn", force=True)

            # Kurze Wartezeit für den Redirect-Request
            for _ in range(40):
                if found_url:
                    break
                time.sleep(0.5)

        except Exception as e:
            browser.close()
            raise Exception(f"Fehler beim Seitenaufruf: {e}")

        browser.close()

        if not found_url:
            raise Exception("Keine Redirect-URL gefunden")

        domain = normalize_domain(found_url)
        if not domain:
            raise Exception("URL konnte nicht normalisiert werden")

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
            "starter_url": STARTER_URL,
            "url": domain,
            "timestamp": timestamp,
            "success": True
        }

        print("\n💾 Schreibe Dateien …")

        # 1. TXT Datei (reine Domain)
        with open("megakino-url.txt", "w", encoding="utf-8") as f:
            f.write(domain + "\n")

        # 2. JSON Datei (strukturierte Daten)
        with open("megakino-url.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # 3. README Datei (Dokumentation mit verstecktem Update-Link)
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(f"""# 🎬 MegaKino

## ▶️ Starter-Link
**{STARTER_URL}**

## 🌐 Aktuelle Domain
**[{domain}](https://{domain})**

### ℹ️ Details
- Starter: `{STARTER_URL}`
- Aktuelle Domain: `{domain}`
- Aktualisiert: `{timestamp}`
- [Jetzt aktualisieren]({WORKFLOW_URL})

---

🔁 Die Domain kann sich ändern.  
👉 **Immer über den Starter-Link einsteigen.**
""")

        print("✓ megakino-url.txt")
        print("✓ megakino-url.json")
        print("✓ README.md")

        print("\n✅ SUCCESS")
        print(f"🎯 Starter: {STARTER_URL}")
        print(f"🎯 Aktuelle Domain: {domain}")

        sys.exit(0)

    except Exception as e:
        print(f"\n❌ FEHLER: {e}")

        error_data = {
            "starter_url": STARTER_URL,
            "url": None,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "success": False
        }

        with open("megakino-url.json", "w", encoding="utf-8") as f:
            json.dump(error_data, f, indent=2)

        with open("megakino-url.txt", "w", encoding="utf-8") as f:
            f.write(f"ERROR: {e}\n")

        sys.exit(1)
