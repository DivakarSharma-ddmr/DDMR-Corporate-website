"""
Rename every file under _assets/ from its URL-encoded name to the decoded
name. Necessary because GitHub Pages decodes %20, %28 etc. in incoming URLs
before looking up files on disk — files saved with literal '%20' in the
filename will 404.

After: HTML references stay encoded ('Logo%20navbar.svg'), the browser sends
encoded, GitHub Pages decodes to 'Logo navbar.svg', file is found.

Runs bottom-up (deepest paths first) so that renaming files inside a folder
happens before renaming the folder itself.
"""
import os, sys
from urllib.parse import unquote

ROOT = sys.argv[1] if len(sys.argv) > 1 else "_assets"

renames = 0
collisions = 0

for dirpath, dirnames, filenames in os.walk(ROOT, topdown=False):
    # Files first
    for name in filenames:
        decoded = unquote(name)
        if decoded != name:
            old = os.path.join(dirpath, name)
            new = os.path.join(dirpath, decoded)
            if os.path.exists(new):
                collisions += 1
                continue
            try:
                os.rename(old, new)
                renames += 1
            except Exception as e:
                print(f"  rename fail: {old} -> {new}: {e}")
    # Then directories
    for name in dirnames:
        decoded = unquote(name)
        if decoded != name:
            old = os.path.join(dirpath, name)
            new = os.path.join(dirpath, decoded)
            if os.path.exists(new):
                collisions += 1
                continue
            try:
                os.rename(old, new)
                renames += 1
            except Exception as e:
                print(f"  rename fail: {old} -> {new}: {e}")

print(f"Renamed {renames} files/dirs. Collisions: {collisions}.")
