import sys
from playwright.sync_api import sync_playwright

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
URL = "http://127.0.0.1:18080/"

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(
        viewport={"width": 1100, "height": 780},
        record_video_dir=OUT_DIR,
        record_video_size={"width": 1100, "height": 780},
    )
    pg = ctx.new_page()
    pg.goto(URL, wait_until="networkidle")
    # 1) initial assessment renders
    pg.wait_for_function("document.getElementById('rectext').textContent.trim().length>0", timeout=20000)
    pg.wait_for_timeout(2200)
    # 2) scroll through evidence + timeline
    pg.mouse.wheel(0, 700); pg.wait_for_timeout(1600)
    pg.mouse.wheel(0, 700); pg.wait_for_timeout(1600)
    pg.mouse.wheel(0, -1400); pg.wait_for_timeout(800)
    # 3) override the intent and re-assess (shows interactivity)
    pg.fill("#intent", "run at 6 AM")
    pg.wait_for_timeout(600)
    pg.click("#run")
    pg.wait_for_function("document.getElementById('status').textContent.includes('assessed') || document.getElementById('status').textContent.includes('mode')", timeout=20000)
    pg.wait_for_timeout(2400)
    pg.mouse.wheel(0, 500); pg.wait_for_timeout(1600)
    ctx.close()   # finalizes the video file
    b.close()
    path = pg.video.path()
    print("VIDEO", path)
