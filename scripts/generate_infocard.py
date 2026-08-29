#!/usr/bin/env python3
"""
generate_infocard.py
--------------------
Emits a neofetch-style info-card SVG (terminal window with a `$ neofetch`
prompt) whose lines fade + slide in one by one, then hold. GitHub-dark + green.

Edit the DATA block below to change what the card says, then re-run.

Usage: python scripts/generate_infocard.py assets/info-card.svg
"""
import sys, html

# ----------------------------------------------------------------- DATA
USER   = "rishikesh"
HOST   = "github"
TITLE  = f"{USER}@{HOST}: ~"
# (label, value)  -- keep values short so they fit the panel
ROWS = [
    ("Name",      "Rishikesh Sarangi"),
    ("Role",      "Backend & Systems Software Engineer"),
    ("Grad",      "B.Tech CSE - KIIT University '26"),
    ("Location",  "Bengaluru, India - open to relocate"),
    ("Focus",     "Databases - search - distributed systems"),
    ("Languages", "Java - Python - C++ - TypeScript - SQL"),
    ("Backend",   "FastAPI - Node.js - Express - REST - WS/SSE"),
    ("Data",      "PostgreSQL - Redis - MongoDB - SQLite"),
    ("DevOps",    "Docker - Linux - AWS - Azure - CI/CD - Git"),
    ("ML",        "TensorFlow - Keras - DeepEval - LangSmith"),
    ("Builds",    "RDBMS engine - Redis clone - Veilo search"),
    ("Creds",     "IEEE-published - LFCS - 300+ DSA solved"),
    ("Impact",    "-25% API latency on live prod pipelines"),
    ("Links",     "github/Rishicreates20 - /in/rishikeshsarangi"),
]

# ----------------------------------------------------------------- theme
BG      = "#0d1117"
PANEL   = "#0d1117"
BORDER  = "#30363d"
BAR     = "#161b22"
GREEN   = "#39d353"
GREEN2  = "#26a641"
KEY     = "#7ee787"
VAL     = "#c9d1d9"
DIM     = "#8b949e"
CURSOR  = "#39d353"
DOTS    = ["#ff5f56", "#ffbd2e", "#27c93f"]
FS      = 15
LH      = 26
LABEL_W = 96          # px reserved for the label column
PAD     = 22
BAR_H   = 34

def esc(s): return html.escape(s)

def build():
    n = len(ROWS)
    # width sized to the longest "label + value" line
    longest = max(len(l) + len(v) for l, v in ROWS)
    body_w  = int(LABEL_W + longest * FS * 0.60 + 24)
    W = max(560, body_w + 2 * PAD)
    header_lines = 2                     # prompt line + separator
    H = BAR_H + PAD + (n + header_lines + 2) * LH + PAD
    xL = PAD
    xV = PAD + LABEL_W

    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" role="img" aria-label="Profile info card">')
    o.append('<defs><style>'
             'text{font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,'
             'monospace;font-size:%dpx;dominant-baseline:middle;}' % FS +
             '.k{fill:%s;font-weight:700;} .v{fill:%s;} .d{fill:%s;}' % (KEY, VAL, DIM) +
             '</style></defs>')
    # window
    o.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" '
             f'fill="{PANEL}" stroke="{BORDER}" stroke-width="1.5"/>')
    o.append(f'<path d="M1 13 a12 12 0 0 1 12 -12 h{W-26} a12 12 0 0 1 12 12 '
             f'v{BAR_H-13} h-{W-2} z" fill="{BAR}"/>')
    for i, c in enumerate(DOTS):
        o.append(f'<circle cx="{22 + i*22}" cy="{BAR_H/2:.0f}" r="6" fill="{c}"/>')
    o.append(f'<text x="{W/2:.0f}" y="{BAR_H/2+1:.0f}" text-anchor="middle" '
             f'class="d" font-size="13">{esc(TITLE)}</text>')

    def fade(el_lines, idx, y):
        """wrap svg fragment lines with a staggered fade+slide group."""
        begin = 0.25 + idx * 0.14
        g = [f'<g opacity="0" transform="translate(0,6)">',
             f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" '
             f'dur="0.42s" fill="freeze"/>',
             f'<animateTransform attributeName="transform" type="translate" '
             f'from="0 6" to="0 0" begin="{begin:.2f}s" dur="0.42s" '
             f'calcMode="spline" keySplines="0.4 0 0.2 1" fill="freeze"/>']
        g += el_lines
        g.append('</g>')
        return "\n".join(g), begin

    y = BAR_H + PAD + LH // 2
    idx = 0
    # prompt line:  user@host ~ $ neofetch
    prompt = (f'<text x="{xL}" y="{y}" xml:space="preserve">'
              f'<tspan fill="{GREEN}" font-weight="700">{USER}@{HOST}</tspan>'
              f'<tspan class="d"> ~ </tspan>'
              f'<tspan fill="{GREEN2}" font-weight="700">$</tspan>'
              f'<tspan class="v"> neofetch</tspan></text>')
    frag, _ = fade([prompt], idx, y); o.append(frag); idx += 1; y += LH
    # separator rule
    rule = (f'<text x="{xL}" y="{y}" class="d" xml:space="preserve">'
            f'{esc("-" * (longest + 12))}</text>')
    frag, _ = fade([rule], idx, y); o.append(frag); idx += 1; y += LH

    last_begin = 0.25
    for label, value in ROWS:
        line = (f'<text x="{xL}" y="{y}"><tspan class="k">{esc(label)}</tspan></text>'
                f'<text x="{xV}" y="{y}"><tspan class="d">: </tspan>'
                f'<tspan class="v">{esc(value)}</tspan></text>')
        frag, b = fade([line], idx, y); o.append(frag); last_begin = b
        idx += 1; y += LH

    # trailing prompt + blinking cursor
    y += LH // 3
    cursor_begin = last_begin + 0.5
    o.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" '
             f'begin="{cursor_begin:.2f}s" dur="0.3s" fill="freeze"/>'
             f'<text x="{xL}" y="{y}" xml:space="preserve">'
             f'<tspan fill="{GREEN}" font-weight="700">{USER}@{HOST}</tspan>'
             f'<tspan class="d"> ~ </tspan>'
             f'<tspan fill="{GREEN2}" font-weight="700">$</tspan>'
             f'<tspan class="v"> </tspan></text>'
             f'<rect x="{xL + int((len(USER)+len(HOST)+5)*FS*0.60)}" y="{y-FS/2-2:.0f}" '
             f'width="{FS*0.6:.0f}" height="{FS}" fill="{CURSOR}">'
             f'<animate attributeName="opacity" values="1;1;0;0;1" '
             f'begin="{cursor_begin+0.3:.2f}s" dur="1.1s" repeatCount="indefinite"/>'
             f'</rect></g>')
    o.append('</svg>')
    return "\n".join(o)

def main():
    outp = sys.argv[1] if len(sys.argv) > 1 else "assets/info-card.svg"
    open(outp, "w").write(build())
    print(f"[infocard] wrote {outp}  ({len(ROWS)} rows)")

if __name__ == "__main__":
    main()
