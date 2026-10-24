import time
import os
import subprocess
import base64
import requests
import re
from playwright.sync_api import sync_playwright

# === CONFIGURATION ===
URL = "https://az-plc-prod-sek1.awager.com/appClient/login"
USER = "admin"
PASS = "password"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA = r"C:\selenum\ChromeProfile"
DEEPSEEK_API_KEY = "sk-7b9d1bb3da4816d5af3d4d27a9da72be"

def bootstrap_chrome():
    print("🚀 Ensuring Chrome is running...")
    cmd = f'"{CHROME_PATH}" --remote-debugging-port=9222 --user-data-dir="{USER_DATA}"'
    subprocess.Popen(cmd, shell=True)

def ask_ai_for_coordinates(base64_img):
    """Sends the screenshot to DeepSeek Vision API for coordinate analysis"""
    print("🧠 Siunčiame vaizdą į DeepSeek API...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    payload = {
        "model": "deepseek-chat", 
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": "This is a slot machine video stream. There is a row of bet buttons (e.g., 'Bet 50', 'Bet Level 1', '100', etc.). Locate the center of the lowest bet button. Return ONLY its estimated relative X and Y coordinates (from 0.0 to 1.0) separated by a comma. For example: 0.17, 0.80"
                    },
                    {
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
                    }
                ]
            }
        ],
        "max_tokens": 20
    }
    
    try:
        response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=10)
        data = response.json()
        reply = data['choices'][0]['message']['content'].strip()
        print(f"🤖 AI atsakė: {reply}")
        
        match = re.search(r"([0-9]*\.?[0-9]+)\s*,\s*([0-9]*\.?[0-9]+)", reply)
        if match:
            return float(match.group(1)), float(match.group(2))
    except Exception as e:
        print(f"⚠️ AI neatsakė laiku arba įvyko klaida: {e}")
        
    print("🛡 Naudojamas matematinis fallback mažiausiam statymui...")
    return 0.17, 0.80

def wait_for_machine_idle(page, timeout_sec=50):
    print(f"⏳ Laukiama, kol baigsis sukimas ar laimėjimo animacijos (iki {timeout_sec}s)...")
    
    # Give the UI a brief moment to transition into "Spinning/Disabled" state initially
    time.sleep(0.5)
    
    start_time = time.time()
    consecutive_idle_seconds = 0
    
    while time.time() - start_time < timeout_sec:
        settings_btn = page.locator("#bet-settings-btn").first
        try:
            if settings_btn.is_visible():
                is_enabled = settings_btn.is_enabled()
                class_attr = settings_btn.get_attribute("class") or ""
                
                # If button is active and doesn't have a disabled class
                if is_enabled and "disabled" not in class_attr.lower():
                    consecutive_idle_seconds += 1
                    # REQUIRE the button to be stable for 3 seconds to beat the win-animation micro-pause
                    if consecutive_idle_seconds >= 2: 
                        print("✅ Mašina laisva, UI mygtukai stabiliai aktyvūs!")
                        return True
                else:
                    # Button disabled (spinning or win animation playing), reset counter
                    consecutive_idle_seconds = 0 
        except:
            consecutive_idle_seconds = 0
            pass 
        time.sleep(1) 
        
    print("⚠ Dėmesio: Mašinos animacijos trunka per ilgai arba UI neatstrigo!")
    return False

def run_test_sequence(page):
    # --- 0. SMART LOAD DETECTOR ---
    print("⏳ Detecting game load status...")
    try:
        loader = page.locator(".loader-wrapper").first
        shield = page.locator(".cdk-overlay-backdrop").first
        
        # Give the loader a maximum of 3 seconds to pop up on screen
        try:
            loader.wait_for(state="visible", timeout=3000)
            print("🎯 Loading popup detected!")
        except:
            print("⚡ Loader didn't appear quickly, assuming lightning-fast load!")

        # Now strictly wait for them to be hidden so it blasts through the instant it's done
        loader.wait_for(state="hidden", timeout=45000)
        shield.wait_for(state="hidden", timeout=20000)
        
        print("✅ Loader AND Shield confirmed GONE!")
        time.sleep(0.5) # Tiny buffer before clicking volume
    except Exception as e:
        print(f"⚠️ Loader fallback triggered: {e}")

    # --- 0.5. VOLUME CHECK ---
    print("🔊 Checking volume status...")
    try:
        volume_btn = page.locator('[data-testid="sound-btn"]').first
        volume_btn.wait_for(state="visible", timeout=5000)
        
        if volume_btn.get_attribute("aria-checked") == "false":
            print("🔇 Volume is OFF. Turning it ON...")
            volume_btn.click(timeout=3000, force=True)
            time.sleep(1.5)
            print("🔊 Volume turned ON!")
        else:
            print("🔊 Volume is already ON. Moving to spins...")
    except Exception as e:
        print(f"⚠️ Volume button check skipped or failed: {e}")

    # --- 1. THE 2-SPIN SEQUENCE ---
    print("🎰 PERFORMING 2 SPINS...")
    for i in range(1, 3):
        try:
            spin_btn = page.locator('button:has(p:text("SPIN!")), button:has-text("SPIN")').first
            spin_btn.wait_for(state="visible", timeout=5000)
            spin_btn.click(timeout=3000, force=True) 
            print(f"🔥 SPIN {i} INITIATED!")
        except:
            print(f"⚠️ Spin {i} blocked, trying coordinate click...")
            page.mouse.click(815, 815) 
        
        # wait_for_machine_idle handles both standard spins and long win animations
        wait_for_machine_idle(page, timeout_sec=50)

    # --- 2. ADAPTIVE CAMERA CONTROL ---
    print("🔍 Adjusting Camera...")
    try:
        magnifier = page.locator('button').filter(has_text="Magnifier")
        magnifier.click(timeout=5000, force=True)
        
        zoom_in = page.locator('button').filter(has_text="Zoom-In")
        zoom_out = page.locator('button').filter(has_text="Zoom-Out")

        if zoom_in.is_visible():
            print("➕ Testing Zoom-In...")
            zoom_in.click(timeout=3000, force=True)
            time.sleep(2)
            zoom_out.click(timeout=3000, force=True)
        else:
            print("➖ Machine Pre-Zoomed. Testing Zoom-Out...")
            zoom_out.click(timeout=3000, force=True)
            time.sleep(2)
            zoom_in.click(timeout=3000, force=True)
        
        time.sleep(1)
        magnifier.click(timeout=3000, force=True)
        print("✅ Zoom Check Done!")
    except Exception as e:
        print(f"⚠️ Camera issue: {e}")
        try:
            page.locator('button').filter(has_text="Magnifier").click(timeout=2000, force=True)
        except: pass

    # --- 3. BET SETTINGS (SINGLE CLICK UI TEST) ---
    print("⚙️ Opening Bet Settings...")
    try:
        settings_btn = page.locator("#bet-settings-btn").first
        settings_btn.click(timeout=5000, force=True)
        time.sleep(2.5) 
        
        try:
            page.locator("app-swipe-controller, text='Bet Level 1'").first.wait_for(state="visible", timeout=4000)
        except:
            print("⚠️ Skydelis ilgai kraunasi, bandome tęsti...")

        time.sleep(0.5) 

        camera_view = None
        controllers = page.locator("app-swipe-controller")
        for i in range(controllers.count()):
            if controllers.nth(i).is_visible():
                camera_view = controllers.nth(i)
                break
                
        html_bet_btn = None
        try:
            html_bet_btn = page.get_by_text(re.compile(r"Bet Level 1", re.IGNORECASE)).first
        except: pass
        
        if html_bet_btn and html_bet_btn.is_visible():
            print("💻 Aptiktas HTML Bet skydelis! Ieškome koordinačių...")
            box = html_bet_btn.bounding_box()
            if box:
                target_x = box['x'] + (box['width'] / 2)
                target_y = box['y'] + (box['height'] / 2)
                print(f"🎯 Fiziškai spaudžiame HTML mygtuką! X: {target_x:.1f}, Y: {target_y:.1f}")
                page.mouse.click(target_x, target_y)
                time.sleep(1.5)
            
        elif camera_view:
            print("📸 Aptiktas kameros vaizdas. Daromas screenshot ir siunčiamas AI...")
            box = camera_view.bounding_box()
            if box:
                img_bytes = camera_view.screenshot(type="jpeg", quality=50) 
                base64_img = base64.b64encode(img_bytes).decode('utf-8')
                
                rel_x, rel_y = ask_ai_for_coordinates(base64_img)
                target_x = box['x'] + (box['width'] * rel_x)
                target_y = box['y'] + (box['height'] * rel_y)
                
                print(f"🎯 AI nusitaikė! X: {target_x:.1f}, Y: {target_y:.1f}")
                page.mouse.click(target_x, target_y)
                time.sleep(1.5)
        else:
            print("⚠️ Nerastas joks atpažįstamas Bet skydelis!")
                
        menu_still_open_final = False
        if camera_view and camera_view.is_visible(): menu_still_open_final = True
        if html_bet_btn and html_bet_btn.is_visible(): menu_still_open_final = True
        
        if menu_still_open_final:
            print("🔒 Meniu vis dar atviras po statymo pakeitimo. Uždarome rankiniu būdu...")
            settings_btn.click(timeout=3000, force=True)
            time.sleep(1)
                
    except Exception as e:
        print(f"⚠ Could not complete Bet click logic: {e}")

    wait_for_machine_idle(page, timeout_sec=40)

    # --- 4. CAMERA BUTTON CLICK ---
    print("🎥 Spaudžiamas 'Camera' mygtukas...")
    try:
        time.sleep(1)
        camera_btn = page.locator('button[aria-label="Camera"]').first
        camera_btn.wait_for(state="visible", timeout=5000)
        camera_btn.click(timeout=5000, force=True)
        print("✅ 'Camera' mygtukas sėkmingai paspaustas!")
        time.sleep(2) 
    except Exception as e:
        print(f"⚠ Nepavyko paspausti 'Camera' mygtuko: {e}")

    # --- 5. EXIT TO LOBBY ---
    print("🚪 Grįžtama į Lobby...")
    try:
        time.sleep(1.5)
        exit_btn = page.locator('.game-play-exit-icon-btn-rounded:visible, .exit-game-play-button:visible').first
        exit_btn.wait_for(state="visible", timeout=2000)
        exit_btn.click(timeout=3000, force=True)
        print("✅ Paspaustas 'Exit' mygtukas!")
        
        time.sleep(1.5) 
        confirm_btn = page.locator('button:visible', has_text="Yes, back to lobby").first
        confirm_btn.wait_for(state="visible", timeout=2000)
        confirm_btn.click(timeout=3000, force=True)
        print("✅ Patvirtintas grįžimas į Lobby!")
    except Exception as e:
        print(f"⚠ Nepavyko grįžti į Lobby: {e}")

def main():
    bootstrap_chrome()
    with sync_playwright() as p:
        print("\n🔗 Connecting...")
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
        except Exception as e:
            print(f"❌ Connection Failed: {e}")
            return
        
        page.goto(URL)
        
        # --- FULLY AUTOMATED LOGIN ---
        try:
            print("⏳ Laukiama prisijungimo lango (prisitaikoma prie tinklo greičio)...")
            page.locator('input[id="username"]').wait_for(state="visible", timeout=60000)
            print("🔐 Prisijungimo langas užkrautas! Vedami duomenys...")
            page.locator('input[id="username"]').fill(USER)
            page.locator('input[id="password"]').fill(PASS)
            page.get_by_role("button", name="Sign In").click()
            print("✅ Prisijungta sėkmingai! Laukiama Lobby...")
            time.sleep(5) 
        except Exception as e: 
            print("⚠️ Prisijungimo langas nerastas per 60s arba jau prisijungta. Tęsiame...")

        # --- FULLY AUTOMATED LOOP ---
        while True:
            try:
                print("\n🎯 Automatiškai ieškomas 'Play' mygtukas...")
                play_btn = page.get_by_role("button", name="Play").first
                play_btn.wait_for(state="visible", timeout=60000)
                play_btn.click(timeout=5000)
                
                run_test_sequence(page)
                
                print("\n🏁 Test Finished.")
                print("="*45)
                print("🔄 Automatiškai pereinama prie kitos mašinos...")
                print("="*45)
                
                time.sleep(2) 
                
            except Exception as e:
                print(f"⚠️ Loop Error: {e}")
                input("Hit ENTER to retry...")

if __name__ == "__main__":
    main()