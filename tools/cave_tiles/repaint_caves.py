"""Repaint the cave interiors (fr_ic*, fr_sc*, fr_ep1-3) from cave_tileset.png.

Each map is rebuilt from its own collision grid in vellmoor.html (FRMAPS), so walls,
floors, ladders, holes, exits and ledges line up with how the map actually plays.

    python3 tools/cave_tiles/repaint_caves.py            # from the repo root
"""
import json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MAPS = os.path.join(ROOT, 'sprites', 'overworld', 'maps')
SHEET = Image.open(os.path.join(os.path.dirname(__file__), 'cave_tileset.png')).convert('RGBA')
T = 16


def tile(x, y, h=1):
    return SHEET.crop((x * T, y * T, x * T + T, y * T + T * h))


def recolor(src, ref):
    """Map src's shades onto ref's palette by brightness rank (keeps alpha)."""
    s = np.array(src).astype(float)
    r = np.array(ref).reshape(-1, 4)
    r = r[r[:, 3] > 128][:, :3]
    lum = lambda a: a[..., 0] * .3 + a[..., 1] * .59 + a[..., 2] * .11
    order = r[np.argsort(lum(r))]
    sl = lum(s[..., :3])
    vis = s[..., 3] > 128
    lo, hi = sl[vis].min(), sl[vis].max()
    idx = ((sl - lo) / max(1, hi - lo) * (len(order) - 1)).clip(0, len(order) - 1).astype(int)
    out = s.copy()
    out[..., :3] = order[idx]
    return Image.fromarray(out.astype(np.uint8))


def with_mouth(face, mouth_src):
    """Cut the black opening of mouth_src into a wall-face tile."""
    m = np.array(mouth_src)
    f = np.array(face).copy()
    dark = (m[..., :3].sum(2) < 60) & (m[..., 3] > 128)
    f[dark] = m[dark]
    return Image.fromarray(f)


ICE_MOUTH = tile(3, 5)


def shadowed(t):
    """Floor tile with the soft shadow a wall casts onto the row below it."""
    a = np.array(t).astype(float)
    for i, k in enumerate((.55, .7, .82, .92)):
        a[i, :, :3] *= k
    return Image.fromarray(a.astype(np.uint8))

STYLES = {
    # Ember Peak tunnels: red-brown rock, sandy floor
    'brown': dict(
        floor=[tile(12, 1)] * 10 + [tile(11, 3)],
        face=[tile(8, 1), tile(10, 1), tile(12, 2), tile(8, 2), tile(10, 2)],
        fill=[tile(9, 0), tile(10, 0), tile(8, 5), tile(9, 5), tile(14, 5), tile(15, 5)],
        boulder=[tile(10, 7), tile(11, 7)],
        ladder=tile(9, 8, 2), hole=tile(12, 8),
        mouth=tile(9, 1),
        edge=(74, 40, 44), void=(18, 12, 14),
    ),
    # Ironmarch Caverns: grey-green cobble stone
    'teal': dict(
        floor=[tile(9, 13)],
        face=[tile(9, 14), tile(10, 14)],
        fill=[tile(14, 13), tile(15, 13)],
        boulder=[recolor(tile(10, 7), tile(14, 13)), recolor(tile(0, 2), tile(14, 13))],
        ladder=tile(9, 8, 2), hole=tile(12, 8),
        mouth=None,
        edge=(38, 52, 54), void=(12, 16, 18),
    ),
    # Saltmere Sea Cave: icy blue rock, frosted floor
    'ice': dict(
        floor=[tile(1, 6)],
        face=[tile(0, 4), tile(1, 4), tile(2, 4), tile(4, 4), tile(2, 5), tile(4, 5)],
        fill=[tile(2, 6), tile(6, 4)],
        boulder=[tile(0, 2), tile(1, 2), tile(3, 2)],
        ladder=tile(3, 6, 2), hole=tile(1, 7),
        mouth=ICE_MOUTH,
        edge=(56, 84, 140), void=(10, 14, 26),
    ),
}

CAVES = {  # map -> (style, height; higher number = further up)
    'ic1': ('teal', 0), 'ic2': ('teal', -1), 'ic3': ('teal', -2),
    'sc1': ('ice', 0), 'sc2': ('ice', -1),
    'ep1': ('brown', 1), 'ep2': ('brown', 2), 'ep3': ('brown', 3),
}


def pick(lst, x, y, salt=0):
    h = (x * 73856093) ^ (y * 19349663) ^ (salt * 83492791)
    return lst[(h & 0x7fffffff) % len(lst)]


def load_maps():
    s = open(os.path.join(ROOT, 'vellmoor.html'), encoding='utf-8').read()
    i = s.index('const FRMAPS=') + len('const FRMAPS=')
    d, _ = json.JSONDecoder().raw_decode(s[i:])
    return d


def paint(key, M):
    style, height = CAVES[key]
    S = STYLES[style]
    w, h = M['w'], M['h']
    coll = M['coll']
    old = np.array(Image.open(os.path.join(MAPS, f'fr_{key}_lower.png')).convert('RGB')).astype(int)
    void = [[coll[y][x] == '1' and old[y * T:y * T + T, x * T:x * T + T].mean() < 30 for x in range(w)] for y in range(h)]
    ledge = {tuple(map(int, k.split(','))): v for k, v in (M.get('ledge') or {}).items()}
    warp = {(x, y): to for x, y, to, _ in M['warps']}

    def walk(x, y):
        return 0 <= x < w and 0 <= y < h and (coll[y][x] == '0' or (x, y) in ledge)

    def solid(x, y):
        return 0 <= x < w and 0 <= y < h and coll[y][x] == '1' and not void[y][x] and (x, y) not in ledge

    face_mouth = S['mouth'] if S['mouth'] is not None else with_mouth(S['face'][0], ICE_MOUTH)
    img = Image.new('RGBA', (w * T, h * T), S['void'] + (255,))

    def put(t, x, y):
        img.alpha_composite(t, (x * T, y * T))

    def outline(x, y, sides):
        px = img.load()
        for sd in sides:
            for i in range(T):
                X, Y = {'l': (x * T, y * T + i), 'r': (x * T + T - 1, y * T + i),
                        't': (x * T + i, y * T), 'b': (x * T + i, y * T + T - 1)}[sd]
                px[X, Y] = S['edge'] + (255,)

    for y in range(h):
        for x in range(w):
            if void[y][x]:
                continue
            if walk(x, y):
                above_wall = solid(x, y - 1)
                put(shadowed(pick(S['floor'], x, y)) if above_wall else pick(S['floor'], x, y), x, y)
                continue
            # blocked rock
            n = [walk(x, y - 1), walk(x, y + 1), walk(x - 1, y), walk(x + 1, y)]
            if all(n):  # a lone rock in open floor
                put(pick(S['floor'], x, y), x, y)
                put(pick(S['boulder'], x, y), x, y)
                continue
            if walk(x, y + 1):
                put(pick(S['floor'], x, y), x, y)   # under any transparent pixels
                put(pick(S['face'], x, y), x, y)
                outline(x, y, 'b')
            else:
                put(pick(S['fill'], x, y), x, y)
            sides = [s for s, ok in zip('tlr', (walk(x, y - 1), walk(x - 1, y), walk(x + 1, y))) if ok]
            outline(x, y, sides)

    # ledges: a rock lip you hop down off
    for (x, y), d in ledge.items():
        put(pick(S['floor'], x, y), x, y)
        lip = pick(S['face'], x, y).crop((0, 9, T, T))
        img.alpha_composite(lip, (x * T, y * T + 9))
        outline(x, y, 'b')

    # ladders, holes and exits
    for (x, y), to in warp.items():
        if to == 'OUT' or to not in CAVES:
            for dx, dy in ((0, 1), (0, -1), (-1, 0), (1, 0)):
                if solid(x + dx, y + dy):
                    put(pick(S['floor'], x, y), x + dx, y + dy)
                    put(face_mouth, x + dx, y + dy)
                    break
            continue
        if CAVES[to][1] > height:  # going up: ladder against the wall above
            put(S['ladder'].crop((0, T, T, 2 * T)), x, y)
            if y > 0 and not void[y - 1][x]:
                put(S['ladder'].crop((0, 0, T, T)), x, y - 1)
        else:                      # going down: hole with a ladder in it
            put(S['hole'], x, y)

    img.save(os.path.join(MAPS, f'fr_{key}_lower.png'))
    Image.new('RGBA', img.size, (0, 0, 0, 0)).save(os.path.join(MAPS, f'fr_{key}_upper.png'))
    return img


if __name__ == '__main__':
    d = load_maps()
    for k in (sys.argv[1:] or CAVES):
        paint(k, d[k])
        print('painted', k, CAVES[k][0])
