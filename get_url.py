#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import json
from datetime import datetime
import time
import sys

def get_megakino_url():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # WICHTIG bei megakino
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

        def on_request(req):
            nonlocal found_url
            url = req.url
            if (
                "megakino.live" not in url
                and any(x in url for x in [".to", ".sx", ".ws", ".cc", ".tv"])
            ):
                if not found_url:
                    found_url = url
                    print("🎯 FOUND:", url)

        page.on("request", on_request)

        print("🌐 Lade megakino.live …")
        page.goto("https://megakino.live", wait_until="networkidle")

        page.wait_for_selector("#goBtn", timeout=30000)
        time.sleep(2)

        # echter Klick
        page.click("#goBtn", force=True)

        # warten auf Redirect-Request
        for _ in range(40):
            if found_url:
                break
            time.sleep(0.5)

        browser.close()

        if not found_url:
            raise Exception("Keine Redirect-URL gefunden")

        return {
            "url": found_url,
            "button_text": "goBtn",
            "status": "OK"
        }

# ===================== MAIN =====================

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("🎬 MegaKino URL Finder")
        print("=" * 60)

        result = get_megakino_url()

        data = {
            "url": result["url"],
            "button_text": result["button_text"],
            "status": result["status"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "success": True
        }

        print("\n💾 Schreibe Dateien …")

        # TXT
        with open("megakino-url.txt", "w", encoding="utf-8") as f:
            f.write(result["url"] + "\n")

        # JSON
        with open("megakino-url.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # README
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(f"""# 🎬 MegaKino URL Finder

## ✅ Aktuelle URL

**{result['url']}**

### Details
- 🔗 URL: `{result['url']}`
- 📊 Status: `{result['status']}`
- 🕐 Zeit: `{data['timestamp']}`

---

Automatisch generiert.
""")

        print("✓ megakino-url.txt")
        print("✓ megakino-url.json")
        print("✓ README.md")

        print("\n✅ SUCCESS")
        print("🎯 Final URL:", result["url"])
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
