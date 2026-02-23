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
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return None

def is_valid_target(url: str) -> bool:
    host = normalize_domain(url)
    if not host:
        return False
    if host in IGNORED_HOSTS:
        return False
    if STARTER_HOST in host:
        return False
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

        # Alle Kandidaten sammeln – finale page.url entscheidet später
        candidate_urls: list[str] = []

        def on_request(req):
            url = req.url
            # Nur Haupt-Navigationsrequests (document), keine Assets
            if req.resource_type == "document" and is_valid_target(url):
                candidate_urls.append(url)
                print(f"📥 Navigation-Request: {url}")

        def on_response(resp):
            location = resp.headers.get("location", "")
            if location and is_valid_target(location):
                candidate_urls.append(location)
                print(f"📥 Location-Header: {location}")

        page.on("request", on_request)
        page.on("response", on_response)

        print(f"🌐 Lade Starter-URL: {STARTER_URL}")
        try:
            page.goto(STARTER_URL, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"⚠️ Warnung beim Laden: {e}")

        time.sleep(3)

        # ── Priorität 1: Finale Browser-URL ─────────────────────────
        final_url = page.url
        print(f"📍 Finale Browser-URL: {final_url}")

        if is_valid_target(final_url):
            domain = normalize_domain(final_url)
            print(f"✅ Finale URL verwendet: {final_url}")
            browser.close()
            return domain

        # ── Priorität 2: Button-Klick Fallback ──────────────────────
        try:
            print("⏳ Suche nach Button #goBtn ...")
            btn = page.wait_for_selector("#goBtn", timeout=5000)
            if btn:
                btn.click(force=True)
                print("🖱️ Button geklickt.")
                time.sleep(6)
                after_url = page.url
                print(f"📍 URL nach Klick: {after_url}")
                if is_valid_target(after_url):
                    domain = normalize_domain(after_url)
                    browser.close()
                    return domain
        except Exception:
            print("ℹ️ Kein Button gefunden.")

        # ── Priorität 3: Meta-Refresh im DOM ────────────────────────
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
                print(f"📥 Meta-Refresh: {meta_url}")
                domain = normalize_domain(meta_url)
                browser.close()
                return domain
        except Exception:
            pass

        # ── Priorität 4: Letzter gesammelter Kandidat ───────────────
        if candidate_urls:
            # Den LETZTEN nehmen – der ist am nächsten an der finalen Zielseite
            last = candidate_urls[-1]
            print(f"📥 Letzter Kandidat aus Interceptor: {last}")
            domain = normalize_domain(last)
            browser.close()
            return domain

        browser.close()
        raise Exception("Keine Ziel-Domain gefunden – Redirect blieb aus.")


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
