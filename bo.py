import time
import subprocess
from playwright.sync_api import sync_playwright

# === CONFIGURATION ===
URL = "https://az-plc-prod.awager.com/boClient/admin/casino/AWAGER/brands/DEV-AWAGER-SEK1"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA = r"C:\selenum\ChromeProfile"
OFFLINE_MACHINES = {100016, 100017, 100018, 100019, 100024, 100025}

def bootstrap_chrome():
    print("🚀 Launching Chrome with Debugging Port 9222...")
    cmd = f'"{CHROME_PATH}" --remote-debugging-port=9222 --user-data-dir="{USER_DATA}"'
    subprocess.Popen(cmd, shell=True)
    time.sleep(5)

def run_backoffice_task():
    bootstrap_chrome()
    
    with sync_playwright() as p:
        print("🔗 Connecting to Chrome...")
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
        except Exception as e:
            print(f"❌ Connection Failed: {e}")
            return

        print(f"🌐 Navigating to: {URL}")
        page.goto(URL)

        print("🚦 READY. Ensure you are logged in.")
        input("👉 Press [ENTER] once the 'Machines' list is visible to start...")

        for machine_id in range(100001, 100033):
            if machine_id in OFFLINE_MACHINES:
                print(f"⏭️ Skipping offline machine: {machine_id}")
                continue

            print(f"✨ Adding Machine ID: {machine_id}")

            try:
                # 1. Click the Plus (+) Icon - Forced to ignore interceptions
                plus_btn = page.locator("button[aria-label='Add Machine']").first
                plus_btn.scroll_into_view_if_needed()
                plus_btn.click(timeout=5000, force=True)
                time.sleep(1)
                
                # 2. Find and click the specific ID in the table
                id_cell = page.locator(f"tr.p-datatable-selectable-row td:text-is('{machine_id}')")
                id_cell.scroll_into_view_if_needed()
                id_cell.click(timeout=5000, force=True)
                
                # 3. Click the final 'Add Machine' button
                add_btn = page.locator("button.p-button").filter(has_text="Add Machine")
                add_btn.click(timeout=5000, force=True)

                print(f"✅ Machine {machine_id} added!")
                time.sleep(2) # Wait for popup to clear

            except Exception as e:
                print(f"⚠️ Failed on {machine_id}. Clearing... Error: {e}")
                page.keyboard.press("Escape")
                time.sleep(1)

        print("\n🏁 Mission Complete!")

if __name__ == "__main__":
    run_backoffice_task()



# ========================================================================
# 🛠️ QUICK-START CHEAT SHEET
# ========================================================================
# 1. Win+R: chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\selenum\ChromeProfile"
# 2. Terminal laptop: cd "C:\Users\PavelKivilša\OneDrive - Awager LTD\Documents\Awager\Python automation"
# 2. Terminal PC: cd "C:\Users\User\Desktop\Desktop\Awager\Python automation"
# 3. Terminal PC: python bo.py
# ========================================================================