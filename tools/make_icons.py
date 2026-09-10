"""Generates the extension icons (a folder glyph) with the stdlib only.

    python tools/make_icons.py
"""

import os
import struct
import zlib

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extension", "icons")

BACK = (234, 165, 46)    # folder back / tab
FRONT = (250, 200, 80)   # folder front panel
EDGE = (176, 112, 12)    # outline
SHEET = (252, 252, 252)  # the file peeking out


def rounded_rect(x0, y0, x1, y1, radius):
    """Returns a hit-test function for a rounded rectangle in unit space."""
    def inside(x, y):
        if x < x0 or x > x1 or y < y0 or y > y1:
            return False
        for cx, cy in ((x0 + radius, y0 + radius), (x1 - radius, y0 + radius),
                       (x0 + radius, y1 - radius), (x1 - radius, y1 - radius)):
            if ((x < x0 + radius) == (cx == x0 + radius)) and \
               ((y < y0 + radius) == (cy == y0 + radius)):
                if (x < x0 + radius or x > x1 - radius) and (y < y0 + radius or y > y1 - radius):
                    if (x - cx) ** 2 + (y - cy) ** 2 > radius ** 2:
                        return False
        return True
    return inside


def shade(size, samples=3):
    """Supersampled render of the folder, returns RGBA rows."""
    tab = rounded_rect(0.06, 0.20, 0.48, 0.34, 0.04)
    back = rounded_rect(0.06, 0.26, 0.94, 0.82, 0.06)
    sheet = rounded_rect(0.32, 0.14, 0.72, 0.52, 0.03)
    front = rounded_rect(0.06, 0.40, 0.94, 0.84, 0.07)

    rows = []
    step = 1.0 / (size * samples)
    for py in range(size):
        row = bytearray()
        for px in range(size):
            acc = [0, 0, 0, 0]
            for sy in range(samples):
                for sx in range(samples):
                    x = (px * samples + sx + 0.5) * step
                    y = (py * samples + sy + 0.5) * step
                    color = None
                    if front(x, y):
                        color = FRONT
                    elif sheet(x, y):
                        color = SHEET
                    elif tab(x, y) or back(x, y):
                        color = BACK
                    if color is None:
                        continue
                    # thin outline near the silhouette edges
                    edge = not (front(x + step, y) and front(x - step, y) and
                                front(x, y + step) and front(x, y - step)) and front(x, y)
                    if edge:
                        color = EDGE
                    acc[0] += color[0]
                    acc[1] += color[1]
                    acc[2] += color[2]
                    acc[3] += 255
            total = samples * samples
            alpha = acc[3] // total
            if alpha == 0:
                row += bytes((0, 0, 0, 0))
            else:
                hits = acc[3] / 255.0
                row += bytes((int(acc[0] / hits), int(acc[1] / hits), int(acc[2] / hits), alpha))
        rows.append(bytes(row))
    return rows


def write_png(path, size):
    rows = shade(size)
    raw = b"".join(b"\x00" + row for row in rows)

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(png)
    print("wrote %s (%d bytes)" % (path, len(png)))


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    for size in (16, 48, 128):
        write_png(os.path.join(OUT_DIR, "icon%d.png" % size), size)
