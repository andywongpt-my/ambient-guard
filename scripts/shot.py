import sys
from playwright.sync_api import sync_playwright

OUT = sys.argv[1] if len(sys.argv) > 1 else "ui.png"
URL = "http://127.0.0.1:18080/"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1100, "height": 1400}, device_scale_factor=2)
    pg.goto(URL, wait_until="networkidle")
    # wait for the recommendation text to be populated by the assess() call
    pg.wait_for_function("document.getElementById('rectext').textContent.trim().length > 0", timeout=20000)
    # give the timeline fetch a moment to fill in
    pg.wait_for_timeout(2500)
    pg.screenshot(path=OUT, full_page=True)
    print("saved", OUT)
    b.close()
