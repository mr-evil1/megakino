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
            
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(45000)
            
            # Gehe zur Landing Page
            print("\n🌐 Loading megakino.live...")
            response = page.goto('https://megakino.live', wait_until='domcontentloaded')
            
            if not response or response.status != 200:
                raise Exception(f"Failed to load page: {response.status if response else 'No response'}")
            
            print("✓ Page loaded")
            
            # Warte auf Button-Aktivierung
            print("\n⏳ Waiting for JavaScript to activate button...")
            page.wait_for_function('''
                () => {
                    const btn = document.getElementById('goBtn');
                    return btn && !btn.disabled;
                }
            ''', timeout=35000)
            
            print("✓ Button is active")
            time.sleep(2)
            
            # Hole Button-Info
            button_info = page.evaluate('''
                () => {
                    const btn = document.getElementById('goBtn');
                    const status = document.getElementById('statusText');
                    return {
                        text: btn ? btn.innerText : null,
                        status: status ? status.innerText : null,
                        href: btn ? btn.href : null,
                        onclick: btn ? btn.getAttribute('onclick') : null,
                        target: btn ? btn.target : null
                    };
                }
            ''')
            
            print(f"\n📋 Button Info:")
            print(f"   Text: {button_info['text']}")
            print(f"   Status: {button_info['status']}")
            print(f"   Href: {button_info['href']}")
            print(f"   Target: {button_info['target']}")
            
            final_url = None
            
            # Strategie 1: Wenn href vorhanden und nicht Landing Page
            if button_info['href'] and button_info['href'] not in ['', 'https://megakino.live', 'https://megakino.live/']:
                final_url = button_info['href']
                print(f"\n✅ Strategy 1: Found URL in href: {final_url}")
            
            # Strategie 2: Button klicken und auf neuen Tab warten
            elif not final_url and button_info['target'] == '_blank':
                print(f"\n🔄 Strategy 2: Button opens new tab...")
                
                # Warte auf neuen Tab
                with context.expect_page() as new_page_info:
                    page.click('#goBtn')
                
                new_page = new_page_info.value
                new_page.wait_for_load_state('domcontentloaded', timeout=10000)
                time.sleep(2)
                
                final_url = new_page.url
                print(f"✅ New tab opened: {final_url}")
                new_page.close()
            
            # Strategie 3: Button klicken und URL-Änderung im gleichen Tab abwarten
            else:
                print(f"\n🔄 Strategy 3: Clicking button and waiting for URL change...")
                
                old_url = page.url
                page.click('#goBtn')
                
                # Warte bis URL sich ändert (max 10 Sekunden)
                for i in range(20):
                    time.sleep(0.5)
                    current_url = page.url
                    
                    if current_url != old_url and current_url not in ['https://megakino.live', 'https://megakino.live/']:
                        final_url = current_url
                        print(f"✅ URL changed to: {final_url}")
                        break
                    
                    if i % 4 == 0:
                        print(f"   [{i//2}s] Still waiting...")
                
                if not final_url:
                    # Letzte Chance: Hol URL direkt aus dem JavaScript
                    print(f"\n🔄 Strategy 4: Extracting URL from window.location...")
                    time.sleep(2)
                    final_url = page.evaluate('() => window.location.href')
            
            browser.close()
            
            # Validierung
            if not final_url or final_url in ['https://megakino.live', 'https://megakino.live/']:
                raise Exception("No valid redirect URL found - still on landing page")
            
            print(f"\n✅ Final URL: {final_url}")
            
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
        
        # JSON
        with open('megakino-url.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("✓ megakino-url.json")
        
        # TXT
        with open('megakino-url.txt', 'w', encoding='utf-8') as f:
            f.write(result['url'] + '\n')
        print("✓ megakino-url.txt")
        
        # README
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

- ⏰ **12:00 UTC** (13:00/14:00 DE)
- ⏰ **00:00 UTC** (01:00/02:00 DE)

## 🚀 Manuell aktualisieren

**[→ Workflow jetzt starten](../../actions/workflows/get-megakino-url.yml)**

## 📊 Rohdaten

- **[megakino-url.txt](megakino-url.txt)** - Nur URL
- **[megakino-url.json](megakino-url.json)** - Vollständige Daten

### API Zugriff

```bash
# Nur URL
curl https://raw.githubusercontent.com/YOUR_USERNAME/megakino/main/megakino-url.txt

# JSON mit Details
curl https://raw.githubusercontent.com/YOUR_USERNAME/megakino/main/megakino-url.json
```

---

*Letzte Aktualisierung: {data['timestamp']}*  
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
        
        error_data = {
            'url': None,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'success': False
        }
        
        try:
            with open('megakino-url.json', 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2)
            
            with open('megakino-url.txt', 'w', encoding='utf-8') as f:
                f.write(f"ERROR: {str(e)}\n")
            
            with open('README.md', 'w', encoding='utf-8') as f:
                f.write(f"""# 🎬 MegaKino URL Finder

## ⚠️ Letzter Lauf fehlgeschlagen

**Fehler:** `{str(e)}`  
**Zeitpunkt:** {error_data['timestamp']}

[**→ Erneut versuchen**](../../actions/workflows/get-megakino-url.yml)
""")
            
            print("\n💾 Error files created")
            
        except Exception as write_error:
            print(f"\n⚠️  Could not write files: {write_error}")
        
        sys.exit(1)
