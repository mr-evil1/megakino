#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import json
from datetime import datetime
import sys

def get_megakino_url():
    """Ruft megakino.live auf und holt die dynamisch generierte URL"""
    
    print("🔍 Opening megakino.live...")
    
    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            page = browser.new_page()
            page.set_default_timeout(40000)
            
            # Gehe zur Seite
            print("🌐 Loading page...")
            response = page.goto('https://megakino.live', wait_until='networkidle')
            
            if not response or response.status != 200:
                raise Exception(f"Page load failed: {response.status if response else 'No response'}")
            
            print("✓ Page loaded")
            print("⏳ Waiting for JavaScript to generate URL...")
            
            # Warte auf Button Aktivierung
            page.wait_for_function('''
                () => {
                    const btn = document.getElementById('goBtn');
                    return btn && !btn.disabled;
                }
            ''', timeout=35000)
            
            print("✓ Button is active")
            
            # Warte nochmal 3 Sekunden extra
            import time
            time.sleep(3)
            
            # Hole Button-Daten
            result = page.evaluate('''
                () => {
                    const btn = document.getElementById('goBtn');
                    const status = document.getElementById('statusText');
                    
                    return {
                        href: btn ? btn.href : null,
                        text: btn ? btn.innerText : null,
                        status: status ? status.innerText : null,
                        onclick: btn ? btn.getAttribute('onclick') : null
                    };
                }
            ''')
            
            print(f"📋 Button text: {result['text']}")
            print(f"📋 Status: {result['status']}")
            print(f"📋 Href: {result['href']}")
            print(f"📋 Onclick: {result['onclick']}")
            
            # Prüfe ob href vorhanden
            if result['href'] and result['href'] != '' and result['href'] != 'https://megakino.live':
                url = result['href']
                print(f"✅ Found URL in href: {url}")
            else:
                # Versuche Button zu klicken und URL zu holen
                print("🖱️ No href found, clicking button...")
                page.click('#goBtn')
                time.sleep(3)
                
                url = page.url
                if url == 'https://megakino.live':
                    raise Exception("Button click did not redirect to new URL")
                
                print(f"✅ Found URL after click: {url}")
            
            browser.close()
            
            return {
                'url': url,
                'text': result['text'],
                'status': result['status']
            }
            
        except Exception as e:
            if browser:
                browser.close()
            raise Exception(f"Failed to get URL: {e}")

# Main
if __name__ == '__main__':
    try:
        result = get_megakino_url()
        
        # Validiere dass URL existiert
        if not result['url']:
            raise Exception("No URL found in result")
        
        # Daten vorbereiten
        data = {
            'url': result['url'],
            'button_text': result['text'] or 'N/A',
            'status': result['status'] or 'N/A',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'success': True
        }
        
        print("\n💾 Saving files...")
        
        # JSON
        with open('megakino-url.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # TXT
        with open('megakino-url.txt', 'w', encoding='utf-8') as f:
            f.write(result['url'] + '\n')
        
        # README
        readme = f"""# 🎬 MegaKino URL Finder

## 📍 Aktuelle URL

### ✅ [{result['url']}]({result['url']})

- **Status:** {result['status'] or 'N/A'}
- **Button:** {result['text'] or 'N/A'}
- **Aktualisiert:** {data['timestamp']}

---

## 🕐 Automatische Updates

- ⏰ **12:00 UTC** (13:00/14:00 DE)
- ⏰ **00:00 UTC** (01:00/02:00 DE)

## 🚀 Manuell starten

[**→ Workflow jetzt ausführen**](../../actions/workflows/get-megakino-url.yml)

## 📊 Rohdaten

- [megakino-url.txt](megakino-url.txt) - Nur URL
- [megakino-url.json](megakino-url.json) - Vollständige Daten

### API Zugriff

```bash
curl https://raw.githubusercontent.com/YOUR_USERNAME/megakino/main/megakino-url.txt
```

---

*Automatisch aktualisiert durch GitHub Actions*
"""
        
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme)
        
        print("✅ All files saved successfully!")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        
        # Erstelle Fehler-Dateien
        error_data = {
            'url': None,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'success': False
        }
        
        with open('megakino-url.json', 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2)
        
        with open('megakino-url.txt', 'w', encoding='utf-8') as f:
            f.write(f"ERROR: {str(e)}\n")
        
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(f"""# 🎬 MegaKino URL Finder

## ⚠️ Letzter Lauf fehlgeschlagen

**Fehler:** {str(e)}

**Zeitpunkt:** {error_data['timestamp']}

[→ Erneut versuchen](../../actions/workflows/get-megakino-url.yml)
""")
        
        print("💾 Error files created")
        sys.exit(1)
