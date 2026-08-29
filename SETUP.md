# Setup guide — your animated GitHub profile README

This repo generates a terminal-styled, self-animating GitHub profile out of
three SVGs (no third-party image services, no JavaScript):

| File | What it is | How it's made |
|------|-----------|---------------|
| `assets/ascii.svg` | ASCII self-portrait that types itself in | generated **once** from your photo |
| `assets/info-card.svg` | neofetch-style panel that fades in line-by-line | generated **once** from `scripts/generate_infocard.py` |
| `assets/heatmap.svg` | your real contribution calendar, revealing on a diagonal | re-generated **daily** by GitHub Actions |

Everything animates because GitHub renders **SMIL / CSS animations inside SVG**
files embedded as `<img>` — even though it strips `<script>` from READMEs.

---

## 1. Create the special profile repo

GitHub shows the README of a repo named **exactly** the same as your username on
your profile page.

1. Go to **github.com/new**.
2. Repository name: **`Rishicreates20`** (must match your username exactly).
3. Set it **Public**, tick **Add a README**, and create it.

You'll see a note: *"You found a secret! Rishicreates20/Rishicreates20 is a
special repository…"* — that's the one.

## 2. Add these files to the repo

Clone it and copy in everything from this bundle, then push:

```bash
git clone https://github.com/Rishicreates20/Rishicreates20.git
cd Rishicreates20
# copy README.md, SETUP.md, requirements.txt, .gitignore,
# and the assets/ scripts/ data/ .github/ folders in here
git add .
git commit -m "feat: animated terminal profile"
git push
```

Your profile is now live at **github.com/Rishicreates20** 🎉

> The `assets/heatmap.svg` shipped here uses **sample** contribution data so the
> layout looks right immediately. Step 4 replaces it with your real numbers.

## 3. Turn on the daily heatmap refresh

The workflow in `.github/workflows/refresh-heatmap.yml` re-scrapes your public
contribution calendar every day at 06:17 UTC and commits the updated SVG.

1. In the repo, open the **Settings → Actions → General**.
2. Under **Workflow permissions**, select **Read and write permissions**, Save.
   (This lets the Action commit the refreshed SVG.)
3. Open the **Actions** tab, pick **"Refresh contribution heatmap"**, and click
   **Run workflow** once to populate your real data immediately.

That's it — it now updates itself daily. The commit message ends in `[skip ci]`
so it never triggers itself in a loop.

---

## Regenerating the static pieces

You only need this if you want to change your photo or your info-card text.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1) ASCII portrait — swap assets/me.jpg for any photo first
python scripts/generate_ascii.py assets/me.jpg assets/ascii.svg

# 2) Info card — edit the DATA block at the top of the script, then:
python scripts/generate_infocard.py assets/info-card.svg

# 3) Heatmap (normally the Action does this):
python scripts/generate_heatmap.py Rishicreates20 assets/heatmap.svg
```

### Preview the animations locally (optional)

The SVGs animate in a browser, so to preview them as images:

```bash
pip install playwright && playwright install chromium
python scripts/render.py assets/ascii.svg preview.png 6000   # waits 6s, screenshots
```

---

## Tuning tips

**ASCII portrait** (`scripts/generate_ascii.py`, top of file):
- `COLS` — width in characters (higher = more detail, bigger SVG). 74 is a good balance.
- `CHAR_ASPECT` — raise if the face looks vertically squashed.
- `GREENS` — the shade ramp; swap for any palette (e.g. amber, Dracula purples).
- Photo tips: a clear, front-lit, high-contrast headshot gives the cleanest result.

**Info card** (`scripts/generate_infocard.py`):
- Edit the `ROWS = [...]` list — each `(label, value)` becomes a line. Keep values
  short so they fit the panel; the panel width auto-fits the longest line.

**Heatmap** (`scripts/generate_heatmap.py`):
- `LEVELS` — the 5 green shades (level 0–4). `CELL`, `GAP`, `RAD` — cell geometry.
- The cron in the workflow (`17 6 * * *`) sets the daily refresh time (UTC).

## How the "no token" scrape works

`generate_heatmap.py` GETs `https://github.com/users/<you>/contributions`, which
returns the calendar HTML publicly — no auth. It reads each day's `data-date` and
`data-level`, plus exact counts from the `<tool-tip>` elements, caches them to
`data/contrib.json` (so a failed scrape falls back to the last good copy), and
re-renders the SVG.
