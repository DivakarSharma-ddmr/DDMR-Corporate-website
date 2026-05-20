"""
Inject the DataDiggers AI chat widget into every HTML file in a folder.

- Adds <link rel="stylesheet" href="/css/chat.css"> just before </head>
- Adds <script>window.DD_CHAT_ENDPOINT="…"</script> and
        <script src="/js/chat.js"></script> just before </body>

Idempotent — if the chat widget is already present, skips the file.
Uses absolute paths (/css/…, /js/…), so the chat files must live at
those locations in the repo root (and the site must be served at the
root of its domain, which we already do at claudewebsite.datadiggers-mr.com).
"""

import os, sys, re

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
WORKER = "https://datadiggers-chat.divakar-sharma.workers.dev/api/chat"

HEAD_INJECTION = '<link rel="stylesheet" href="/css/chat.css">'
BODY_INJECTION = (
    f'<script>window.DD_CHAT_ENDPOINT="{WORKER}";</script>'
    '<script src="/js/chat.js" defer></script>'
)

MARKER = "DD_CHAT_ENDPOINT"

def inject_one(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()
    except Exception as e:
        print(f"  read fail: {path}: {e}")
        return False
    if MARKER in html:
        return False  # already injected
    new = html
    # Add CSS before </head> (first occurrence)
    if "</head>" in new:
        new = new.replace("</head>", f"  {HEAD_INJECTION}\n</head>", 1)
    # Add JS before </body> (last occurrence)
    idx = new.rfind("</body>")
    if idx >= 0:
        new = new[:idx] + f"  {BODY_INJECTION}\n" + new[idx:]
    else:
        new += f"\n{BODY_INJECTION}\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return True

def main():
    count = 0; injected = 0
    for dirpath, _, files in os.walk(ROOT):
        # Skip our own asset cache
        if "_assets" in dirpath.split(os.sep): continue
        if ".git" in dirpath.split(os.sep): continue
        if "node_modules" in dirpath.split(os.sep): continue
        for name in files:
            if name.endswith(".html"):
                count += 1
                full = os.path.join(dirpath, name)
                if inject_one(full):
                    injected += 1
    print(f"Scanned {count} HTML files. Injected chat widget into {injected}.")

if __name__ == "__main__":
    main()
