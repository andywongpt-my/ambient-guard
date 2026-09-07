"""
G4 Production E2E Tests

Validates the live production application at https://bee.andywongpt.com
"""

import pytest
from playwright.sync_api import Page, expect


PRODUCTION_URL = "https://bee.andywongpt.com"


@pytest.fixture(scope="module")
def console_errors():
    """Collect console errors during test execution."""
    return []


@pytest.fixture(scope="module")
def failed_requests():
    """Collect failed network requests during test execution."""
    return []


def test_production_page_loads(page: Page, console_errors, failed_requests):
    """Test 1: Production page loads successfully."""
    # Setup listeners
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
    page.on("requestfailed", lambda req: failed_requests.append({"url": req.url, "failure": req.failure}))
    
    page.goto(PRODUCTION_URL, wait_until="networkidle", timeout=30000)
    
    # Verify page title
    expect(page).to_have_title("Ambient Guard")
    
    # Verify main container exists
    expect(page.locator(".container")).to_be_visible(timeout=10000)


def test_decision_banner_visible(page: Page):
    """Test 2: Ambient Guard decision banner is visible."""
    page.goto(PRODUCTION_URL, wait_until="networkidle", timeout=30000)
    
    # Wait for assessment to load
    page.wait_for_selector(".state-banner", timeout=15000)
    
    # Verify banner is visible
    banner = page.locator(".state-banner")
    expect(banner).to_be_visible()
    
    # Verify banner has content
    state_label = banner.locator(".state-label")
    expect(state_label).to_be_visible()
    expect(state_label).not_to_be_empty()


def test_my_plan_section_visible(page: Page):
    """Test 3: My Plan section is visible."""
    page.goto(PRODUCTION_URL, wait_until="networkidle", timeout=30000)
    
    # Wait for plan section
    page.wait_for_selector(".section-title", timeout=15000)
    
    # Find "My Plan" section
    plan_section = page.locator(".section").filter(has_text="My Plan")
    expect(plan_section).to_be_visible()
    
    # Verify plan card has content
    plan_card = plan_section.locator(".card")
    expect(plan_card).to_be_visible()


def test_bee_provenance_visible(page: Page):
    """Test 4: Bee provenance/source is visible."""
    page.goto(PRODUCTION_URL, wait_until="networkidle", timeout=30000)
    
    # Wait for Bee pill badge
    page.wait_for_selector(".pill.bee", timeout=15000)
    
    # Verify Bee source badge is visible
    bee_badge = page.locator(".pill.bee")
    expect(bee_badge).to_be_visible()
    expect(bee_badge).to_contain_text("Bee")


def test_environmental_metrics_render(page: Page):
    """Test 5: Environmental metrics render."""
    page.goto(PRODUCTION_URL, wait_until="networkidle", timeout=30000)
    
    # Wait for metrics grid
    page.wait_for_selector(".metrics-grid", timeout=15000)
    
    # Verify metrics exist
    metrics = page.locator(".metric-item")
    expect(metrics.first).to_be_visible()
    
    # Should have at least AQI metric
    aqi_metric = page.locator(".metric-item").filter(has_text="AQI")
    expect(aqi_metric).to_be_visible()


def test_forecast_labeling_visible(page: Page):
    """Test 6: Forecast labeling is visible."""
    page.goto(PRODUCTION_URL, wait_until="networkidle", timeout=30000)
    
    # Wait for forecast pill
    page.wait_for_selector(".pill.forecast", timeout=15000)
    
    # Verify forecast badge is visible
    forecast_badge = page.locator(".pill.forecast")
    expect(forecast_badge).to_be_visible()
    expect(forecast_badge).to_contain_text("forecast")


def test_timeline_renders(page: Page):
    """Test 7: Personal Environmental Timeline renders."""
    page.goto(PRODUCTION_URL, wait_until="networkidle", timeout=30000)
    
    # Wait for timeline
    page.wait_for_selector(".timeline", timeout=15000)
    
    # Verify timeline is visible
    timeline = page.locator(".timeline")
    expect(timeline).to_be_visible()
    
    # Should have at least one entry
    entries = timeline.locator(".timeline-entry")
    expect(entries.first).to_be_visible()


def test_evidence_drawer_opens(page: Page):
    """Test 8: Evidence drawer opens successfully."""
    page.goto(PRODUCTION_URL, wait_until="networkidle", timeout=30000)
    
    # Wait for drawer toggle
    page.wait_for_selector(".drawer-toggle", timeout=15000)
    
    # Click to open drawer
    drawer_toggle = page.locator(".drawer-toggle")
    drawer_toggle.click()
    
    # Verify drawer content is visible
    drawer_content = page.locator(".drawer-content")
    expect(drawer_content).to_be_visible()
    
    # Verify evidence table exists
    evidence_table = page.locator(".evidence-table")
    expect(evidence_table).to_be_visible()


def test_privacy_message_visible(page: Page):
    """Test 9: Privacy message is visible."""
    page.goto(PRODUCTION_URL, wait_until="networkidle", timeout=30000)
    
    # Wait for footer
    page.wait_for_selector("footer", timeout=15000)
    
    # Verify privacy message
    privacy = page.locator("footer .privacy")
    expect(privacy).to_be_visible()
    expect(privacy).to_contain_text("processes only the Bee context needed")


def test_assess_api_succeeds(page: Page):
    """Test 10: POST /api/v1/assess succeeds."""
    # Use page.request for API calls
    response = page.request.post(f"{PRODUCTION_URL}/api/v1/assess", 
                                   data={"content-type": "application/json"},
                                   timeout=30000)
    
    assert response.ok, f"API returned {response.status}"
    
    # Verify response has expected structure
    data = response.json()
    assert "bee_mode" in data
    assert "assessment" in data
    assert data["bee_mode"] == "mcp"


def test_no_critical_console_errors(page: Page, console_errors):
    """Verify no critical console errors during tests."""
    page.goto(PRODUCTION_URL, wait_until="networkidle", timeout=30000)
    page.wait_for_selector(".state-banner", timeout=15000)
    
    # Filter out non-critical errors
    critical_errors = [
        err for err in console_errors 
        if "network" not in err.text.lower() and "404" not in err.text.lower()
    ]
    
    assert len(critical_errors) == 0, f"Critical console errors: {[e.text for e in critical_errors]}"


def test_no_failed_requests(page: Page, failed_requests):
    """Verify no unexplained failed network requests."""
    page.goto(PRODUCTION_URL, wait_until="networkidle", timeout=30000)
    page.wait_for_selector(".state-banner", timeout=15000)
    
    # Filter out expected failures (e.g., favicon, analytics)
    unexpected_failures = [
        req for req in failed_requests
        if "favicon" not in req["url"].lower()
    ]
    
    assert len(unexpected_failures) == 0, f"Unexpected failed requests: {unexpected_failures}"
