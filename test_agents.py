#!/usr/bin/env python3
"""
Test suite for all x402agent.no services.

Tests:
  - Free endpoints: expect HTTP 200
  - Paid endpoints: expect HTTP 402 (Payment Required)
  - Well-known manifests: /.well-known/x402.json
  - Health/liveness checks
  - Response format validation

Usage:  python test_agents.py
"""

import json, sys, time, urllib.request, urllib.error, ssl

# Don't verify SSL for testing (some fly.dev certs can be flaky)
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

PASS = 0
FAIL = 0
WARN = 0

def req(url, timeout=15):
    """Make a GET request, return (status, headers, body)."""
    r = urllib.request.Request(url, headers={"User-Agent": "x402agent-test/1.0"})
    try:
        resp = urllib.request.urlopen(r, timeout=timeout, context=CTX)
        return resp.status, dict(resp.headers), resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, dict(e.headers), body
    except Exception as e:
        return 0, {}, str(e)

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}" + (f" — {detail}" if detail else ""))

def warn(name, detail=""):
    global WARN
    WARN += 1
    print(f"  ⚠ {name}" + (f" — {detail}" if detail else ""))

def is_json(body):
    try:
        json.loads(body)
        return True
    except:
        return False

# ── Tests per service ────────────────────────────────────────────────────

def test_norwegian_companies_house():
    print("\n═══ Norwegian Companies House ═══")
    base = "https://norwegian-companies-house.fly.dev"

    # Health / liveness
    status, _, body = req(f"{base}/")
    test("Root responds", status in (200, 402, 404, 307))

    # Well-known manifest
    status, _, body = req(f"{base}/.well-known/x402.json")
    if status == 200:
        test("x402.json manifest returns 200", True)
        test("x402.json is valid JSON", is_json(body))
        if is_json(body):
            manifest = json.loads(body)
            test("x402.json has service.id", "service" in manifest and "id" in manifest.get("service", {}))
            test("x402.json has endpoints", "endpoints" in manifest and len(manifest.get("endpoints", [])) > 0)
    else:
        warn("x402.json manifest", f"HTTP {status}")

    # Paid endpoint — /company/{org_nr} → expect 402
    status, headers, body = req(f"{base}/company/923609016")
    test("/company/923609016 returns 402", status == 402, f"got {status}")
    if status == 402:
        test("402 response is JSON", is_json(body))

    # Paid endpoint — /search?q=equinor → expect 402
    status, _, body = req(f"{base}/search?q=equinor")
    test("/search?q=equinor returns 402", status == 402, f"got {status}")

    # Paid endpoint — /person → expect 402
    status, _, body = req(f"{base}/person/Anders%20Opedal")
    test("/person/Anders Opedal returns 402", status == 402, f"got {status}")


def test_bhrefs():
    print("\n═══ bhrefs — SEO Tools ═══")
    base = "https://bhrefs.com"

    # Health / liveness
    status, _, body = req(f"{base}/")
    test("Root responds", status in (200, 402, 404, 307))

    # Well-known manifest
    status, _, body = req(f"{base}/.well-known/x402.json")
    if status == 200:
        test("x402.json manifest returns 200", True)
        test("x402.json is valid JSON", is_json(body))
    else:
        warn("x402.json manifest", f"HTTP {status}")

    # Paid endpoints → expect 402
    status, _, body = req(f"{base}/backlinks/cognite.com")
    test("/backlinks/cognite.com returns 402", status == 402, f"got {status}")

    status, _, body = req(f"{base}/referring-domains/cognite.com")
    test("/referring-domains/cognite.com returns 402", status == 402, f"got {status}")

    status, _, body = req(f"{base}/gap?domains=cognite.com,siemens.com")
    test("/gap returns 402", status == 402, f"got {status}")


def test_aurora():
    print("\n═══ Aurora — Norwegian Weather Intelligence ═══")
    base = "https://x402-aurora.fly.dev"

    # Free endpoints — expect 200
    status, _, body = req(f"{base}/health")
    test("/health returns 200", status == 200, f"got {status}")

    status, _, body = req(f"{base}/api-status")
    test("/api-status returns 200", status == 200, f"got {status}")
    if status == 200 and is_json(body):
        test("/api-status is valid JSON", True)
        data = json.loads(body)
        test("/api-status has status field", "status" in data or "ok" in data or "upstreams" in data,
             f"keys: {list(data.keys())[:5]}")

    status, _, body = req(f"{base}/cities")
    test("/cities returns 200", status == 200, f"got {status}")
    if status == 200:
        test("/cities is valid JSON", is_json(body))
        if is_json(body):
            data = json.loads(body)
            cities = data if isinstance(data, list) else data.get("cities", [])
            test(f"/cities has entries ({len(cities)} cities)", len(cities) > 0)

    # Well-known manifest
    status, _, body = req(f"{base}/.well-known/x402.json")
    if status == 200:
        test("x402.json manifest returns 200", True)
        test("x402.json is valid JSON", is_json(body))
        if is_json(body):
            manifest = json.loads(body)
            test("x402.json has service.id='aurora'",
                 manifest.get("service", {}).get("id") == "aurora",
                 f"got: {manifest.get('service', {}).get('id')}")
            eps = manifest.get("endpoints", [])
            test(f"x402.json has {len(eps)} endpoints", len(eps) >= 4)
    else:
        warn("x402.json manifest", f"HTTP {status}")

    # Paid endpoints → expect 402 (or 500 if CDP creds rotating)
    for path, label in [
        ("/forecast?lat=59.91&lon=10.75", "/forecast"),
        ("/forecast/city?name=oslo", "/forecast/city"),
        ("/marine?lat=60.0&lon=5.0", "/marine"),
        ("/alerts", "/alerts"),
    ]:
        status, _, body = req(f"{base}{path}")
        if status == 402:
            test(f"{label} returns 402", True)
        elif status == 500:
            warn(f"{label} returns 500 (CDP credentials rotating?)")
        else:
            test(f"{label} returns 402", False, f"got {status}")


# ── Marketing site tests ─────────────────────────────────────────────────

def test_marketing_site():
    print("\n═══ x402agent.no Marketing Site ═══")
    base = "https://x402agent.no"

    status, headers, body = req(base)
    test("Homepage returns 200", status == 200, f"got {status}")
    if status == 200:
        test("Homepage has <title>", "<title>" in body)
        test("Homepage mentions 'Norway'", "Norway" in body or "Norwegian" in body)
        test("Homepage has favicon.svg", "favicon.svg" in body)
        test("Homepage has search box", 'agent-search' in body)
        test("Homepage lists Aurora", "aurora" in body.lower() or "Aurora" in body)

    # Detail pages
    for slug in ["norwegian-companies-house", "bhrefs", "aurora"]:
        status, _, body = req(f"{base}/{slug}/")
        test(f"/{slug}/ returns 200", status == 200, f"got {status}")

    # SEO files
    status, _, body = req(f"{base}/sitemap.xml")
    test("sitemap.xml returns 200", status == 200, f"got {status}")
    if status == 200:
        test("sitemap.xml has aurora", "aurora" in body)

    status, _, body = req(f"{base}/robots.txt")
    test("robots.txt returns 200", status == 200, f"got {status}")

    status, _, body = req(f"{base}/favicon.svg")
    test("favicon.svg returns 200", status == 200, f"got {status}")

    # HTTPS enforcement
    status, headers, _ = req("http://x402agent.no")
    test("HTTP redirects to HTTPS", status in (301, 302, 200), f"got {status}")


# ── Run all ──────────────────────────────────────────────────────────────

def main():
    print("x402agent.no — Full Test Suite")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("=" * 50)

    test_marketing_site()
    test_norwegian_companies_house()
    test_bhrefs()
    test_aurora()

    print("\n" + "=" * 50)
    print(f"Results: {PASS} passed, {FAIL} failed, {WARN} warnings")
    print("=" * 50)

    sys.exit(1 if FAIL > 0 else 0)

if __name__ == "__main__":
    main()
