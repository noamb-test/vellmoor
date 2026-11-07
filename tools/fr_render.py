"""Render a FireRed (pret/pokefirered) map layout to Vellmoor lower/upper PNGs.

    from fr_render import render
    lower, upper, coll, behav = render(PFR, 'CeladonCity_GameCorner', 'building', 'game_corner')

PFR is a checkout of pret/pokefirered with data/layouts and data/tilesets present.
"""
import os, struct
import numpy as np
from PIL import Image

NUM_PRIMARY = 640  # tiles and metatiles in a FireRed primary tileset


def _pal(path):
    lines = open(path).read().split()
    n = int(lines[2])
    v = list(map(int, lines[3:3 + n * 3]))
    return [tuple(v[i * 3:i * 3 + 3]) for i in range(n)]


class Tileset:
    def __init__(self, root, name, secondary, gfx=None):
        base = os.path.join(root, 'data', 'tilesets', 'secondary' if secondary else 'primary', name)
        g = os.path.join(root, 'data', 'tilesets', 'secondary' if secondary else 'primary', gfx or name)
        im = Image.open(os.path.join(g, 'tiles.png'))
        a = np.array(im)
        if im.mode != 'P':
            raise ValueError('expected an indexed tiles.png')
        a = a & 15
        h, w = a.shape
        self.tiles = [a[y:y + 8, x:x + 8] for y in range(0, h, 8) for x in range(0, w, 8)]
        self.pals = [_pal(os.path.join(g, 'palettes', f'{i:02d}.pal')) for i in range(16)]
        mt = open(os.path.join(base, 'metatiles.bin'), 'rb').read()
        self.metatiles = [struct.unpack_from('<8H', mt, i) for i in range(0, len(mt), 16)]
        at = open(os.path.join(base, 'metatile_attributes.bin'), 'rb').read()
        self.attrs = [struct.unpack_from('<I', at, i)[0] for i in range(0, len(at), 4)]


def render(root, layout, primary, secondary, secondary_gfx=None):
    P = Tileset(root, primary, False)
    S = Tileset(root, secondary, True, secondary_gfx)
    import json
    L = json.load(open(os.path.join(root, 'data', 'layouts', 'layouts.json')))['layouts']
    info = next(l for l in L if l.get('name') == layout + '_Layout')
    w, h = info['width'], info['height']
    raw = open(os.path.join(root, info['blockdata_filepath']), 'rb').read()
    blocks = struct.unpack('<%dH' % (w * h), raw)
    pals = P.pals[:7] + S.pals[7:13] + P.pals[13:16]

    def tile(idx):
        return P.tiles[idx] if idx < NUM_PRIMARY else S.tiles[idx - NUM_PRIMARY]

    def meta(mid):
        return (P.metatiles[mid], P.attrs[mid]) if mid < NUM_PRIMARY else (S.metatiles[mid - NUM_PRIMARY], S.attrs[mid - NUM_PRIMARY])

    lower = np.zeros((h * 16, w * 16, 4), np.uint8)
    upper = np.zeros((h * 16, w * 16, 4), np.uint8)
    coll, behav = [], []

    def draw(dst, ent, X, Y, opaque):
        idx, hf, vf, pal = ent & 0x3FF, ent >> 10 & 1, ent >> 11 & 1, ent >> 12 & 15
        t = tile(idx)
        if hf: t = t[:, ::-1]
        if vf: t = t[::-1]
        colors = np.array(pals[pal] + [(0, 0, 0)] * 16)[:16]
        rgb = colors[t]
        mask = (t != 0) | opaque
        reg = dst[Y:Y + 8, X:X + 8]
        reg[mask, :3] = rgb[mask]
        reg[mask, 3] = 255

    for y in range(h):
        crow, brow = '', []
        for x in range(w):
            b = blocks[y * w + x]
            mid, col = b & 0x3FF, b >> 10 & 3
            crow += '1' if col else '0'
            ents, attr = meta(mid)
            brow.append(attr & 0x1FF)
            layer = attr >> 29 & 3  # 0 normal, 1 covered, 2 split
            for i in range(8):
                X, Y = x * 16 + (i & 1) * 8, y * 16 + (i >> 1 & 1) * 8
                if i < 4:
                    draw(lower, ents[i], X, Y, True)
                elif layer == 1:
                    draw(lower, ents[i], X, Y, False)
                else:
                    draw(upper, ents[i], X, Y, False)
        coll.append(crow)
        behav.append(brow)
    return Image.fromarray(lower), Image.fromarray(upper), coll, behav
