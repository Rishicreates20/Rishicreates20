#!/usr/bin/env python3
"""
generate_heatmap.py
-------------------
Scrapes the public GitHub contributions calendar (no token required) and
renders it as an animated SVG whose cells reveal on a diagonal wave, then
hold. Caches the parsed data to data/contrib.json so a failed scrape falls
back to the last good copy.

Usage:
    python scripts/generate_heatmap.py <github-username> assets/heatmap.svg
    # optional 3rd arg: path to a data json to render instead of scraping
"""
import sys, os, json, datetime as dt

USER_DEFAULT = "Rishicreates20"

# GitHub green ramp (level 0..4) on a dark canvas
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
BG      = "#0d1117"
BAR     = "#161b22"
BORDER  = "#30363d"
DIM     = "#8b949e"
GREEN   = "#39d353"
GREEN2  = "#26a641"
DOTS    = ["#ff5f56", "#ffbd2e", "#27c93f"]

CELL, GAP, RAD = 11, 3, 2
PAD = 20
BAR_H = 34
TOP = 22          # room for month labels
LEFT = 30         # room for weekday labels
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
WDAYS  = {1:"Mon", 3:"Wed", 5:"Fri"}     # GitHub shows Mon/Wed/Fri

# ---------------------------------------------------------------- scrape
def scrape(user):
    import requests
    from bs4 import BeautifulSoup
    url = f"https://github.com/users/{user}/contributions"
    headers = {"User-Agent": "Mozilla/5.0 (profile-readme-bot)",
               "X-Requested-With": "XMLHttpRequest"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # tooltip -> exact count, keyed by the day cell id
    counts = {}
    for tip in soup.select("tool-tip"):
        tid = tip.get("for")
        txt = tip.get_text(" ", strip=True)
        n = 0
        if txt and txt[0].isdigit():
            n = int(txt.split()[0].replace(",", ""))
        elif txt.lower().startswith("no contribution"):
            n = 0
        if tid:
            counts[tid] = n

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        level = int(td.get("data-level", 0) or 0)
        cid = td.get("id")
        count = counts.get(cid, None)
        days.append({"date": date, "level": level,
                     "count": count if count is not None else level})
    if not days:
        raise RuntimeError("no day cells parsed; GitHub markup may have changed")
    days.sort(key=lambda d: d["date"])
    total = sum(d["count"] for d in days if isinstance(d["count"], int))
    return {"user": user, "days": days, "total": total,
            "generated": dt.datetime.utcnow().isoformat() + "Z"}

# ---------------------------------------------------------------- layout
def to_grid(data):
    days = data["days"]
    start = dt.date.fromisoformat(days[0]["date"])
    # GitHub's first column is a Sunday; align columns on that
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)
    cols = {}
    for d in days:
        date = dt.date.fromisoformat(d["date"])
        col = (date - start).days // 7
        row = (date.weekday() + 1) % 7          # Sun=0 .. Sat=6
        cols.setdefault(col, {})[row] = d
    ncols = max(cols) + 1
    return cols, ncols, start

# ---------------------------------------------------------------- svg
def build(data):
    cols, ncols, start = to_grid(data)
    grid_w = ncols * (CELL + GAP)
    W = LEFT + grid_w + 2 * PAD
    H = BAR_H + TOP + 7 * (CELL + GAP) + PAD + 30
    total = data.get("total", 0)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" role="img" aria-label="GitHub contribution heatmap">']
    o.append('<defs><style>'
             'text{font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,'
             'monospace;}</style></defs>')
    o.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" '
             f'fill="{BG}" stroke="{BORDER}" stroke-width="1.5"/>')
    o.append(f'<path d="M1 13 a12 12 0 0 1 12 -12 h{W-26} a12 12 0 0 1 12 12 '
             f'v{BAR_H-13} h-{W-2} z" fill="{BAR}"/>')
    for i, c in enumerate(DOTS):
        o.append(f'<circle cx="{22+i*22}" cy="{BAR_H//2}" r="6" fill="{c}"/>')
    o.append(f'<text x="{W//2}" y="{BAR_H//2+5}" text-anchor="middle" '
             f'fill="{DIM}" font-size="13">Rishicreates20 ~ $ ./contributions.sh</text>')

    gx = PAD + LEFT
    gy = BAR_H + TOP
    # month labels
    last_month = None
    for col in range(ncols):
        wk = cols.get(col)
        if not wk:
            continue
        any_day = min(wk.values(), key=lambda d: d["date"])
        m = dt.date.fromisoformat(any_day["date"]).month
        if m != last_month:
            x = gx + col * (CELL + GAP)
            o.append(f'<text x="{x}" y="{BAR_H+14}" fill="{DIM}" font-size="10">'
                     f'{MONTHS[m-1]}</text>')
            last_month = m
    # weekday labels
    for row, name in WDAYS.items():
        y = gy + row * (CELL + GAP) + CELL - 1
        o.append(f'<text x="{PAD-2}" y="{y}" fill="{DIM}" font-size="9" '
                 f'text-anchor="start">{name}</text>')

    # cells with diagonal reveal
    step = 0.018       # per-diagonal delay
    for col in range(ncols):
        for row in range(7):
            d = cols.get(col, {}).get(row)
            level = d["level"] if d else 0
            x = gx + col * (CELL + GAP)
            y = gy + row * (CELL + GAP)
            begin = (col + row) * step
            fill = LEVELS[level]
            o.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RAD}" '
                f'fill="{fill}" opacity="0" transform="scale(1)" '
                f'transform-origin="{x+CELL/2:.1f}px {y+CELL/2:.1f}px">'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.3f}s" dur="0.35s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="scale" '
                f'values="0.2;1.15;1" begin="{begin:.3f}s" dur="0.45s" '
                f'calcMode="spline" keySplines="0.34 1.2 0.6 1;0.2 0 0.2 1" '
                f'fill="freeze"/></rect>')

    # footer: total + legend
    fy = gy + 7 * (CELL + GAP) + 20
    o.append(f'<text x="{PAD}" y="{fy}" fill="{GREEN}" font-size="12" '
             f'font-weight="700">{total:,}</text>'
             f'<text x="{PAD+len(f"{total:,}")*8+4}" y="{fy}" fill="{DIM}" '
             f'font-size="12"> contributions in the last year</text>')
    lx = W - PAD - (len(LEVELS) * (CELL + GAP)) - 60
    o.append(f'<text x="{lx-30}" y="{fy}" fill="{DIM}" font-size="11">Less</text>')
    for i, c in enumerate(LEVELS):
        o.append(f'<rect x="{lx + i*(CELL+GAP)+6}" y="{fy-10}" width="{CELL}" '
                 f'height="{CELL}" rx="{RAD}" fill="{c}"/>')
    o.append(f'<text x="{lx + len(LEVELS)*(CELL+GAP)+10}" y="{fy}" fill="{DIM}" '
             f'font-size="11">More</text>')
    o.append('</svg>')
    return "\n".join(o)

# ---------------------------------------------------------------- main
def main():
    user = sys.argv[1] if len(sys.argv) > 1 else USER_DEFAULT
    outp = sys.argv[2] if len(sys.argv) > 2 else "assets/heatmap.svg"
    data_json = sys.argv[3] if len(sys.argv) > 3 else "data/contrib.json"

    data = None
    if len(sys.argv) > 3 and os.path.exists(data_json):
        data = json.load(open(data_json))       # render from provided cache
        print(f"[heatmap] rendering from cache {data_json}")
    else:
        try:
            data = scrape(user)
            os.makedirs(os.path.dirname(data_json) or ".", exist_ok=True)
            json.dump(data, open(data_json, "w"), indent=1)
            print(f"[heatmap] scraped {len(data['days'])} days, "
                  f"{data['total']} total")
        except Exception as e:
            sys.stderr.write(f"[heatmap] scrape failed: {e}\n")
            if os.path.exists(data_json):
                data = json.load(open(data_json))
                sys.stderr.write("[heatmap] using cached data\n")
            else:
                raise
    open(outp, "w").write(build(data))
    print(f"[heatmap] wrote {outp}")

if __name__ == "__main__":
    main()
