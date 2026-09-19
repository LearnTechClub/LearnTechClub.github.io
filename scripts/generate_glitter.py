"""Generate transparent BT.2100 PQ glitter; Python standard library only.

Run from any directory; writes to the sibling assets repository. RGB encodes up to 2000 cd/m² with a pronounced power-law beam falloff; alpha shapes the reflections.
cICP 9/16/0/1 signals BT.2020, PQ, RGB, full range (PNG Third Edition).
Do not strip color metadata or convert these files to ordinary sRGB PNGs.
"""
import math
from pathlib import Path
import struct
import zlib

OUT = Path(__file__).resolve().parents[2] / 'assets'
SCALE = 8  # 904 × 632 pixels; CSS keeps the same apparent sparkle size.
PEAK_NITS = 2000
BEAM_NITS = 1000
CORE_POWER = 4.0
CORE_RADIUS = .9
FALLOFF_POWER = 2.0
THICKNESS_POWER = 2.0
BEAM_BASE_WIDTH = .065  # Fine diffraction streak, with no solid polygon edges.
WIDTH, HEIGHT = 113 * SCALE, 79 * SCALE

def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))

def pq(nits):
    m1, m2 = 2610 / 16384, 2523 / 32
    y = (nits / 10000) ** m1
    return ((3424 / 4096 + 2413 / 128 * y) / (1 + 2392 / 128 * y)) ** m2

def beam_nits(radius, tip_radius):
    # A sharp central peak joins the beam continuously at the core edge.
    # Apply the power law in physical luminance before PQ encoding.
    distance = max(0, min(1, (radius - CORE_RADIUS) / (tip_radius - CORE_RADIUS)))
    beam = BEAM_NITS * (1 + distance) ** -FALLOFF_POWER
    core = max(0, 1 - radius / CORE_RADIUS) ** CORE_POWER
    return beam + (PEAK_NITS - BEAM_NITS) * core

def beam_width(distance, tip_radius):
    # Broad luminous shoulder near the source, quickly narrowing to a hairline.
    return BEAM_BASE_WIDTH + .65 / (1 + distance / .45) ** THICKNESS_POWER

def beam_alpha(along, across, tip_radius, pixel_width):
    along, across = abs(along), abs(across)
    width = beam_width(along, tip_radius)
    # Integrate a Gaussian across the pixel so narrow rays remain smooth.
    edge = .5 * pixel_width
    coverage = width * math.sqrt(math.pi) / (2 * pixel_width) * (
        math.erf((across + edge) / width) - math.erf((across - edge) / width))
    # Soft longitudinal fade, avoiding a visible endpoint.
    return coverage * math.exp(-3 * (along / tip_radius) ** 4)

def generate(long_rays):
    length = 2 if long_rays else 1
    c, s = math.cos(math.radians(32)), math.sin(math.radians(32))
    white = round(pq(PEAK_NITS) * 65535)
    raw = bytearray()
    for py in range(HEIGHT):
        raw.append(0)
        for px in range(WIDTH):
            alpha = 0
            luminance = 0
            for cx, cy, size in [(11,17,.65),(39,43,1),(71,29,.5),(97,61,.8)]:
                dx, dy = ((px+.5)/SCALE-cx)/size, ((py+.5)/SCALE-cy)/size
                x, y = c*dx+s*dy, -s*dx+c*dy
                r = math.hypot(x,y)
                if r > 2 * 7 * length:
                    continue
                # Smooth bloom and a luminous core; no hard circular dot.
                halo = .12 * math.exp(-(r / 1.8) ** 1.3)
                pixel_width = 1 / (SCALE * size)
                core = math.exp(-(r / .6) ** 2)
                vertical = beam_alpha(y, x, 7 * length, pixel_width)
                horizontal = beam_alpha(x, y, 5 * length, pixel_width)
                # Faint short diagonal scattering around the central bloom.
                diagonal = .035 * math.exp(-(r / 1.5) ** 2) * (
                    math.exp(-((x-y) / .28) ** 2) + math.exp(-((x+y) / .28) ** 2))
                a = 1 - (1-core) * (1-halo) * (1-vertical) * (1-horizontal) * (1-diagonal)
                if a > 0:
                    tip_radius = (7 if abs(y) >= abs(x) else 5) * length
                    nits = beam_nits(r, tip_radius)
                    luminance = nits * a + luminance * (1 - a)
                    alpha = a + alpha * (1 - a)
            code = round(pq(luminance / alpha) * 65535) if alpha else 0
            raw.extend(struct.pack('>HHHH', code, code, code, round(alpha*65535)))
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
