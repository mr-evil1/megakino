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
STARTER_HOST = "megakino.live"
WORKFLOW_URL = "https://github.com/mr-evil1/megakino/actions/workflows/get-megakino-url.yml"

# Blacklist: Diese Hosts gelten NICHT als Ziel
IGNORED_HOSTS = {
    "megakino.live",
    "www.megakino.live",
    # CDN / Tracking / Cloudflare etc. können hier ergänzt werden
    "challenges.cloudflare.com",
}

# ==========================================================
# Hilfsfunktionen
# ==========================================================

def normalize_domain(url: str) -> str | None:
    if not url:
        return None
    try:
        parsed = urlparse(url if "://" in url else "https://" + url)
        return parsed.netloc.lower().lstrip("www.")
    except Exception:
        return None

def is_valid_target(url: str) -> bool:
    """Gibt True zurück, wenn die URL ein echter Redirect-Zielhost ist."""
    host = normalize_domain(url)
    if not host:
        return False
    if host in IGNORED_HOSTS:
        return False
    # Muss mindestens einen Punkt enthalten (echte Domain)
    if "." not in host:
        return False
    return True

# ==========================================================
# MegaKino Domain Finder
# ==========================================================

def get_megakino_domain() -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )

        page = context.new_page()
        found_url: str | None = None

        # ── Request-Interceptor ──────────────────────────────────────
        def on_request(req):
            nonlocal found_url
            if found_url:
                return
            url = req.url
            if is_valid_target(url) and STARTER_HOST not in url:
                found_url = url
                print(f"🎯 Redirect-Request erkannt: {url}")

        # ── Response-Interceptor (Location-Header) ───────────────────
        def on_response(resp):
            nonlocal found_url
            if found_url:
                return
            location = resp.headers.get("location", "")
            if location and is_valid_target(location) and STARTER_HOST not in location:
                found_url = location
                print(f"🎯 Location-Header erkannt: {location}")

        page.on("request", on_request)
        page.on("response", on_response)

        print(f"🌐 Lade Starter-URL: {STARTER_URL}")
        try:
            page.goto(STARTER_URL, wait_until="commit", timeout=30000)
        except Exception as e:
            print(f"⚠️ Warnung beim Laden: {e}")

        # Kurz warten – automatische Weiterleitungen brauchen manchmal etwas
        time.sleep(6)

        # ── Check 1: Finale Browser-URL ──────────────────────────────
        current_url = page.url
        print(f"📍 Aktuelle Browser-URL: {current_url}")
        if not found_url and is_valid_target(current_url) and STARTER_HOST not in current_url:
            found_url = current_url
            print(f"🎯 Weiterleitung über Browser-URL erkannt: {current_url}")

        # ── Check 2: Button-Fallback ─────────────────────────────────
        if not found_url:
            try:
                print("⏳ Suche nach Button #goBtn ...")
                btn = page.wait_for_selector("#goBtn", timeout=5000)
                if btn:
                    btn.click(force=True)
                    print("🖱️ Button geklickt.")
                    time.sleep(6)
                    after_click_url = page.url
                    if is_valid_target(after_click_url) and STARTER_HOST not in after_click_url:
                        found_url = after_click_url
                        print(f"🎯 Nach Button-Klick: {after_click_url}")
            except Exception:
                print("ℹ️ Kein Button gefunden.")

        # ── Check 3: Meta-Refresh / JS redirect im DOM ───────────────
        if not found_url:
            try:
                meta_url = page.evaluate("""() => {
                    const meta = document.querySelector('meta[http-equiv="refresh"]');
                    if (meta) {
                        const m = meta.content.match(/url=([^;]+)/i);
                        return m ? m[1].trim() : null;
                    }
                    return null;
                }""")
                if meta_url and is_valid_target(meta_url):
                    found_url = meta_url
                    print(f"🎯 Meta-Refresh-URL erkannt: {meta_url}")
            except Exception:
                pass

        browser.close()

        if not found_url:
            raise Exception("Keine Ziel-Domain gefunden – Redirect blieb aus.")

        domain = normalize_domain(found_url)
        if not domain:
            raise Exception(f"Domain konnte nicht aus URL extrahiert werden: {found_url}")

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
            "success": True,
        }

        print(f"\n✅ Erfolg! Ziel-Domain: {domain}")

        with open("megakino-url.txt", "w", encoding="utf-8") as f:
            f.write(domain + "\n")

        with open("megakino-url.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        with open("README.md", "w", encoding="utf-8") as f:
            f.write(
                f"# 🎬 MegaKino\n\n"
                f"## ▶️ Starter-Link\n**{STARTER_URL}**\n\n"
                f"## 🌐 Aktuelle Domain\n**[{domain}](https://{domain})**\n\n"
                f"### ℹ️ Details\n"
                f"- Aktualisiert: `{timestamp}`\n"
                f"- [Workflow]({WORKFLOW_URL})"
            )

        sys.exit(0)

    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        sys.exit(1)
