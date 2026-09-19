"""Generate transparent BT.2100 PQ glitter; Python standard library only.

Run from any directory; writes to the sibling assets repository. RGB encodes 1000 cd/m²; alpha shapes the reflections.
cICP 9/16/0/1 signals BT.2020, PQ, RGB, full range (PNG Third Edition).
Do not strip color metadata or convert these files to ordinary sRGB PNGs.
"""
import math
from pathlib import Path
import struct
import zlib

OUT = Path(__file__).resolve().parents[2] / 'assets'
SCALE = 4
WIDTH, HEIGHT = 113 * SCALE, 79 * SCALE

def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))

def pq(nits):
    m1, m2 = 2610 / 16384, 2523 / 32
    y = (nits / 10000) ** m1
    return ((3424 / 4096 + 2413 / 128 * y) / (1 + 2392 / 128 * y)) ** m2

def inside(x, y, vertices):
    result = False
    prev = vertices[-1]
    for point in vertices:
        ax, ay = prev
        bx, by = point
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            result = not result
        prev = point
    return result

def generate(long_rays):
    length = 2 if long_rays else 1
    polygon = [(0,-7*length),(.8,-1),(5*length,0),(.8,1),(0,7*length),(-.8,1),(-5*length,0),(-.8,-1)]
    c, s = math.cos(math.radians(32)), math.sin(math.radians(32))
    white = round(pq(1000) * 65535)
    rgb = struct.pack('>HHH', white, white, white)
    raw = bytearray()
    for py in range(HEIGHT):
        raw.append(0)
        for px in range(WIDTH):
            alpha = 0
            for cx, cy, size in [(11,17,.65),(39,43,1),(71,29,.5),(97,61,.8)]:
                dx, dy = ((px+.5)/SCALE-cx)/size, ((py+.5)/SCALE-cy)/size
                x, y = c*dx+s*dy, -s*dx+c*dy
                r = math.hypot(x,y)
                a = max(0, .7*(1-r/4))
                if r <= .9 or inside(x,y,polygon):
                    a = 1
                alpha = 1-(1-alpha)*(1-a)
            raw.extend(rgb + struct.pack('>H', round(alpha*65535)))
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB',WIDTH,HEIGHT,16,6,0,0,0))
    png += chunk(b'cICP', bytes([9,16,0,1]))
    png += chunk(b'IDAT', zlib.compress(raw,9)) + chunk(b'IEND',b'')
    path = OUT / ('glitter-hdr-long.png' if long_rays else 'glitter-hdr.png')
    path.write_bytes(png)
    print(path.name, len(png), 'bytes; peak PQ code:', white)

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    generate(False)
    generate(True)
