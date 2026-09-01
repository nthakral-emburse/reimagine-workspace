#!/usr/bin/env python3
"""Extract every Backbone route from mercury into a table."""

import os, re, csv

ROOT = "repos/legacy/mercury/js"
OUT_DIR = "notes/survey"

# matches:  routes: { ... }   or   appRoutes: { ... }
BLOCK = re.compile(r"\b(?:appRoutes|routes)\s*:\s*\{(.*?)\}", re.S)
# matches:  'some/url': 'handlerName'
PAIR = re.compile(r"""['"]([^'"]*)['"]\s*:\s*['"]([^'"]+)['"]""")


def area_for(path):
    """Guess the feature area from the file path."""
    parts = path.replace("\\", "/").split("/")
    if "products" in parts:
        i = parts.index("products")
        return "/".join(parts[i + 1:i + 3]).rsplit("/", 1)[0] if len(parts) > i + 2 else parts[i + 1]
    if "routers" in parts:
        return "dashboard"
    if "cr_core" in parts:
        return "core"
    return "other"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in ("node_modules", "bower_components")]
        for fn in filenames:
            if not fn.endswith(".js"):
                continue
            full = os.path.join(dirpath, fn)
            try:
                text = open(full, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            if "Router.extend" not in text:
                continue

            for block in BLOCK.findall(text):
                for url, handler in PAIR.findall(block):
                    rows.append({
                        "area": area_for(full),
                        "url": url,
                        "handler": handler,
                        "file": full,
                    })

    rows.sort(key=lambda r: (r["area"], r["url"]))

    with open(f"{OUT_DIR}/mercury-routes.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["area", "url", "handler", "file"])
        w.writeheader()
        w.writerows(rows)

    # readable version, grouped by area
    by_area = {}
    for r in rows:
        by_area.setdefault(r["area"], []).append(r)

    with open(f"{OUT_DIR}/mercury-routes.md", "w") as f:
        f.write("# Mercury routes\n\n")
        f.write(f"{len(rows)} routes across {len(by_area)} areas.\n\n")
        for area in sorted(by_area):
            f.write(f"## {area}  ({len(by_area[area])})\n\n")
            for r in by_area[area]:
                f.write(f"- `{r['url']}` -> `{r['handler']}`  \n  <sub>{r['file']}</sub>\n")
            f.write("\n")

    print(f"{len(rows)} routes, {len(by_area)} areas")
    for area in sorted(by_area):
        print(f"  {len(by_area[area]):3d}  {area}")


if __name__ == "__main__":
    main()