#!/usr/bin/env python3
"""Quick UI validation using Playwright."""

from playwright.sync_api import sync_playwright

def validate_production():
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Desktop validation
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        page.goto("https://bee.andywongpt.com", wait_until="networkidle", timeout=30000)
        page.wait_for_selector(".state-banner", timeout=15000)
        
        # Test 1: Decision banner
        banner = page.locator(".state-banner")
        if banner.is_visible():
            results.append("✓ Decision banner visible")
        else:
            results.append("✗ Decision banner NOT visible")
        
        # Test 2: My Plan section
        plan = page.locator(".section").filter(has_text="My Plan")
        if plan.is_visible():
            results.append("✓ My Plan section visible")
        else:
            results.append("✗ My Plan section NOT visible")
        
        # Test 3: Bee provenance
        bee_badge = page.locator(".pill.bee")
        if bee_badge.is_visible():
            results.append("✓ Bee provenance visible")
        else:
            results.append("✗ Bee provenance NOT visible")
        
        # Test 4: Environmental metrics
        metrics = page.locator(".metric-item")
        if metrics.first.is_visible():
            results.append("✓ Environmental metrics visible")
        else:
            results.append("✗ Environmental metrics NOT visible")
        
        # Test 5: Forecast label
        forecast = page.locator(".pill.forecast").first
        if forecast.is_visible():
            results.append("✓ Forecast labeling visible")
        else:
            results.append("✗ Forecast labeling NOT visible")
        
        # Test 6: Timeline
        timeline = page.locator(".timeline")
        if timeline.is_visible():
            results.append("✓ Timeline visible")
        else:
            results.append("✗ Timeline NOT visible")
        
        # Test 7: Evidence drawer
        drawer_toggle = page.locator(".drawer-toggle")
        drawer_toggle.click()
        page.wait_for_selector(".drawer-content.open", timeout=5000)
        drawer = page.locator(".drawer-content")
        if drawer.is_visible():
            results.append("✓ Evidence drawer opens")
        else:
            results.append("✗ Evidence drawer does NOT open")
        
        # Test 8: Privacy message
        privacy = page.locator("footer .privacy")
        if privacy.is_visible():
            results.append("✓ Privacy message visible")
        else:
            results.append("✗ Privacy message NOT visible")
        
        # Test 9: API health
        response = page.request.get("https://bee.andywongpt.com/health")
        if response.ok:
            data = response.json()
            if data.get("bee_mode") == "mcp":
                results.append("✓ API healthy (bee_mode=mcp)")
            else:
                results.append(f"✗ API unexpected bee_mode: {data.get('bee_mode')}")
        else:
            results.append(f"✗ API unhealthy: {response.status}")
        
        context.close()
        
        # Mobile validation
        mobile_context = browser.new_context(viewport={"width": 390, "height": 844})
        mobile_page = mobile_context.new_page()
        
        mobile_page.goto("https://bee.andywongpt.com", wait_until="networkidle", timeout=30000)
        mobile_page.wait_for_selector(".state-banner", timeout=15000)
        
        # Test 10: Mobile layout
        banner_mobile = mobile_page.locator(".state-banner")
        if banner_mobile.is_visible():
            results.append("✓ Mobile: Decision banner visible")
        else:
            results.append("✗ Mobile: Decision banner NOT visible")
        
        # Check for horizontal overflow (scroll)
        scroll_width = mobile_page.evaluate("document.documentElement.scrollWidth")
        client_width = mobile_page.evaluate("document.documentElement.clientWidth")
        if scroll_width <= client_width:
            results.append("✓ Mobile: No horizontal overflow")
        else:
            results.append(f"✗ Mobile: Horizontal overflow ({scroll_width}px > {client_width}px)")
        
        mobile_context.close()
        browser.close()
    
    return results

if __name__ == "__main__":
    print("G4 Production UI Validation")
    print("=" * 50)
    for result in validate_production():
        print(result)
    print("=" * 50)
    print("Validation complete.")
