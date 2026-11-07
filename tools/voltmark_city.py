"""Voltmark, rebuilt as a New York-style city.

Writes  <out>/vm_layout.json  (map for the map editor: grid, buildings, signs, NPCs, exits)
        <out>/vm_ground.png   (hand-painted streets, sidewalks, park, river, towers, details)
        <out>/vm_extra.json   (extra blocked tiles for things painted on the ground)

    python3 tools/voltmark_city.py <out_dir>
"""
import json, os, random, sys
from PIL import Image, ImageDraw

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
W, H, T = 56, 48, 16
rng = random.Random(12)

# ------------------------------------------------------------------ layout
g = [['S'] * W for _ in range(H)]          # S sidewalk, R road, G grass, P park path, K park wall, W water, T tree


def fill(x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H, y1 + 1)):
        for x in range(max(0, x0), min(W, x1 + 1)):
            g[y][x] = c


ROADS = []
def road(x0, y0, x1, y1, axis):
    fill(x0, y0, x1, y1, 'R'); ROADS.append((x0, y0, x1, y1, axis))

road(0, 16, W - 1, 19, 'h')        # Broadway (exits at both ends, rows 17-19)
road(24, 20, 25, 42, 'v')          # Fifth Avenue
road(26, 30, W - 1, 31, 'h')       # 42nd Street
road(0, 43, W - 1, 44, 'h')        # Riverside Drive
fill(0, 46, W - 1, H - 1, 'W')     # the river

# Central Park: walled, with gates, paths, trees and a reservoir
PX0, PY0, PX1, PY1 = 0, 22, 22, 41
fill(PX0, PY0, PX1, PY1, 'G')
for x in range(PX0, PX1 + 1): g[PY0][x] = 'K'; g[PY1][x] = 'K'
for y in range(PY0, PY1 + 1): g[y][PX1] = 'K'; g[y][PX0] = 'K'
for (x, y) in [(8, PY0), (9, PY0), (16, PY0), (17, PY0), (PX1, 26), (PX1, 27), (PX1, 36), (PX1, 37), (10, PY1), (11, PY1)]:
    g[y][x] = 'P'
fill(4, 27, 18, 27, 'P'); fill(4, 36, 18, 36, 'P'); fill(4, 27, 4, 36, 'P'); fill(18, 27, 18, 36, 'P')   # loop
fill(8, 23, 9, 26, 'P'); fill(16, 23, 17, 26, 'P'); fill(19, 26, 21, 27, 'P'); fill(19, 36, 21, 37, 'P'); fill(10, 37, 11, 40, 'P')
fill(7, 29, 15, 34, 'W')            # reservoir
fill(6, 28, 16, 28, 'P'); fill(6, 35, 16, 35, 'P'); fill(6, 28, 6, 35, 'P'); fill(16, 28, 16, 35, 'P')
def trees(x, y):
    if all(g[y + b][x + a] == 'G' for a in (0, 1) for b in (0, 1)):
        for a in (0, 1):
            for b in (0, 1): g[y + b][x + a] = 'T'
for x in range(1, 21, 2):
    trees(x, 23); trees(x, 39)
for y in range(25, 38, 2):
    trees(1, y); trees(19, y) if y not in (26, 36) else None
for (x, y) in [(12, 23), (2, 25), (2, 33), (13, 24), (20, 31), (19, 29), (19, 33)]:
    trees(x, y)

# -------------------------------------------------------------- buildings
B = []
def bld(kit, x, y, name, goes=None):
    d = {'kit': kit, 'karea': 5, 'x': x, 'y': y, 'name': name, 'goes': goes or {'type': 'keep'}}
    B.append(d)

bld('radio_tower', 9, 13, 'tower')
bld('dept_store', 21, 13, 'dept')
bld('radio_lav', 30, 13, 'empire', {'type': 'locked', 'text': 'VOLTMARK TOWER\nThe observation deck is closed for repairs after the last thunderstorm.'})
bld('game_corner', 38, 13, 'gamecorner')
bld('gym_goldenrod', 51, 13, 'gym')
bld('center', 32, 27, 'center')
bld('mart', 41, 27, 'mart')
bld('house_goldenrod', 50, 27, 'house1')
bld('dept_celadon', 30, 41, 'trade', {'type': 'locked', 'text': 'VOLTMARK TRADE CENTER\nOffices only. A guard waves you away politely.'})
bld('train', 38, 41, 'station')
bld('theater', 50, 41, 'theater', {'type': 'locked', 'text': 'THE VOLTMARK THEATER\nTonight: “The Phantom of the Lavender Tower.”\nSOLD OUT'})

# ---------------------------------------------------------------- people
SIGNS = [
    {'x': 3, 'y': 15, 'model': 'sign', 'lines': ['VOLTMARK', 'The city that never powers down. Electric-type Gym on Broadway.']},
    {'x': 27, 'y': 21, 'model': 'sign', 'lines': ['@builtin:notice board']},
    {'x': 54, 'y': 15, 'model': 'gymsign', 'lines': ['@builtin:gym sign']},
    {'x': 12, 'y': 37, 'model': 'sign', 'lines': ['VOLT FOUNTAIN', 'The lights in the water are powered by the Electric Gym.']},
    {'x': 7, 'y': 21, 'model': 'sign', 'lines': ['CENTRAL PARK', 'Open dawn to dusk. Please keep Pokémon off the flower beds.']},
    {'x': 28, 'y': 29, 'model': 'sign', 'lines': ['42nd STREET', 'Pokémon Center ← · Poké Mart → · Grand Station ↓']},
]
NPCS = [
    {'builtin': 'keep', 'ox': 39, 'oy': 15, 'x': 49, 'y': 15, 'dir': 'left'},
    {'builtin': 'keep', 'ox': 9, 'oy': 20, 'x': 9, 'y': 30, 'dir': 'right'},   # the Pokémon by the water
    {'builtin': 'keep', 'ox': 35, 'oy': 21, 'x': 2, 'y': 20, 'dir': 'up'},     # points to the west road
    {'builtin': 'keep', 'ox': 28, 'oy': 7, 'x': 30, 'y': 15, 'dir': 'down'},
    {'builtin': 'keep', 'ox': 32, 'oy': 34, 'x': 13, 'y': 27, 'dir': 'down'},
    {'builtin': 'keep', 'ox': 24, 'oy': 21, 'x': 23, 'y': 33, 'dir': 'right'},
    {'builtin': 'keep', 'ox': 33, 'oy': 10, 'x': 36, 'y': 14, 'dir': 'down'},
    {'builtin': 'keep', 'ox': 35, 'oy': 18, 'x': 42, 'y': 21, 'dir': 'down'},
    {'builtin': 'a12_i12', 'x': 3, 'y': 38, 'dir': 'down'},
    {'kind': 'person', 'sheet': 'guitarist', 'x': 17, 'y': 33, 'dir': 'left', 'wander': False, 'say': ['When the Gym powers up, the whole fountain sparkles. Best free show in Vellmoor!']},
    {'kind': 'person', 'sheet': 'gentleman', 'x': 36, 'y': 42, 'dir': 'up', 'wander': False, 'say': ['Grand Station. The trains still run on Electric Pokémon power. Clean and quick.']},
    {'kind': 'person', 'sheet': 'lady', 'x': 47, 'y': 42, 'dir': 'left', 'wander': False, 'say': ['I’ve waited three hours for theater tickets. Three hours!']},
    {'kind': 'person', 'sheet': 'pokefan_m', 'x': 20, 'y': 15, 'dir': 'right', 'wander': True, 'say': ['Everybody here walks fast. Try to keep up!']},
    {'kind': 'person', 'sheet': 'school_kid_f', 'x': 40, 'y': 20, 'dir': 'up', 'wander': False, 'say': ['Look at all the billboards! I could stand here all day.']},
    {'kind': 'person', 'sheet': 'fisherman', 'x': 18, 'y': 45, 'dir': 'down', 'wander': False, 'say': ['You’d be amazed what bites in the river. Mostly old boots, though.']},
    {'kind': 'person', 'sheet': 'twin', 'x': 7, 'y': 37, 'dir': 'up', 'wander': True, 'say': ['I fed the Psyduck in the pond! Don’t tell anyone.']},
    {'kind': 'person', 'sheet': 'policeman', 'x': 26, 'y': 15, 'dir': 'down', 'wander': False, 'say': ['Look both ways! The taxis here don’t slow down for anybody.']},
]

# ------------------------------------------------------------- painting
img = Image.new('RGBA', (W * T, H * T), (0, 0, 0, 255))
px = img.load()
d = ImageDraw.Draw(img)
EXTRA = set()                    # tiles blocked by painted things


def noise(x0, y0, w, h, base, amp, density=.35):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            v = rng.random()
            c = base
            if v < density * .5: c = tuple(max(0, k - amp) for k in base)
            elif v < density: c = tuple(min(255, k + amp // 2) for k in base)
            px[x, y] = c + (255,)


ASPH = (78, 82, 90); SIDE = (198, 194, 186); SIDE_J = (170, 166, 158); CURB = (226, 224, 218); CURB_SH = (120, 118, 116)
GRASS = (104, 176, 88); PATH = (206, 186, 140); WALL = (150, 140, 124); WALL_TOP = (186, 176, 158)
YEL = (240, 200, 60); WHT = (236, 236, 232)
at = lambda x, y: g[y][x] if 0 <= x < W and 0 <= y < H else 'S'

for y in range(H):
    for x in range(W):
        c, X, Y = g[y][x], x * T, y * T
        if c == 'R':
            noise(X, Y, T, T, ASPH, 10, .25)
        elif c == 'S':
            noise(X, Y, T, T, SIDE, 8, .3)
            d.line([X, Y + T - 1, X + T - 1, Y + T - 1], fill=SIDE_J); d.line([X + T - 1, Y, X + T - 1, Y + T - 1], fill=SIDE_J)
        elif c in 'GT':
            noise(X, Y, T, T, GRASS, 16, .3)
            for _ in range(2):
                a, b = rng.randrange(1, 14), rng.randrange(2, 14)
                px[X + a, Y + b] = (74, 140, 64, 255); px[X + a + 1, Y + b - 1] = (74, 140, 64, 255)
        elif c == 'P':
            noise(X, Y, T, T, PATH, 14, .4)
        elif c == 'K':
            noise(X, Y, T, T, WALL, 12, .35)
            d.rectangle([X, Y, X + T - 1, Y + 3], fill=WALL_TOP)
            for k in range(0, T, 8): d.line([X + k, Y + 4, X + k, Y + T - 1], fill=(120, 112, 100))
            d.line([X, Y + 9, X + T - 1, Y + 9], fill=(120, 112, 100))
        elif c == 'W':
            noise(X, Y, T, T, (58, 112, 176), 12, .25)
            if (x * 7 + y * 3) % 5 == 0: d.line([X + 3, Y + 6, X + 9, Y + 6], fill=(150, 196, 236))
            if (x * 5 + y * 11) % 7 == 0: d.line([X + 8, Y + 12, X + 13, Y + 12], fill=(150, 196, 236))

# curbs where sidewalk meets road, and grass edges next to paths
for y in range(H):
    for x in range(W):
        X, Y = x * T, y * T
        if g[y][x] == 'S':
            if at(x, y + 1) == 'R': d.rectangle([X, Y + 13, X + 15, Y + 14], fill=CURB); d.line([X, Y + 15, X + 15, Y + 15], fill=CURB_SH)
            if at(x, y - 1) == 'R': d.rectangle([X, Y, X + 15, Y + 1], fill=CURB); d.line([X, Y + 2, X + 15, Y + 2], fill=(176, 172, 164))
            if at(x + 1, y) == 'R': d.rectangle([X + 13, Y, X + 14, Y + 15], fill=CURB); d.line([X + 15, Y, X + 15, Y + 15], fill=CURB_SH)
            if at(x - 1, y) == 'R': d.rectangle([X, Y, X + 1, Y + 15], fill=CURB)
        if g[y][x] == 'W' and at(x, y - 1) not in 'W':   # stone rim on water
            d.rectangle([X, Y, X + 15, Y + 3], fill=(176, 170, 160)); d.line([X, Y + 4, X + 15, Y + 4], fill=(40, 70, 110))
        if g[y][x] == 'W' and at(x, y + 1) not in 'W' and y < H - 1:
            d.rectangle([X, Y + 13, X + 15, Y + 15], fill=(176, 170, 160))
        if g[y][x] == 'W' and at(x - 1, y) not in 'W' and x > 0: d.rectangle([X, Y, X + 2, Y + 15], fill=(176, 170, 160))
        if g[y][x] == 'W' and at(x + 1, y) not in 'W' and x < W - 1: d.rectangle([X + 13, Y, X + 15, Y + 15], fill=(176, 170, 160))

# lane markings (skip intersections)
def is_cross(x, y):
    h = any(a <= x <= c and b <= y <= e for a, b, c, e, ax in ROADS if ax == 'h')
    v = any(a <= x <= c and b <= y <= e for a, b, c, e, ax in ROADS if ax == 'v')
    return h and v or (at(x, y - 1) == 'R' and at(x, y + 1) == 'R' and at(x - 1, y) == 'R' and at(x + 1, y) == 'R' and False)

def in_inter(x, y):
    # a road tile touched by both a horizontal and a vertical road
    hh = any(a <= x <= c and b <= y <= e for a, b, c, e, ax in ROADS if ax == 'h')
    vv = any(a <= x <= c and b - 1 <= y <= e + 1 for a, b, c, e, ax in ROADS if ax == 'v')
    return hh and vv

for (x0, y0, x1, y1, ax) in ROADS:
    if ax == 'h':
        mid = (y0 + y1 + 1) / 2 * T
        for x in range(x0, x1 + 1):
            if in_inter(x, y0): continue
            X = x * T
            d.line([X, mid - 2, X + 15, mid - 2], fill=YEL); d.line([X, mid + 1, X + 15, mid + 1], fill=YEL)
            if y1 - y0 >= 3:
                for yy in (y0 * T + T, y1 * T):
                    if x % 2 == 0: d.line([X + 2, yy, X + 11, yy], fill=WHT)
    else:
        mid = (x0 + x1 + 1) / 2 * T
        for y in range(y0, y1 + 1):
            if any(a <= x0 <= c and b <= y <= e for a, b, c, e, a2 in ROADS if a2 == 'h'): continue
            Y = y * T
            d.line([mid - 2, Y, mid - 2, Y + 15], fill=YEL); d.line([mid + 1, Y, mid + 1, Y + 15], fill=YEL)

def zebra_h(x, y0, y1):          # stripes for crossing a horizontal road (walking up/down)
    for y in range(y0, y1 + 1):
        for k in range(0, T, 4): d.rectangle([x * T + 1, y * T + k, x * T + 14, y * T + k + 1], fill=WHT)
def zebra_v(y, x0, x1):          # stripes for crossing a vertical road (walking left/right)
    for x in range(x0, x1 + 1):
        for k in range(0, T, 4): d.rectangle([x * T + k, y * T + 1, x * T + k + 1, y * T + 14], fill=WHT)

for x in (22, 23, 26, 27): zebra_h(x, 16, 19)          # across Broadway at Fifth
for x in (26, 27): zebra_h(x, 43, 44)
for x in (22, 23): zebra_h(x, 43, 44)
for y in (21, 29, 32, 42): zebra_v(y, 24, 25)            # across Fifth
for x in (45, 46): zebra_h(x, 30, 31)                    # mid-block on 42nd
for x in (8, 9, 16, 17): zebra_h(x, 16, 19)              # to the park gates
for x in (10, 11): zebra_h(x, 43, 44)

# promenade railing above the river
for x in range(W):
    X, Y = x * T, 45 * T
    d.rectangle([X, Y + 12, X + 15, Y + 13], fill=(60, 64, 72)); d.line([X, Y + 8, X + 15, Y + 8], fill=(60, 64, 72))
    for k in (2, 10): d.line([X + k, Y + 8, X + k, Y + 13], fill=(60, 64, 72))

# ------------------------------------------------------------- towers
def tower(x0, y0, x1, y1, kind, roof=True, sign=None):
    """A painted building front covering pixels x0..x1, y0..y1."""
    base = {'brick': (156, 82, 66), 'stone': (196, 182, 150), 'glass': (86, 124, 168), 'grey': (134, 138, 150), 'cream': (214, 200, 168)}[kind]
    dark = tuple(int(c * .7) for c in base); lite = tuple(min(255, int(c * 1.18)) for c in base)
    d.rectangle([x0, y0, x1, y1], fill=base)
    d.rectangle([x0, y0, x1, y1], outline=(40, 40, 48))
    if roof:
        d.rectangle([x0, y0, x1, y0 + 3], fill=lite); d.line([x0, y0 + 4, x1, y0 + 4], fill=dark)
    top = y0 + (7 if roof else 2)
    shop = y1 - 15
    ww, wh, sx, sy = (5, 6, 8, 10) if kind != 'glass' else (6, 8, 8, 10)
    for wy in range(top, shop - wh, sy):
        for wx in range(x0 + 3, x1 - ww - 1, sx):
            lit = rng.random() < .28
            col = (255, 226, 120) if lit else ((150, 196, 230) if kind == 'glass' else (44, 52, 74))
            d.rectangle([wx, wy, wx + ww - 1, wy + wh - 1], fill=col)
            if not lit and kind != 'glass': d.line([wx, wy, wx + ww - 1, wy], fill=(90, 104, 140))
            d.line([wx, wy + wh, wx + ww - 1, wy + wh], fill=dark)
    # street-level shopfront with an awning
    d.rectangle([x0 + 1, shop, x1 - 1, y1 - 1], fill=(52, 58, 70))
    aw = rng.choice([(196, 52, 52), (40, 120, 76), (40, 84, 160), (220, 150, 40)])
    for k in range(x0 + 1, x1 - 1, 4):
        d.rectangle([k, shop - 3, min(k + 1, x1 - 1), shop + 1], fill=aw)
        if k + 2 <= x1 - 1: d.rectangle([k + 2, shop - 3, min(k + 3, x1 - 1), shop + 1], fill=(240, 236, 228))
    for k in range(x0 + 4, x1 - 6, 10): d.rectangle([k, shop + 5, k + 5, y1 - 3], fill=(120, 170, 200))
    if sign: billboard(*sign)


def billboard(x0, y0, x1, y1, text, bg, fg):
    d.rectangle([x0 - 1, y0 - 1, x1 + 1, y1 + 1], fill=(30, 30, 36))
    d.rectangle([x0, y0, x1, y1], fill=bg)
    for k in range(x0, x1, 3): px[k, y0] = (255, 255, 200, 255); px[k, y1] = (255, 255, 200, 255)
    tw = d.textlength(text)
    d.text(((x0 + x1 - tw) / 2, (y0 + y1) / 2 - 6), text, fill=fg)


def water_tower(x, y):
    d.rectangle([x, y + 10, x + 1, y + 15], fill=(60, 50, 44)); d.rectangle([x + 9, y + 10, x + 10, y + 15], fill=(60, 50, 44))
    d.rectangle([x - 1, y + 2, x + 11, y + 10], fill=(146, 104, 70)); d.polygon([(x - 2, y + 2), (x + 5, y - 3), (x + 12, y + 2)], fill=(96, 70, 50))
    for k in (4, 7): d.line([x - 1, y + k, x + 11, y + k], fill=(110, 78, 52))

FILL = []   # pixel rects that are solid (turned into blocked tiles)
def solid(x0, y0, x1, y1): FILL.append((x0, y0, x1, y1))

# north side of Broadway (doors on row 13): towers between the landmarks run to the top edge
tower(0, 0, 95, 223, 'brick', roof=False); solid(0, 0, 95, 223)
tower(220, 0, 304, 223, 'stone', roof=False); solid(220, 0, 304, 223)
tower(398, 0, 430, 223, 'glass', roof=False); solid(398, 0, 430, 223)
tower(676, 0, 772, 223, 'grey', roof=False, sign=(684, 120, 764, 150, 'VOLT COLA', (210, 40, 40), (255, 255, 255))); solid(676, 0, 772, 223)
billboard(684, 40, 764, 70, 'GAME CORNER', (40, 40, 140), (255, 232, 90))
billboard(684, 80, 764, 108, 'SKYWAY AIR', (20, 140, 120), (255, 255, 255))
tower(884, 0, 895, 223, 'brick', roof=False); solid(884, 0, 895, 223)
# block between Broadway and 42nd (doors on row 27)
tower(416, 360, 474, 447, 'brick'); water_tower(440, 364); solid(416, 352, 474, 447)
tower(572, 352, 634, 447, 'stone'); solid(572, 352, 634, 447)
tower(728, 360, 784, 447, 'cream'); water_tower(752, 364); solid(728, 352, 784, 447)
tower(854, 352, 895, 447, 'brick'); solid(854, 352, 895, 447)
# block south of 42nd (doors on row 41)
tower(724, 520, 750, 671, 'grey'); solid(724, 512, 750, 671)
tower(876, 520, 895, 671, 'stone'); solid(876, 512, 895, 671)
tower(416, 520, 424, 671, 'brick'); solid(416, 512, 424, 671)

# ---------------------------------------------------------- street details
def taxi(tx, ty, vertical=False):
    X, Y = tx * T, ty * T
    if not vertical:
        d.rounded_rectangle([X + 1, Y + 3, X + 30, Y + 13], 3, fill=(246, 196, 32), outline=(60, 44, 10))
        d.rectangle([X + 9, Y + 4, X + 22, Y + 11], fill=(54, 62, 80)); d.rectangle([X + 14, Y + 4, X + 17, Y + 11], fill=(246, 196, 32))
        d.rectangle([X + 13, Y + 1, X + 18, Y + 3], fill=(255, 250, 220)); d.line([X + 2, Y + 8, X + 29, Y + 8], fill=(30, 30, 30))
        for k in (5, 24): d.rectangle([X + k, Y + 13, X + k + 3, Y + 15], fill=(24, 24, 28))
        EXTRA.update({(tx, ty), (tx + 1, ty)})
    else:
        d.rounded_rectangle([X + 3, Y + 1, X + 13, Y + 30], 3, fill=(246, 196, 32), outline=(60, 44, 10))
        d.rectangle([X + 4, Y + 9, X + 11, Y + 22], fill=(54, 62, 80)); d.rectangle([X + 4, Y + 14, X + 11, Y + 17], fill=(246, 196, 32))
        d.line([X + 8, Y + 2, X + 8, Y + 29], fill=(30, 30, 30))
        EXTRA.update({(tx, ty), (tx, ty + 1)})

for (x, y) in [(4, 16), (13, 19), (33, 16), (44, 19), (49, 16), (36, 30), (50, 31), (3, 43), (40, 44)]:
    taxi(x, y)
for (x, y) in [(24, 23), (25, 36)]:
    taxi(x, y, True)

def hydrant(tx, ty):
    X, Y = tx * T, ty * T
    d.rectangle([X + 5, Y + 5, X + 10, Y + 13], fill=(206, 40, 40)); d.rectangle([X + 4, Y + 7, X + 11, Y + 8], fill=(160, 24, 24))
    d.ellipse([X + 5, Y + 2, X + 10, Y + 7], fill=(226, 60, 60)); EXTRA.add((tx, ty))
for (x, y) in [(15, 14), (35, 20), (46, 29), (28, 42)]:
    hydrant(x, y)

def bench(tx, ty):
    X, Y = tx * T, ty * T
    d.rectangle([X + 1, Y + 6, X + 30, Y + 9], fill=(130, 84, 48)); d.rectangle([X + 1, Y + 3, X + 30, Y + 4], fill=(110, 70, 40))
    for k in (3, 27): d.rectangle([X + k, Y + 10, X + k + 1, Y + 14], fill=(50, 50, 56))
    EXTRA.update({(tx, ty), (tx + 1, ty)})
for (x, y) in [(10, 26), (12, 37), (2, 37)]:
    bench(x, y)

def trash(tx, ty):
    X, Y = tx * T, ty * T
    d.rectangle([X + 4, Y + 4, X + 11, Y + 14], fill=(70, 96, 70)); d.rectangle([X + 3, Y + 3, X + 12, Y + 5], fill=(50, 70, 50)); EXTRA.add((tx, ty))
for (x, y) in [(18, 20), (44, 14), (33, 32), (52, 42)]:
    trash(x, y)

# subway entrance: green railings, globe lamps
def subway(tx, ty):
    X, Y = tx * T, ty * T
    d.rectangle([X, Y + 2, X + 31, Y + 15], fill=(40, 44, 52)); d.rectangle([X + 4, Y + 5, X + 27, Y + 15], fill=(18, 18, 22))
    for k in range(4, 28, 3): d.line([X + 4, Y + 5 + (k - 4) // 3, X + 27, Y + 5 + (k - 4) // 3], fill=(60, 60, 66))
    d.rectangle([X, Y + 2, X + 31, Y + 3], fill=(36, 110, 66)); d.rectangle([X, Y + 2, X + 1, Y + 15], fill=(36, 110, 66)); d.rectangle([X + 30, Y + 2, X + 31, Y + 15], fill=(36, 110, 66))
    for k in (0, 28): d.ellipse([X + k, Y - 4, X + k + 4, Y], fill=(140, 220, 120)); d.line([X + k + 2, Y, X + k + 2, Y + 2], fill=(36, 110, 66))
    EXTRA.update({(tx, ty), (tx + 1, ty)})
subway(12, 20)
subway(44, 32)

# the fountain in the reservoir
FX, FY = 11 * T, 31 * T + 8
d.ellipse([FX - 14, FY - 6, FX + 30, FY + 18], fill=(176, 170, 160)); d.ellipse([FX - 10, FY - 3, FX + 26, FY + 15], fill=(86, 150, 210))
d.rectangle([FX + 5, FY - 12, FX + 10, FY + 6], fill=(200, 196, 188)); d.ellipse([FX - 1, FY - 16, FX + 16, FY - 8], fill=(200, 196, 188))
for k in range(-3, 20, 4): d.line([FX + 7, FY - 18, FX + k, FY - 6], fill=(200, 230, 255))

# lamps are editor props; mark where we want them
LAMPS = [(6, 15), (18, 15), (27, 15), (34, 15), (46, 15), (6, 20), (20, 20), (30, 20), (38, 20), (50, 20),
         (30, 29), (38, 29), (47, 29), (30, 32), (47, 32), (8, 42), (16, 42), (34, 42), (46, 42), (6, 45), (16, 45), (26, 45), (36, 45), (46, 45)]

# ---------------------------------------------------------------- write
blocked = set(EXTRA)
for (x0, y0, x1, y1) in FILL:
    for ty in range(y0 // T, y1 // T + 1):
        for tx in range(x0 // T, x1 // T + 1):
            ox = max(0, min(x1, tx * T + 15) - max(x0, tx * T) + 1); oy = max(0, min(y1, ty * T + 15) - max(y0, ty * T) + 1)
            if ox * oy >= 128 and 0 <= tx < W and 0 <= ty < H: blocked.add((tx, ty))

grid_editor = [''.join('S' if c == 'P' else ('S' if c == 'K' else c) for c in row) for row in g]
layout = {'v': 1, 'area': 12, 'name': 'Voltmark', 'kind': 'town', 'w': W, 'h': H, 'style': 'a5', 'treeArea': 5, 'tint': None, 'water': None,
          'grid': grid_editor, 'buildings': B, 'props': [{'prop': 'lamp', 'x': x, 'y': y} for x, y in LAMPS], 'signs': SIGNS, 'npcs': NPCS,
          'exits': [{'side': 'east', 'a': 17, 'b': 19, 'to': 11}, {'side': 'west', 'a': 17, 'b': 19, 'to': 13}], 'doors': {}}
walls = {(x, y) for y in range(H) for x in range(W) if g[y][x] == 'K'}
json.dump(layout, open(os.path.join(OUT, 'vm_layout.json'), 'w'), ensure_ascii=False)
json.dump({'blocked': sorted(blocked | walls), 'grid': [''.join(r) for r in g]}, open(os.path.join(OUT, 'vm_extra.json'), 'w'))
img.save(os.path.join(OUT, 'vm_ground.png'))
print('ok', len(blocked), 'painted blocks')
