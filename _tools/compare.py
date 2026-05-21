"""
Compare the cloned site against the original.

For every URL in sitemap.xml:
  - Fetch original (www.datadiggers-mr.com) and mirror (claudewebsite.datadiggers-mr.com)
  - Record: HTTP status, byte length, title, image count, link count,
            form count, key integrations (GA/GTM/Cookiebot/HubSpot/reCAPTCHA),
            chat widget injection (mirror only)
  - Flag anomalies (status mismatch, missing assets, missing scripts)

Also samples a list of asset URLs referenced by mirror pages and verifies
each returns 200 — catches broken images.

Writes a human-readable summary to stdout.
"""

import re, requests, urllib3, sys
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

urllib3.disable_warnings()

ORIG = "https://www.datadiggers-mr.com"
MIRROR = "https://claudewebsite.datadiggers-mr.com"
SAMPLE_LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 0  # 0 = all

sess = requests.Session()
sess.headers.update({"User-Agent": "Mozilla/5.0 (compare-bot)"})
sess.verify = False

INTEGRATIONS = {
    "google-analytics": re.compile(r"google-analytics\.com|gtag/js|G-[A-Z0-9]+", re.I),
    "gtm":              re.compile(r"googletagmanager\.com|GTM-[A-Z0-9]+"),
    "cookiebot":        re.compile(r"cookiebot\.com"),
    "hubspot-forms":    re.compile(r"hsforms\.net|js\.hsforms"),
    "recaptcha":        re.compile(r"google\.com/recaptcha"),
    "chat-widget":      re.compile(r"DD_CHAT_ENDPOINT"),
    "webflow":          re.compile(r"created in Webflow"),
}

def fetch_features(url):
    try:
        r = sess.get(url, timeout=20, allow_redirects=True)
        if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type", ""):
            return {"status": r.status_code, "bytes": 0, "title": "", "imgs": 0, "links": 0, "forms": 0, "integrations": set()}
        html = r.text
        title = re.search(r"<title[^>]*>([^<]*)</title>", html, re.I)
        return {
            "status":       r.status_code,
            "bytes":        len(html),
            "title":        title.group(1).strip() if title else "",
            "imgs":         len(re.findall(r"<img\b", html, re.I)),
            "links":        len(re.findall(r"<a\s[^>]*href=", html, re.I)),
            "forms":        len(re.findall(r"<form\b", html, re.I)),
            "integrations": {k for k, p in INTEGRATIONS.items() if p.search(html)},
            "html":         html,
        }
    except Exception as e:
        return {"status": 0, "bytes": 0, "title": "", "imgs": 0, "links": 0, "forms": 0, "integrations": set(), "error": str(e)}

def get_sitemap():
    r = sess.get(f"{ORIG}/sitemap.xml", timeout=30)
    urls = re.findall(r"<loc>([^<]+)</loc>", r.text)
    # Convert to path-only
    paths = []
    seen = set()
    for u in urls:
        p = urlparse(u.strip()).path or "/"
        if p not in seen:
            seen.add(p); paths.append(p)
    return paths

def compare_one(path):
    o = fetch_features(ORIG + path)
    m = fetch_features(MIRROR + path)
    diff = {}
    diff["path"]              = path
    diff["orig_status"]       = o["status"]
    diff["mirror_status"]     = m["status"]
    diff["title_match"]       = (o.get("title", "") == m.get("title", ""))
    diff["bytes_orig"]        = o["bytes"]
    diff["bytes_mirror"]      = m["bytes"]
    diff["bytes_pct"]         = (m["bytes"] / o["bytes"] * 100) if o["bytes"] else 0
    diff["img_delta"]         = m["imgs"] - o["imgs"]
    diff["link_delta"]        = m["links"] - o["links"]
    diff["form_delta"]        = m["forms"] - o["forms"]
    diff["missing_in_mirror"] = o["integrations"] - m["integrations"] - {"webflow"}  # webflow is fine
    diff["extra_in_mirror"]   = m["integrations"] - o["integrations"]
    return diff

def check_assets_subset(mirror_html, base_url, limit=30):
    """Verify a sample of asset URLs from a mirror page return 200."""
    asset_urls = set()
    for m in re.finditer(r"""(?:src|href)=["']([^"']+)["']""", mirror_html):
        u = m.group(1)
        if u.startswith("/_assets/") or u.startswith("_assets/"):
            absu = urljoin(base_url, u)
            asset_urls.add(absu)
    sample = list(asset_urls)[:limit]
    results = []
    for url in sample:
        try:
            r = sess.head(url, timeout=10, allow_redirects=True)
            results.append((url, r.status_code))
        except Exception as e:
            results.append((url, 0))
    return results

def main():
    print("Reading sitemap…", flush=True)
    paths = get_sitemap()
    if SAMPLE_LIMIT:
        paths = paths[:SAMPLE_LIMIT]
    print(f"  {len(paths)} URLs", flush=True)

    print("Comparing pages (20 threads)…", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futs = {ex.submit(compare_one, p): p for p in paths}
        for i, fut in enumerate(as_completed(futs), 1):
            results.append(fut.result())
            if i % 50 == 0:
                print(f"  {i}/{len(paths)}", flush=True)

    # ============================ SUMMARY ===========================
    print()
    print("=" * 60)
    print("PAGE-LEVEL SUMMARY")
    print("=" * 60)

    both_200 = sum(1 for r in results if r["orig_status"] == 200 and r["mirror_status"] == 200)
    orig_200 = sum(1 for r in results if r["orig_status"] == 200)
    mirror_200 = sum(1 for r in results if r["mirror_status"] == 200)
    only_orig = [r for r in results if r["orig_status"] == 200 and r["mirror_status"] != 200]
    only_mirror = [r for r in results if r["orig_status"] != 200 and r["mirror_status"] == 200]
    title_mismatches = [r for r in results if r["orig_status"] == 200 and r["mirror_status"] == 200 and not r["title_match"]]

    print(f"Pages on original: {orig_200}/{len(results)}")
    print(f"Pages on mirror:   {mirror_200}/{len(results)}")
    print(f"Both 200:          {both_200}")
    print(f"Only on original:  {len(only_orig)}")
    print(f"Only on mirror:    {len(only_mirror)}")
    print(f"Title mismatches:  {len(title_mismatches)}")

    if only_orig:
        print(f"\nMissing from mirror (sample):")
        for r in only_orig[:10]:
            print(f"  {r['mirror_status']} {r['path']}")
    if title_mismatches:
        print(f"\nTitle mismatches (sample):")
        for r in title_mismatches[:5]:
            print(f"  {r['path']}")

    # Both-200 page stats
    both = [r for r in results if r["orig_status"] == 200 and r["mirror_status"] == 200]
    if both:
        print()
        print("=" * 60)
        print("CONTENT-LEVEL SUMMARY (pages that returned 200 on both)")
        print("=" * 60)

        avg_bytes_pct = sum(r["bytes_pct"] for r in both) / len(both)
        print(f"Avg HTML size on mirror vs original: {avg_bytes_pct:.1f}%")

        # Count integration coverage
        orig_int_counts = Counter()
        mirror_int_counts = Counter()
        for r in both:
            for k in r["missing_in_mirror"]: orig_int_counts[k] += 1
        # We need to know how many pages had each integration on original; track separately
        # Reload: for both pages refetch quickly via existing counts
        # Easier: count from results
        print()
        print("Integrations present on original but missing on mirror (pages affected):")
        if not orig_int_counts:
            print("  (none — every integration preserved)")
        else:
            for k, c in orig_int_counts.most_common():
                print(f"  {c:4d}  {k}")

        # Image / link / form deltas
        img_diffs = Counter(r["img_delta"] for r in both)
        link_diffs = Counter(r["link_delta"] for r in both)
        form_diffs = Counter(r["form_delta"] for r in both)

        print()
        print(f"Image-count diff (mirror minus original):")
        for delta, count in sorted(img_diffs.items())[:10]:
            print(f"  delta {delta:+3d}: {count} pages")
        print(f"\nLink-count diff:")
        for delta, count in sorted(link_diffs.items())[:10]:
            print(f"  delta {delta:+3d}: {count} pages")
        print(f"\nForm-count diff:")
        for delta, count in sorted(form_diffs.items())[:10]:
            print(f"  delta {delta:+3d}: {count} pages")

    # Spot-check assets on the homepage
    print()
    print("=" * 60)
    print("ASSET HEALTH CHECK (sample of mirror's homepage assets)")
    print("=" * 60)
    hp = fetch_features(MIRROR + "/")
    if hp.get("html"):
        sample = check_assets_subset(hp["html"], MIRROR + "/")
        ok = sum(1 for _, s in sample if s == 200)
        broken = [(u, s) for u, s in sample if s != 200]
        print(f"Sampled {len(sample)} assets; OK: {ok}; broken: {len(broken)}")
        for u, s in broken[:10]:
            print(f"  {s}  {u[-100:]}")

if __name__ == "__main__":
    main()
