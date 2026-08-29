#!/usr/bin/env python3
"""Render an SVG (with SMIL animations) to PNG at a given time via Chromium."""
import sys, base64, os
from playwright.sync_api import sync_playwright

def main():
    svg_path = sys.argv[1]
    out_png  = sys.argv[2]
    wait_ms  = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
    svg = open(svg_path).read()
    b64 = base64.b64encode(svg.encode()).decode()
    html = f'''<!doctype html><html><head><meta charset="utf-8">
    <style>html,body{{margin:0;padding:0;background:#0d1117}}
    img{{display:block}}</style></head>
    <body><img id="s" src="data:image/svg+xml;base64,{b64}"></body></html>'''
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--force-color-profile=srgb"])
        pg = b.new_page(device_scale_factor=2)
        pg.set_content(html)
        el = pg.query_selector("#s")
        pg.wait_for_timeout(wait_ms)          # let SMIL animation finish
        el.screenshot(path=out_png)
        b.close()
    print(f"[render] {out_png} ({os.path.getsize(out_png)} bytes) @ {wait_ms}ms")

if __name__ == "__main__":
    main()
