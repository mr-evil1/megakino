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

# Liste der TLDs, die als gültige Ziele gelten
VALID_TLDS = [".to", ".sx", ".ws", ".cc", ".tv", ".fit", ".net", ".me"]

# ==========================================================
# URL Normalisierung
# ==========================================================

def normalize_domain(url):
    if not url:
        return None
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc or parsed.path.split("/")[0]
        return netloc
    except Exception:
        return None

# ==========================================================
# MegaKino Domain Finder
# ==========================================================

def get_megakino_domain():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )

        page = context.new_page()
        found_url = None

        # Request-Interception: Falls im Hintergrund ein Redirect auf eine neue TLD passiert
        def on_request(req):
            nonlocal found_url
            url = req.url
            if not found_url and "megakino.live" not in url:
                if any(tld in url for tld in VALID_TLDS):
                    found_url = url
                    print(f"🎯 Redirect-Request erkannt: {url}")

        page.on("request", on_request)

        print(f"🌐 Lade Starter-URL: {STARTER_URL}")
        try:
            # Wir warten nur kurz auf networkidle, da Redirects oft sofort passieren
            page.goto(STARTER_URL, wait_until="commit", timeout=30000)
            
            # 1. Check: Hat sich die URL bereits von selbst geändert?
            time.sleep(5) # Kurze Pause für automatische Weiterleitung
            current_url = page.url
            if any(tld in current_url for tld in VALID_TLDS) and "megakino.live" not in current_url:
                found_url = current_url
                print(f"🎯 Automatische Weiterleitung erkannt: {current_url}")

            # 2. Check: Falls noch keine URL gefunden, versuchen wir den Button (Fallback)
            if not found_url:
                try:
                    print("⏳ Suche nach Button #goBtn...")
                    btn = page.wait_for_selector("#goBtn", timeout=5000)
                    if btn:
                        btn.click(force=True)
                        print("🖱️ Button geklickt.")
                        time.sleep(5)
                        found_url = page.url
                except:
                    print("ℹ️ Kein Button gefunden, fahre fort...")

        except Exception as e:
            print(f"⚠️ Warnung während des Ladens: {e}")

        # Letzter Abgleich der gefundenen URL
        final_url = found_url or page.url
        browser.close()

        domain = normalize_domain(final_url)
        
        # Validierung: Ist es wirklich eine neue Domain oder noch der Starter?
        if not domain or "megakino.live" in domain:
            raise Exception("Keine Ziel-Domain gefunden (Immer noch auf Starter-URL)")

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

        print(f"\n✅ Erfolg! Ziel-Domain: {domain}")
        
        # Speichern der Dateien...
        with open("megakino-url.txt", "w", encoding="utf-8") as f:
            f.write(domain + "\n")

        with open("megakino-url.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        with open("README.md", "w", encoding="utf-8") as f:
            f.write(f"# 🎬 MegaKino\n\n## ▶️ Starter-Link\n**{STARTER_URL}**\n\n## 🌐 Aktuelle Domain\n**[{domain}](https://{domain})**\n\n### ℹ️ Details\n- Aktualisiert: `{timestamp}`\n- [Workflow]({WORKFLOW_URL})")

        sys.exit(0)

    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        sys.exit(1)
