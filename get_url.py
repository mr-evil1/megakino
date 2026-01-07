#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import json
from datetime import datetime
import sys
import time

def get_megakino_url():
    """Ruft megakino.live auf und holt die dynamisch generierte URL"""
    
    print("🔍 Starting MegaKino URL Finder...")
    
    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            page = browser.new_page()
            page.set_default_timeout(45000)
            
            # Gehe zur Landing Page
            print("\n🌐 Loading megakino.live...")
            response = page.goto('https://megakino.live', wait_until='networkidle')
            
            if not response or response.status != 200:
                raise Exception(f"Failed to load page: {response.status if response else 'No response'}")
            
            print("✓ Page loaded successfully")
            
            # Warte auf Button-Aktivierung
            print("\n⏳ Waiting for JavaScript to activate button...")
            page.wait_for_function('''
                () => {
                    const btn = document.getElementById('goBtn');
                    return btn && !btn.disabled;
                }
            ''', timeout=35000)
            
            print("✓ Button is now active")
            
            # Extra Wartezeit
            time.sleep(2)
            
            # Hole aktuelle Button-Info
            button_info = page.evaluate('''
                () => {
                    const btn = document.getElementById('goBtn');
                    const status = document.getElementById('statusText');
                    return {
                        text: btn ? btn.innerText : null,
                        status: status ? status.innerText : null,
                        href: btn ? btn.href : null
                    };
                }
            ''')
            
            print(f"\n📋 Button Info:")
            print(f"   Text: {button_info['text']}")
            print(f"   Status: {button_info['status']}")
            print(f"   Href: {button_info['href']}")
            
            # Klicke den Button
            print("\n🖱️  Clicking button...")
            
            # Warte auf Navigation nach Button-Klick
            with page.expect_navigation(timeout=10000):
                page.click('#goBtn')
            
            # Warte kurz für finale URL
            time.sleep(2)
            
            final_url = page.url
            
            print(f"\n✅ Redirected to: {final_url}")
            
            # Validiere URL
            if final_url == 'https://megakino.live' or final_url == 'https://megakino.live/':
                raise Exception("Button did not redirect to a new URL")
            
            browser.close()
            
            return {
                'url': final_url,
                'text': button_info['text'],
                'status': button_info['status']
            }
            
        except Exception as e:
            if browser:
                browser.close()
            raise Exception(f"Error: {e}")

# Main execution
if __name__ == '__main__':
    try:
        print("=" * 60)
        print("🎬 MegaKino URL Finder")
        print("=" * 60)
        
        result = get_megakino_url()
        
        # Validierung
        if not result['url']:
            raise Exception("No URL in result")
        
        # Daten
        data = {
            'url': result['url'],
            'button_text': result['text'] or 'N/A',
            'status': result['status'] or 'N/A',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'success': True
        }
        
        print("\n" + "=" * 60)
        print("💾 Saving files...")
        print("=" * 60)
        
        # JSON speichern
        with open('megakino-url.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("✓ megakino-url.json")
        
        # TXT speichern
        with open('megakino-url.txt', 'w', encoding='utf-8') as f:
            f.write(result['url'] + '\n')
        print("✓ megakino-url.txt")
        
        # README erstellen
        readme = f"""# 🎬 MegaKino URL Finder

## 📍 Aktuelle URL

### ✅ **[{result['url']}]({result['url']})**

**Details:**
- 🔗 URL: `{result['url']}`
- 📊 Status: `{result['status'] or 'N/A'}`
- 🔘 Button: `{result['text'] or 'N/A'}`
- 🕐 Aktualisiert: `{data['timestamp']}`

---

## 🕐 Automatische Updates

Dieses Repository wird automatisch aktualisiert:
- ⏰ **12:00 UTC** (13:00/14:00 DE)
- ⏰ **00:00 UTC** (01:00/02:00 DE)

## 🚀 Manuell aktualisieren

**[→ Workflow jetzt starten](../../actions/workflows/get-megakino-url.yml)**

1. Klicke auf den Link
2. Klicke "Run workflow" (grüner Button)
3. Warte 1-2 Minuten
4. Aktualisiere diese Seite

## 📊 Rohdaten

- **[megakino-url.txt](megakino-url.txt)** - Nur die URL
- **[megakino-url.json](megakino-url.json)** - Vollständige Daten (JSON)

### 🔗 Raw URL (für Scripts)

```bash
# Hole aktuelle URL
curl https://raw.githubusercontent.com/YOUR_USERNAME/megakino/main/megakino-url.txt

# JSON mit allen Details
curl https://raw.githubusercontent.com/YOUR_USERNAME/megakino/main/megakino-url.json
```

---

## 📝 Wie es funktioniert

1. Script öffnet `megakino.live`
2. Wartet bis JavaScript den Button aktiviert
3. Klickt auf "View Full Site" Button
4. Folgt der Weiterleitung zur echten MegaKino URL
5. Speichert die finale URL

---

*Zuletzt erfolgreich aktualisiert: {data['timestamp']}*  
*Automatisch durch GitHub Actions*
"""
        
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme)
        print("✓ README.md")
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print(f"\n🎯 Final URL: {result['url']}\n")
        
        sys.exit(0)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ FAILED: {e}")
        print("=" * 60)
        
        # Error-Daten
        error_data = {
            'url': None,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'success': False
        }
        
        # Error-Dateien erstellen
        try:
            with open('megakino-url.json', 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2)
            
            with open('megakino-url.txt', 'w', encoding='utf-8') as f:
                f.write(f"ERROR: {str(e)}\n")
                f.write(f"Time: {error_data['timestamp']}\n")
            
            with open('README.md', 'w', encoding='utf-8') as f:
                f.write(f"""# 🎬 MegaKino URL Finder

## ⚠️ Letzter Lauf fehlgeschlagen

**Fehler:** `{str(e)}`

**Zeitpunkt:** {error_data['timestamp']}

---

## 🔄 Erneut versuchen

[**→ Workflow neu starten**](../../actions/workflows/get-megakino-url.yml)

---

*Weitere Details in den Actions Logs*
""")
            
            print("\n💾 Error files created")
            
        except Exception as write_error:
            print(f"\n⚠️  Could not write error files: {write_error}")
        
        sys.exit(1)
