"""
Mirror www.datadiggers-mr.com to a local folder.

Walks sitemap.xml, downloads each page, discovers every asset reference
(img/src, link/href, script/src, srcset, inline style url(), meta og:image),
downloads assets, and rewrites every URL in the HTML to a local relative path.

Output structure:
  out/
    index.html                          # homepage
    company/index.html                  # /company
    case-studies/foo/index.html         # /case-studies/foo
    _assets/<host>/<path>               # all downloaded assets

This way the local URLs match the production URLs exactly (so internal
links keep working) and GitHub Pages serves index.html for /<path>/.
"""

import os, re, sys, time, hashlib, html as html_module, traceback
import requests, urllib3
from urllib.parse import urlparse, urljoin, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

# Windows-invalid path chars + control chars
INVALID_PATH_CHARS = re.compile(r'[<>:"|?*\x00-\x1f]')

urllib3.disable_warnings()

BASE = "https://www.datadiggers-mr.com"
OUT  = sys.argv[1] if len(sys.argv) > 1 else "out"

# Hosts whose assets we want to localise. Anything else (GA, GTM, Cookiebot,
# HubSpot Forms etc.) stays hot-linked.
ASSET_HOSTS = {
    "www.datadiggers-mr.com",
    "datadiggers-mr.com",
    "cdn.prod.website-files.com",
    "d3e54v103j8qbb.cloudfront.net",
    "uploads-ssl.webflow.com",
    "assets.website-files.com",
    "global-uploads.webflow.com",
}
# Same-domain hosts (where pages also live). For URLs on these hosts, only
# treat as an asset if the URL has one of the recognised asset extensions —
# otherwise it's an internal page link, not something to download separately.
PAGE_HOSTS = {"www.datadiggers-mr.com", "datadiggers-mr.com"}
ASSET_EXTS = {
    ".jpg",".jpeg",".png",".gif",".webp",".svg",".ico",".avif",".bmp",
    ".mp4",".webm",".mov",".mp3",".wav",".ogg",".m4a",
    ".css",".js",".mjs",".map",
    ".woff",".woff2",".ttf",".otf",".eot",
    ".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx",
    ".json",".xml",".txt",".zip"
}

sess = requests.Session()
sess.headers.update({"User-Agent": "Mozilla/5.0 (DDMirror)"})
sess.verify = False

# ---------------------------------------------------------------- 1) URLS
def get_sitemap_urls():
    r = sess.get(f"{BASE}/sitemap.xml", timeout=30)
    r.raise_for_status()
    urls = re.findall(r"<loc>([^<]+)</loc>", r.text)
    # de-dup, keep order
    seen, out = set(), []
    for u in urls:
        u = u.strip()
        if u not in seen:
            seen.add(u); out.append(u)
    return out

# --------------------------------------------------------------- 2) PAGES
def page_local_path(page_url):
    p = urlparse(page_url).path
    p = p.strip("/")
    if not p:
        return "index.html"
    if "." in os.path.basename(p):
        return p  # already a file (e.g. .pdf)
    return f"{p}/index.html"

def fetch_page(url):
    try:
        r = sess.get(url, timeout=30, allow_redirects=True)
        if r.status_code == 200 and "text/html" in r.headers.get("Content-Type", ""):
            return url, r.text
    except Exception as e:
        print(f"  PAGE FAIL {url}: {e}", flush=True)
    return url, None

# -------------------------------------------------------------- 3) ASSETS
ATTR_PATTERNS = [
    re.compile(r"""(\s(?:src|href|data-src|poster|content)\s*=\s*["'])([^"']+)(["'])""", re.I),
]
SRCSET_PATTERN = re.compile(r"""(\ssrcset\s*=\s*["'])([^"']+)(["'])""", re.I)
CSS_URL_PATTERN = re.compile(r"""url\((["']?)([^)"']+)(\1)\)""", re.I)

def absolutize(url, page_url):
    if not url: return None
    # HTML-decode entities like &amp; and &quot; that sneak in from attribute values
    url = html_module.unescape(url).strip()
    if not url: return None
    # Reject obviously bad URLs (whitespace, quotes, ampersand at start)
    if any(c in url for c in (' ', '"', "'", '\n', '\r', '\t')): return None
    if url.startswith("data:") or url.startswith("mailto:") or url.startswith("tel:") or url.startswith("javascript:") or url.startswith("#"):
        return None
    if url.startswith("//"): return "https:" + url
    if url.startswith("http"): return url
    # Skip protocol-other-than-http
    if "://" in url: return None
    return urljoin(page_url, url)

def is_asset_host(url):
    if not url: return False
    try:
        p = urlparse(url)
        host = p.netloc.lower()
        if host not in ASSET_HOSTS: return False
        # On the main domain, only treat URLs with asset extensions as assets
        if host in PAGE_HOSTS:
            ext = os.path.splitext(p.path)[1].lower()
            return ext in ASSET_EXTS
        return True
    except Exception:
        return False

def discover_assets_in_page(html, page_url):
    found = set()
    # src/href/etc
    for p in ATTR_PATTERNS:
        for m in p.finditer(html):
            u = absolutize(m.group(2), page_url)
            if is_asset_host(u): found.add(u)
    # srcset (comma-separated url + descriptor)
    for m in SRCSET_PATTERN.finditer(html):
        for part in m.group(2).split(","):
            url = part.strip().split()
            if url:
                u = absolutize(url[0], page_url)
                if is_asset_host(u): found.add(u)
    # url() in inline styles
    for m in CSS_URL_PATTERN.finditer(html):
        u = absolutize(m.group(2), page_url)
        if is_asset_host(u): found.add(u)
    return found

def sanitize_path_segment(s):
    """Replace Windows-invalid characters with _ in a single path segment."""
    return INVALID_PATH_CHARS.sub("_", s)

def asset_local_path(url):
    p = urlparse(url)
    host = sanitize_path_segment(p.netloc)
    path = p.path
    if p.query:
        h = hashlib.md5(p.query.encode()).hexdigest()[:8]
        base, ext = os.path.splitext(path)
        path = f"{base}_{h}{ext}"
    if not path or path.endswith("/"):
        path = path + "_index"
    # Sanitize each segment
    segments = [sanitize_path_segment(seg) for seg in path.split("/") if seg]
    # Cap each segment to 80 chars to avoid Windows MAX_PATH (260) blowing up
    segments = [seg[:80] if len(seg) > 80 else seg for seg in segments]
    safe_path = "/".join(segments)
    return f"_assets/{host}/{safe_path}"

def fetch_asset(url):
    try:
        local = asset_local_path(url)
        full = os.path.join(OUT, local)
        if os.path.exists(full):
            return url, local, 0
        os.makedirs(os.path.dirname(full), exist_ok=True)
        r = sess.get(url, timeout=60, stream=True)
        if r.status_code == 200:
            with open(full, "wb") as f:
                size = 0
                for chunk in r.iter_content(8192):
                    f.write(chunk); size += len(chunk)
            # If it's a CSS file, scan it for further asset refs
            if "text/css" in r.headers.get("Content-Type", "") or url.endswith(".css"):
                try:
                    with open(full, "r", encoding="utf-8", errors="replace") as f:
                        css = f.read()
                    nested = set()
                    for m in CSS_URL_PATTERN.finditer(css):
                        u = absolutize(m.group(2), url)
                        if is_asset_host(u): nested.add(u)
                    return url, local, size, nested
                except Exception:
                    pass
            return url, local, size
    except Exception as e:
        # Don't crash the run on a single bad asset
        print(f"  ASSET FAIL {url[:120]}: {type(e).__name__}: {e}", flush=True)
    return url, None, 0

# ---------------------------------------------------- 4) URL REWRITE
def relpath_from(page_local, target_local):
    """Compute relative path from page_local to target_local, both relative to OUT."""
    if not target_local:
        target_local = "."
    page_dir = os.path.dirname(page_local) or "."
    rel = os.path.relpath(target_local, page_dir)
    return rel.replace("\\", "/")

def page_directory(local_path):
    """Directory portion (for href to a page index.html). '' for root."""
    d = os.path.dirname(local_path)
    return d if d else "."

def rewrite_html(html, page_url, page_local, asset_map, page_paths):
    """Replace every absolute URL we mirrored with its local relative equivalent."""
    # 1. Asset URLs: replace each with relative path
    def replace_asset(m):
        original = m.group(0)
        url_text = m.group(2)
        u = absolutize(url_text, page_url)
        if u in asset_map:
            rel = relpath_from(page_local, asset_map[u])
            return f"{m.group(1)}{rel}{m.group(3)}"
        return original
    for p in ATTR_PATTERNS:
        html = p.sub(replace_asset, html)

    def replace_srcset(m):
        prefix, value, suffix = m.group(1), m.group(2), m.group(3)
        new_parts = []
        for part in value.split(","):
            stripped = part.strip()
            if not stripped:
                continue
            bits = stripped.split(None, 1)
            url = bits[0]; rest = bits[1] if len(bits) > 1 else ""
            u = absolutize(url, page_url)
            if u in asset_map:
                rel = relpath_from(page_local, asset_map[u])
                new_parts.append((rel + (" " + rest if rest else "")))
            else:
                new_parts.append(stripped)
        return f"{prefix}{', '.join(new_parts)}{suffix}"
    html = SRCSET_PATTERN.sub(replace_srcset, html)

    def replace_css_url(m):
        quote_open, url_text, quote_close = m.group(1), m.group(2), m.group(3)
        u = absolutize(url_text, page_url)
        if u in asset_map:
            rel = relpath_from(page_local, asset_map[u])
            return f"url({quote_open}{rel}{quote_close})"
        return m.group(0)
    html = CSS_URL_PATTERN.sub(replace_css_url, html)

    # 2. Internal page links: absolute URLs to the original domain → local
    # Use directory-style relative paths (e.g. "company/", "../", "./")
    page_dir = page_directory(page_local)
    for orig_url, local_target in page_paths.items():
        target_dir = page_directory(local_target)
        if target_dir == page_dir:
            rel = "./"
        else:
            rel = os.path.relpath(target_dir, page_dir).replace("\\", "/")
            if not rel.endswith("/"): rel = rel + "/"
        # Replace href="<url>" and href="<url>/" and href="<url>#fragment"
        for variant in (orig_url, orig_url + "/"):
            html = html.replace(f'href="{variant}"', f'href="{rel}"')
            html = html.replace(f"href='{variant}'", f"href='{rel}'")
            html = html.replace(f'href="{variant}#', f'href="{rel}#')
            html = html.replace(f"href='{variant}#", f"href='{rel}#")
    return html

# --------------------------------------------------------------- MAIN
def main():
    os.makedirs(OUT, exist_ok=True)
    print(f"[1/5] Reading sitemap…", flush=True)
    urls = get_sitemap_urls()
    print(f"      Found {len(urls)} page URLs", flush=True)

    print(f"[2/5] Downloading pages (10 threads)…", flush=True)
    pages = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(fetch_page, u): u for u in urls}
        for i, fut in enumerate(as_completed(futures), 1):
            url, html = fut.result()
            if html:
                pages[url] = html
            if i % 50 == 0:
                print(f"      {i}/{len(urls)} pages downloaded", flush=True)
    print(f"      {len(pages)} pages OK", flush=True)

    print(f"[3/5] Discovering assets…", flush=True)
    assets_to_fetch = set()
    for u, h in pages.items():
        assets_to_fetch.update(discover_assets_in_page(h, u))
    print(f"      {len(assets_to_fetch)} unique assets", flush=True)

    print(f"[4/5] Downloading assets (20 threads)…", flush=True)
    asset_map = {}
    total_bytes = 0
    pending = set(assets_to_fetch)
    done_count = 0
    pass_num = 0
    while pending:
        pass_num += 1
        batch = list(pending)
        pending = set()
        with ThreadPoolExecutor(max_workers=20) as ex:
            futures = [ex.submit(fetch_asset, u) for u in batch]
            for fut in as_completed(futures):
                result = fut.result()
                url, local = result[0], result[1]
                if local:
                    asset_map[url] = local
                    total_bytes += result[2] if len(result) > 2 else 0
                    if len(result) >= 4:
                        for n in result[3]:
                            if n not in asset_map: pending.add(n)
                done_count += 1
                if done_count % 100 == 0:
                    print(f"      {done_count} assets done, {total_bytes/1024/1024:.1f} MB", flush=True)
        print(f"      pass {pass_num} done, {len(pending)} new asset refs", flush=True)
    print(f"      {len(asset_map)} assets, {total_bytes/1024/1024:.1f} MB total", flush=True)

    # Pre-compute local path for each page URL
    page_paths = {u: page_local_path(u) for u in pages.keys()}

    print(f"[5/5] Rewriting HTML and writing files…", flush=True)
    for i, (url, html) in enumerate(pages.items(), 1):
        local = page_paths[url]
        out_path = os.path.join(OUT, local)
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        rewritten = rewrite_html(html, url, local, asset_map, page_paths)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(rewritten)
        if i % 100 == 0:
            print(f"      {i}/{len(pages)} pages written", flush=True)
    print(f"      Done. Output in {OUT}/", flush=True)
    print(f"      Pages: {len(pages)}  Assets: {len(asset_map)}  Size: {total_bytes/1024/1024:.1f} MB", flush=True)

if __name__ == "__main__":
    main()
