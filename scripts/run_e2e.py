#!/usr/bin/env python3
"""
Run G4 Production E2E tests with screenshot capture.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


EVIDENCE_DIR = Path(__file__).parent.parent / "evidence" / "milestones" / "G4"
SCREENSHOTS_DIR = EVIDENCE_DIR / "screenshots"
BROWSER_DIR = EVIDENCE_DIR / "browser"


def ensure_dirs():
    """Create evidence directories."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    BROWSER_DIR.mkdir(parents=True, exist_ok=True)


def run_playwright_tests():
    """Run Playwright tests and capture results."""
    print("=" * 60)
    print("Running Playwright E2E Tests")
    print("=" * 60)
    
    # Run pytest with Playwright
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/e2e/", "-v", 
         "--tb=short", "--playwright", "headless",
         f"--output={BROWSER_DIR}"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    
    # Save output
    output_file = BROWSER_DIR / "playwright-results.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Playwright E2E Results - {datetime.utcnow().isoformat()}\n")
        f.write("=" * 60 + "\n\n")
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\n\nSTDERR:\n")
        f.write(result.stderr)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


def capture_desktop_screenshot():
    """Capture desktop viewport screenshot using Playwright."""
    print("\n" + "=" * 60)
    print("Capturing Desktop Screenshot (1440x900)")
    print("=" * 60)
    
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        # Collect console and network data
        console_errors = []
        failed_requests = []
        
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("requestfailed", lambda req: failed_requests.append({"url": req.url, "failure": req.failure}))
        
        # Navigate
        page.goto("https://bee.andywongpt.com", wait_until="networkidle", timeout=30000)
        page.wait_for_selector(".state-banner", timeout=15000)
        
        # Capture main screenshot
        page.screenshot(path=str(SCREENSHOTS_DIR / "desktop-main.png"), full_page=False)
        print(f"✓ Captured desktop-main.png")
        
        # Open evidence drawer
        drawer_toggle = page.locator(".drawer-toggle")
        drawer_toggle.click()
        page.wait_for_selector(".drawer-content.open", timeout=5000)
        
        # Capture evidence drawer screenshot
        page.screenshot(path=str(SCREENSHOTS_DIR / "desktop-evidence.png"), full_page=False)
        print(f"✓ Captured desktop-evidence.png")
        
        browser.close()
        
        # Save console summary
        with open(BROWSER_DIR / "console-summary.txt", "w", encoding="utf-8") as f:
            f.write(f"Console Summary - Desktop\n")
            f.write("=" * 60 + "\n")
            if console_errors:
                f.write(f"\nErrors ({len(console_errors)}):\n")
                for err in console_errors[:20]:  # Limit to 20
                    f.write(f"  - {err}\n")
            else:
                f.write("\nNo console errors.\n")
        
        # Save network summary
        with open(BROWSER_DIR / "network-summary.json", "w", encoding="utf-8") as f:
            json.dump({
                "viewport": "1440x900",
                "failed_requests": failed_requests[:20],  # Limit to 20
                "total_errors": len(console_errors),
                "total_failed": len(failed_requests)
            }, f, indent=2)
        
        return len(console_errors) == 0 and len(failed_requests) == 0


def capture_mobile_screenshot():
    """Capture mobile viewport screenshot using Playwright."""
    print("\n" + "=" * 60)
    print("Capturing Mobile Screenshot (390x844)")
    print("=" * 60)
    
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use iPhone 14 Pro viewport
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        
        # Collect console and network data
        console_errors = []
        
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        # Navigate
        page.goto("https://bee.andywongpt.com", wait_until="networkidle", timeout=30000)
        page.wait_for_selector(".state-banner", timeout=15000)
        
        # Capture main screenshot
        page.screenshot(path=str(SCREENSHOTS_DIR / "mobile-main.png"), full_page=False)
        print(f"✓ Captured mobile-main.png")
        
        browser.close()
        
        return len(console_errors) == 0


def main():
    """Run all E2E validations."""
    ensure_dirs()
    
    # Check if Playwright is installed
    try:
        import playwright
    except ImportError:
        print("ERROR: Playwright not installed. Run: pip install playwright pytest-playwright")
        print("Then run: playwright install chromium")
        return 1
    
    # Run tests
    tests_passed = run_playwright_tests()
    
    # Capture screenshots
    desktop_ok = capture_desktop_screenshot()
    mobile_ok = capture_mobile_screenshot()
    
    # Summary
    print("\n" + "=" * 60)
    print("G4 E2E Validation Summary")
    print("=" * 60)
    print(f"Playwright Tests: {'PASS' if tests_passed else 'FAIL'}")
    print(f"Desktop Screenshot: {'PASS' if desktop_ok else 'FAIL'}")
    print(f"Mobile Screenshot: {'PASS' if mobile_ok else 'FAIL'}")
    print(f"\nEvidence saved to: {EVIDENCE_DIR}")
    
    return 0 if (tests_passed and desktop_ok and mobile_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
