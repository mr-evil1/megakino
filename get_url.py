#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import json
from datetime import datetime

def get_megakino_url():
    """Ruft megakino.live auf und holt die dynamisch generierte URL"""
    
    print("🔍 Opening megakino.live...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Öffne megakino.live
        page.goto('https://megakino.live', timeout=30000)
        print("✓ Page loaded")
        
        # Warte bis JavaScript den Button aktiviert (max 30 Sekunden)
        print("⏳ Waiting for JavaScript to generate URL...")
        page.wait_for_function(
            '() => !document.getElementById("goBtn").disabled',
            timeout=30000
        )
        
        # Hole die generierte URL
        result = page.evaluate('''() => {
            const btn = document.getElementById('goBtn');
            return {
                url: btn.href,
                text: btn.innerText,
                status: document.getElementById('statusText').innerText
            };
        }''')
        
        browser.close()
        
        print(f"✅ Found: {result['url']}")
        return result

# Hole URL
result = get_megakino_url()

# Speichere als JSON
data = {
    'url': result['url'],
    'button_text': result['text'],
    'status': result['status'],
    'timestamp': datetime.utcnow().isoformat() + 'Z'
}

with open('megakino-url.json', 'w') as f:
    json.dump(data, f, indent=2)

# Speichere nur URL als Text
with open('megakino-url.txt', 'w') as f:
    f.write(result['url'])

# Update README
readme = f"""# MegaKino URL

**Aktuelle URL:** [{result['url']}]({result['url']})

**Status:** {result['status']}  
**Letzte Aktualisierung:** {data['timestamp']}

---

Automatisch aktualisiert via GitHub Actions.
"""

with open('README.md', 'w') as f:
    f.write(readme)

print("💾 Saved results")