#!/usr/bin/env python3
"""
generate_ascii.py
-----------------
Turns a photo into a self-typing ASCII-art portrait SVG for a GitHub profile
README. Removes the background (rembg), boosts local contrast (CLAHE), maps
brightness to a glyph density ramp, and emits an animated SVG whose rows wipe
in horizontally, staggered top-to-bottom, then freeze.

Usage:
    python scripts/generate_ascii.py assets/me.jpg assets/ascii.svg
"""
import sys
import html
import numpy as np
from PIL import Image
import cv2

# ---------------------------------------------------------------- config
COLS          = 74            # width of the portrait in characters
CHAR_ASPECT   = 2.15          # glyph height / width (monospace cells are tall)
FONT_SIZE     = 13            # px
LINE_HEIGHT   = 13            # px  (dense, terminal-like)
CHAR_WIDTH    = FONT_SIZE * 0.60
PAD           = 16            # px padding around the art
# dark -> dense glyph, bright -> sparse.  index 0 = brightest.
RAMP          = " .`'\",:;Il!i~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
# GitHub-dark + green palette; brightness picks a shade for subtle depth
GREENS        = ["#0e4429", "#006d32", "#26a641", "#39d353", "#56d364", "#7ee787"]
BG            = "#0d1117"
CURSOR        = "#39d353"

def load_matte(path):
    """Return (gray[0..255] float, alpha[0..1] float) with background removed."""
    try:
        from rembg import remove, new_session
        # lightweight model keeps memory + download small and CI-friendly
        session = new_session("u2netp")
        src = Image.open(path).convert("RGBA")
        cut = remove(src, session=session)      # RGBA, subject on transparent bg
        rgba = np.asarray(cut).astype(np.float32)
        alpha = rgba[:, :, 3] / 255.0
        rgb = rgba[:, :, :3]
    except Exception as e:                      # fallback: use whole image
        sys.stderr.write(f"[ascii] rembg unavailable ({e}); using full frame\n")
        rgb = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
        alpha = np.ones(rgb.shape[:2], np.float32)

    gray = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    # local contrast so facial features survive the downsample
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray).astype(np.float32)
    return gray, alpha

def crop_to_subject(gray, alpha):
    ys, xs = np.where(alpha > 0.4)
    if len(xs) == 0:
        return gray, alpha
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()
    m = int(0.04 * max(y1 - y0, x1 - x0))       # small margin
    y0 = max(0, y0 - m); x0 = max(0, x0 - m)
    y1 = min(gray.shape[0], y1 + m); x1 = min(gray.shape[1], x1 + m)
    return gray[y0:y1, x0:x1], alpha[y0:y1, x0:x1]

def to_grid(gray, alpha):
    """Sample the image into a COLS-wide char grid; return glyphs + shade idx."""
    h, w = gray.shape
    cw = w / COLS
    ch = cw * CHAR_ASPECT
    rows = max(1, int(h / ch))
    glyphs, shades = [], []
    for r in range(rows):
        g_row, s_row = [], []
        for c in range(COLS):
            y0 = int(r * ch); y1 = max(y0 + 1, int((r + 1) * ch))
            x0 = int(c * cw); x1 = max(x0 + 1, int((c + 1) * cw))
            a = float(alpha[y0:y1, x0:x1].mean())
            if a < 0.35:                         # background -> empty cell
                g_row.append(" "); s_row.append(-1); continue
            b = float(gray[y0:y1, x0:x1].mean()) / 255.0   # 0 dark .. 1 bright
            gi = int((1.0 - b) * (len(RAMP) - 1))
            g_row.append(RAMP[len(RAMP) - 1 - gi] if False else RAMP[gi])
            si = min(len(GREENS) - 1, int(b * len(GREENS)))
            s_row.append(si)
        glyphs.append(g_row); shades.append(s_row)
    return glyphs, shades

def trim_blank_edges(glyphs, shades):
    def blank(row): return all(ch == " " for ch in row)
    while glyphs and blank(glyphs[0]):
        glyphs.pop(0); shades.pop(0)
    while glyphs and blank(glyphs[-1]):
        glyphs.pop(); shades.pop()
    return glyphs, shades

def build_svg(glyphs, shades):
    rows = len(glyphs)
    grid_w = COLS * CHAR_WIDTH
    W = int(grid_w + 2 * PAD)
    H = int(rows * LINE_HEIGHT + 2 * PAD + 6)
    row_delay = 0.055                            # stagger between rows (s)
    wipe_dur  = 0.42                             # wipe duration per row (s)

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="ASCII self-portrait">')
    out.append('<defs>')
    out.append(
        '<style>text{font-family:"SFMono-Regular",Consolas,"Liberation Mono",'
        'Menlo,monospace;font-size:%dpx;white-space:pre;}</style>' % FONT_SIZE)
    out.append('</defs>')
    out.append(f'<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>')

    for r, (grow, srow) in enumerate(zip(glyphs, shades)):
        y = PAD + FONT_SIZE + r * LINE_HEIGHT
        begin = f'{r * row_delay:.3f}s'
        clip_id = f'w{r}'
        # per-row horizontal wipe
        out.append(
            f'<clipPath id="{clip_id}"><rect x="{PAD}" y="{y - FONT_SIZE}" '
            f'height="{LINE_HEIGHT + 2}" width="0">'
            f'<animate attributeName="width" from="0" to="{grid_w:.1f}" '
            f'begin="{begin}" dur="{wipe_dur}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.4 0 0.2 1" keyTimes="0;1"/>'
            f'</rect></clipPath>')
        out.append(f'<g clip-path="url(#{clip_id})">')
        # group runs of same shade into <tspan> for compact colored text
        x = PAD
        spans, run, run_shade = [], [], None
        def flush(cur_x):
            if not run:
                return cur_x
            text = html.escape("".join(run))
            length = len(run) * CHAR_WIDTH
            color = GREENS[run_shade] if run_shade >= 0 else BG
            spans.append(
                f'<tspan x="{cur_x:.1f}" textLength="{length:.1f}" '
                f'lengthAdjust="spacingAndGlyphs" fill="{color}">{text}</tspan>')
            return cur_x + length
        for ch, sh in zip(grow, srow):
            if sh != run_shade and run:
                x = flush(x); run = []
            run_shade = sh; run.append(ch)
        x = flush(x)
        out.append(f'<text y="{y}" xml:space="preserve">{"".join(spans)}</text>')
        out.append('</g>')

    # blinking cursor that lands after the last row finishes typing
    last_begin = rows * row_delay + wipe_dur
    cy = PAD + rows * LINE_HEIGHT
    out.append(
        f'<rect x="{PAD}" y="{cy - FONT_SIZE + 2}" width="{CHAR_WIDTH:.1f}" '
        f'height="{FONT_SIZE}" fill="{CURSOR}" opacity="0">'
        f'<animate attributeName="opacity" values="0;0;1" '
        f'keyTimes="0;{last_begin/(last_begin+1.2):.3f};1" '
        f'dur="{last_begin + 1.2:.2f}s" fill="freeze"/>'
        f'<animate attributeName="opacity" values="1;1;0;0;1" begin="{last_begin+1.2:.2f}s" '
        f'dur="1.1s" repeatCount="indefinite"/></rect>')
    out.append('</svg>')
    return "\n".join(out)

def main():
    inp = sys.argv[1] if len(sys.argv) > 1 else "assets/me.jpg"
    outp = sys.argv[2] if len(sys.argv) > 2 else "assets/ascii.svg"
    gray, alpha = load_matte(inp)
    gray, alpha = crop_to_subject(gray, alpha)
    glyphs, shades = to_grid(gray, alpha)
    glyphs, shades = trim_blank_edges(glyphs, shades)
    svg = build_svg(glyphs, shades)
    with open(outp, "w") as f:
        f.write(svg)
    print(f"[ascii] wrote {outp}  ({len(glyphs)} rows x {COLS} cols)")

if __name__ == "__main__":
    main()
