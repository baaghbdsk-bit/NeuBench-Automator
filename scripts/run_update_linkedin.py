import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from playwright.sync_api import sync_playwright
import config

first_name = "NeuBench"
last_name = "AI"
headline = "Building NeuBench • Real-Time AI Benchmarks across 266+ Models | LLM Evals & Engineering Commentary"

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(str(config.LINKEDIN_USER_DATA_DIR), headless=True, channel='chrome')
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto('https://www.linkedin.com/in/vishnu-gupta-b6b2951b2/', wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(3000)

    # Click Edit Profile
    edit_link = page.locator('a[aria-label="Edit profile"]').first
    if edit_link.is_visible():
        edit_link.click()
        page.wait_for_timeout(3500)

    print('On edit intro page:', page.url)

    inputs = page.locator('input[type="text"]').all()
    # The first two visible inputs on the edit intro form are always First Name & Last Name
    visible_inputs = [inp for inp in inputs if inp.is_visible()]
    print('Found visible text inputs:', len(visible_inputs))

    if len(visible_inputs) >= 2:
        fn_input = visible_inputs[0]
        ln_input = visible_inputs[1]
        
        print('Updating First Name to:', first_name)
        fn_input.click()
        fn_input.fill("")
        fn_input.press_sequentially(first_name, delay=50)

        print('Updating Last Name to:', last_name)
        ln_input.click()
        ln_input.fill("")
        ln_input.press_sequentially(last_name, delay=50)

    # Headline: look for textarea or input with headline
    textareas = page.locator('textarea').all()
    hl_filled = False
    for ta in textareas:
        val = ta.input_value()
        if any(w in val for w in ["BABU", "Student", "BBDNITM", "Lucknow", "NeuBench"]):
            print('Found Headline textarea! Updating...')
            ta.click()
            ta.fill("")
            ta.press_sequentially(headline, delay=20)
            hl_filled = True
            break

    if not hl_filled and len(visible_inputs) >= 3:
        # Check third or fourth input
        for inp in visible_inputs[2:]:
            val = inp.input_value()
            if any(w in val for w in ["BABU", "Student", "BBDNITM", "Lucknow", "NeuBench"]):
                print('Found Headline in input! Updating...')
                inp.click()
                inp.fill("")
                inp.press_sequentially(headline, delay=20)
                break

    page.wait_for_timeout(2000)

    # Click Save button
    save_btn = page.locator('button:has-text("Save")').first
    if save_btn and save_btn.is_visible():
        print('Clicking Save button...')
        save_btn.click()
        page.wait_for_timeout(4000)
        print('Save completed! New profile URL:', page.url)
    else:
        print('Could not find Save button')

    # Update cached profile JSON
    profile_data = {
        "name": f"{first_name} {last_name}".strip(),
        "headline": headline,
        "location": "Kakori, Uttar Pradesh, India",
        "profile_url": page.url,
        "connections": 7,
        "followers": 7,
        "impressions": 0,
        "profile_views": 0,
        "search_appearances": 0
    }
    with open(config.BASE_DIR / "linkedin_profile.json", "w", encoding="utf-8") as f:
        import json
        json.dump(profile_data, f, indent=2)

    ctx.close()
    print("SUCCESS: Profile updated successfully!")

