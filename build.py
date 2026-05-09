#!/usr/bin/env python3
"""
Static site generator for x402agent.no

Usage:  python build.py

Reads services.json → generates:
  - index.html              (main landing page)
  - {slug}/index.html       (detail page per service)

To add a new service: edit services.json, then run this script.
"""

import json, html, os, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))

def load_services():
    with open(os.path.join(ROOT, "services.json")) as f:
        return json.load(f)

# ── Shared CSS ──────────────────────────────────────────────────────────

CSS = """\
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#0a0a0f;--surface:#12121a;--border:#1e1e2e;
  --text:#e2e2e8;--muted:#8888a0;--accent:#6366f1;
  --accent2:#818cf8;--green:#22c55e;--amber:#f59e0b;
}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}
a{color:var(--accent2);text-decoration:none}
a:hover{text-decoration:underline}
.container{max-width:960px;margin:0 auto;padding:0 24px}

/* Hero */
.hero{text-align:center;padding:80px 0 60px}
.hero h1{font-size:48px;font-weight:700;letter-spacing:-1px;margin-bottom:16px}
.hero h1 span{color:var(--accent)}
.hero p{font-size:20px;color:var(--muted);max-width:600px;margin:0 auto 32px}
.badge-row{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:40px}
.badge{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;border-radius:20px;font-size:13px;font-weight:500;background:var(--surface);border:1px solid var(--border);color:var(--muted)}
.badge .dot{width:8px;height:8px;border-radius:50%;background:var(--green)}

/* Product cards */
.products{padding:40px 0 60px}
.products h2{text-align:center;font-size:28px;margin-bottom:40px;color:var(--text)}
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:24px}
.product{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:32px;transition:border-color .2s}
.product:hover{border-color:var(--accent)}
.product-tag{display:inline-block;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;padding:4px 10px;border-radius:6px;margin-bottom:16px}
.product-tag.live{background:rgba(34,197,94,.15);color:var(--green)}
.product-tag.soon{background:rgba(245,158,11,.15);color:var(--amber)}
.product h3{font-size:22px;margin-bottom:8px}
.product h3 a{color:var(--text)}
.product h3 a:hover{color:var(--accent2)}
.product p{color:var(--muted);font-size:15px;margin-bottom:16px}
.product-meta{display:flex;gap:16px;flex-wrap:wrap}
.product-meta span{font-size:13px;color:var(--muted)}
.product-meta strong{color:var(--text)}

/* How it works */
.how{padding:40px 0 60px;border-top:1px solid var(--border)}
.how h2{text-align:center;font-size:28px;margin-bottom:40px}
.steps{display:grid;grid-template-columns:1fr 1fr 1fr;gap:24px}
.step{text-align:center;padding:24px}
.step-num{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;border-radius:50%;background:var(--accent);color:white;font-weight:700;font-size:18px;margin-bottom:16px}
.step h4{font-size:16px;margin-bottom:8px}
.step p{color:var(--muted);font-size:14px}

/* Protocol */
.protocol{padding:40px 0 60px;border-top:1px solid var(--border);text-align:center}
.protocol h2{font-size:28px;margin-bottom:16px}
.protocol>p{color:var(--muted);max-width:600px;margin:0 auto 24px;font-size:16px}
.code-block{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:20px 24px;text-align:left;font-family:'SF Mono',Monaco,monospace;font-size:13px;max-width:600px;margin:0 auto;overflow-x:auto;color:var(--muted);white-space:pre}
.code-block .comment{color:#555}
.code-block .url{color:var(--accent2)}
.code-block .status{color:var(--green)}

/* Detail page */
.back{display:inline-block;margin-top:32px;margin-bottom:-20px;font-size:14px;color:var(--muted)}
.back:hover{color:var(--accent2)}
.detail-hero{padding:60px 0 40px;border-bottom:1px solid var(--border)}
.detail-hero h1{font-size:36px;margin-bottom:8px}
.detail-hero .tagline{font-size:18px;color:var(--muted);margin-bottom:20px}
.detail-hero .meta-row{display:flex;gap:16px;flex-wrap:wrap;align-items:center}
.detail-hero .meta-row span{font-size:14px;color:var(--muted)}
.detail-hero .meta-row strong{color:var(--text)}
.section{padding:40px 0;border-bottom:1px solid var(--border)}
.section:last-of-type{border-bottom:none}
.section h2{font-size:24px;margin-bottom:24px}
.endpoint{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:24px;margin-bottom:16px}
.endpoint .ep-header{display:flex;align-items:center;gap:12px;margin-bottom:8px}
.endpoint .method{background:var(--accent);color:white;padding:3px 10px;border-radius:4px;font-size:12px;font-weight:700;font-family:monospace}
.endpoint .path{font-family:'SF Mono',Monaco,monospace;font-size:15px;color:var(--text)}
.endpoint .ep-desc{color:var(--muted);font-size:14px;margin-bottom:12px}
.endpoint .ep-price{font-size:13px;color:var(--muted);margin-bottom:12px}
.endpoint .ep-price strong{color:var(--green)}
.endpoint .ep-example{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:14px 16px;font-family:'SF Mono',Monaco,monospace;font-size:12px;color:var(--muted);overflow-x:auto;white-space:pre;margin-top:8px}
.details-text{color:var(--muted);font-size:15px;line-height:1.8;max-width:700px}
.details-text p{margin-bottom:16px}

/* Footer */
footer{border-top:1px solid var(--border);padding:40px 0;text-align:center;color:var(--muted);font-size:14px}
footer a{color:var(--muted)}
footer a:hover{color:var(--text)}

@media(max-width:700px){
  .hero h1{font-size:32px}
  .hero p{font-size:17px}
  .product-grid,.steps{grid-template-columns:1fr}
  .detail-hero h1{font-size:28px}
}
"""

FOOTER = """\
<footer>
  <div class="container">
    <p>&copy; 2026 x402agent.no &middot; <a href="https://x402.org">x402 Protocol</a> &middot; USDC on <a href="https://base.org">Base</a></p>
  </div>
</footer>
"""

# ── Index page ──────────────────────────────────────────────────────────

def render_product_card(svc):
    e = html.escape
    status = svc["status"]
    tag_cls = "live" if status == "live" else "soon"
    tag_label = "Live" if status == "live" else "Coming Soon"

    # Link: detail page for live services, or external url, or #
    href = f"/{svc['slug']}/"
    if status != "live":
        href = svc.get("url", "#")

    num_endpoints = len(svc.get("endpoints", []))

    return f"""\
      <div class="product">
        <span class="product-tag {tag_cls}">{tag_label}</span>
        <h3><a href="{e(href)}">{e(svc['name'])}</a></h3>
        <p>{e(svc['description'])}</p>
        <div class="product-meta">
          <span>From <strong>{e(svc['price'])}</strong>/query</span>
          <span><strong>{num_endpoints}</strong> endpoint{"s" if num_endpoints != 1 else ""}</span>
          <span>{e(svc.get('currency', 'USDC on Base'))}</span>
        </div>
      </div>"""


def build_index(services):
    cards = "\n".join(render_product_card(s) for s in services)

    # Use first live service for the protocol example
    live = [s for s in services if s["status"] == "live" and s.get("endpoints")]
    if live and live[0]["endpoints"]:
        ep = live[0]["endpoints"][0]
        example_req = html.escape(ep["example_request"])
        example_resp = html.escape(ep["example_response"])
    else:
        example_req = "curl https://api.example.com/data"
        example_resp = '{"result": "..."}'

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>x402agent — AI Agent Services Powered by x402</title>
<meta name="description" content="Pay-per-query APIs built for AI agents. Company intelligence, SEO tools, and more — all powered by the x402 micropayment protocol. No API keys, no subscriptions.">
<link rel="canonical" href="https://x402agent.no/">
<meta property="og:title" content="x402agent — AI Agent Services">
<meta property="og:description" content="Pay-per-query APIs built for AI agents. Powered by x402 micropayments on Base.">
<meta property="og:url" content="https://x402agent.no/">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<style>
{CSS}
</style>
</head>
<body>

<div class="container">

  <section class="hero">
    <h1><span>x402</span>agent</h1>
    <p>Pay-per-query APIs built for AI agents. No API keys, no subscriptions — just micropayments on Base.</p>
    <div class="badge-row">
      <span class="badge"><span class="dot"></span> x402 Protocol</span>
      <span class="badge">USDC on Base</span>
      <span class="badge">No Accounts Needed</span>
      <span class="badge">From $0.01/query</span>
    </div>
  </section>

  <section class="products">
    <h2>Services</h2>
    <div class="product-grid">
{cards}
    </div>
  </section>

  <section class="how">
    <h2>How It Works</h2>
    <div class="steps">
      <div class="step">
        <div class="step-num">1</div>
        <h4>Request</h4>
        <p>Your AI agent sends a GET request to any paid endpoint</p>
      </div>
      <div class="step">
        <div class="step-num">2</div>
        <h4>Pay</h4>
        <p>The server returns HTTP 402. Your agent signs a USDC micropayment on Base</p>
      </div>
      <div class="step">
        <div class="step-num">3</div>
        <h4>Receive</h4>
        <p>Resend with payment header — get structured data instantly</p>
      </div>
    </div>
  </section>

  <section class="protocol">
    <h2>x402 Protocol</h2>
    <p>The open standard for HTTP micropayments. Your agent pays per query with USDC — no API keys, no rate limits, no vendor lock-in.</p>
    <div class="code-block"><span class="comment"># 1. Request data</span>
{example_req}
<span class="comment"># → 402 Payment Required</span>

<span class="comment"># 2. Agent pays USDC, retries with payment header</span>
<span class="status"># → 200 OK</span>
{example_resp}</div>
  </section>

</div>

{FOOTER}

</body>
</html>"""


# ── Service detail page ─────────────────────────────────────────────────

def render_endpoint(ep):
    e = html.escape
    example = ""
    if ep.get("example_request"):
        example += f'\n<div class="ep-example">{e(ep["example_request"])}</div>'
    if ep.get("example_response"):
        example += f'\n<div class="ep-example">{e(ep["example_response"])}</div>'

    return f"""\
    <div class="endpoint">
      <div class="ep-header">
        <span class="method">{e(ep['method'])}</span>
        <span class="path">{e(ep['path'])}</span>
      </div>
      <div class="ep-desc">{e(ep['description'])}</div>
      <div class="ep-price">Price: <strong>{e(ep.get('price', 'TBD'))}</strong></div>{example}
    </div>"""


def build_detail(svc):
    e = html.escape
    status = svc["status"]
    tag_cls = "live" if status == "live" else "soon"
    tag_label = "Live" if status == "live" else "Coming Soon"

    endpoints_html = "\n".join(render_endpoint(ep) for ep in svc.get("endpoints", []))

    api_url = svc.get("url", "")
    api_link = f'<span>API: <strong><a href="{e(api_url)}">{e(api_url)}</a></strong></span>' if api_url else ""

    domain_note = ""
    if svc.get("domain"):
        domain_note = f'<span>Domain: <strong>{e(svc["domain"])}</strong></span>'

    details_paragraphs = ""
    if svc.get("details"):
        for para in svc["details"].strip().split("\n\n"):
            details_paragraphs += f"<p>{e(para.strip())}</p>\n"

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(svc['name'])} — x402agent</title>
<meta name="description" content="{e(svc['description'])}">
<link rel="canonical" href="https://x402agent.no/{svc['slug']}/">
<meta property="og:title" content="{e(svc['name'])} — x402agent">
<meta property="og:description" content="{e(svc['description'])}">
<meta property="og:url" content="https://x402agent.no/{svc['slug']}/">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<style>
{CSS}
</style>
</head>
<body>

<div class="container">

  <a href="/" class="back">&larr; All Services</a>

  <section class="detail-hero">
    <span class="product-tag {tag_cls}">{tag_label}</span>
    <h1>{e(svc['name'])}</h1>
    <p class="tagline">{e(svc.get('tagline', svc['description']))}</p>
    <div class="meta-row">
      <span>From <strong>{e(svc['price'])}</strong>/query</span>
      <span>{e(svc.get('currency', 'USDC on Base'))}</span>
      {api_link}
      {domain_note}
    </div>
  </section>

  <section class="section">
    <h2>Endpoints</h2>
{endpoints_html}
  </section>

  <section class="section">
    <h2>About</h2>
    <div class="details-text">
{details_paragraphs}
    </div>
  </section>

</div>

{FOOTER}

</body>
</html>"""


# ── Build ────────────────────────────────────────────────────────────────

def main():
    services = load_services()

    # Write index.html
    index_path = os.path.join(ROOT, "index.html")
    with open(index_path, "w") as f:
        f.write(build_index(services))
    print(f"  ✓ index.html")

    # Write detail pages
    for svc in services:
        if svc["status"] != "live":
            continue
        slug_dir = os.path.join(ROOT, svc["slug"])
        os.makedirs(slug_dir, exist_ok=True)
        detail_path = os.path.join(slug_dir, "index.html")
        with open(detail_path, "w") as f:
            f.write(build_detail(svc))
        print(f"  ✓ {svc['slug']}/index.html")

    print(f"\nBuilt {len(services)} services. Done.")


if __name__ == "__main__":
    main()
