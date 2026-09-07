import sys
from playwright.sync_api import sync_playwright

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
URL = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:18080/"
# mode: "hero" (default) just loads + scrolls the real assessment; "override" also
# types an intent override and re-assesses (used for the local/mock demo).
MODE = sys.argv[3] if len(sys.argv) > 3 else "hero"

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(
        viewport={"width": 1100, "height": 900},
        record_video_dir=OUT_DIR,
        record_video_size={"width": 1100, "height": 900},
    )
    pg = ctx.new_page()
    pg.goto(URL, wait_until="networkidle")
    # initial (real) assessment renders
    pg.wait_for_function("document.getElementById('rectext').textContent.trim().length>0", timeout=45000)
    pg.wait_for_timeout(2500)
    # scroll slowly through context -> conditions -> recommendation -> evidence -> timeline
    for dy in (500, 500, 500, 500):
        pg.mouse.wheel(0, dy); pg.wait_for_timeout(1500)
    pg.wait_for_timeout(1500)                 # linger on the labelled timeline
    pg.mouse.wheel(0, -2000); pg.wait_for_timeout(1000)
    if MODE == "override":
        pg.fill("#intent", "run at 6 AM"); pg.wait_for_timeout(600)
        pg.click("#run")
        pg.wait_for_function("document.getElementById('status').textContent.includes('mode')", timeout=45000)
        pg.wait_for_timeout(2400); pg.mouse.wheel(0, 600); pg.wait_for_timeout(1500)
    ctx.close()
    b.close()
    print("VIDEO", pg.video.path())
