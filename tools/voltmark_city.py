"""Voltmark laid out like HGSS Goldenrod City, using only the map editor's own tiles and sprites.

Writes <out>/vm_layout.json, a map in the map editor's format (Goldenrod city style):
  S plaza ground, R avenues, D boardwalk, F flowers, T trees, W sea.
Buildings, rocks, lamps, signs and mailboxes are the editor's kits and props.
Bake it with tools/voltmark_bake.js, which runs the editor's own bakeTown()/townData().

    python3 tools/voltmark_city.py <out_dir>
"""
import json, os, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
W, H = 56, 48
g = [['S'] * W for _ in range(H)]


def fill(x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H, y1 + 1)):
        for x in range(max(0, x0), min(W, x1 + 1)):
            g[y][x] = c


# ---- the sea to the west, the Tower island and the pier
fill(0, 0, 15, H - 1, 'W')
fill(2, 7, 12, 29, 'S')                 # island
fill(0, 16, 1, 19, 'D')                 # pier out to the west road
fill(13, 16, 15, 19, 'D')               # pier to the mainland
fill(4, 24, 5, 25, 'F'); fill(9, 24, 10, 25, 'F'); fill(3, 27, 11, 27, 'F')

# ---- edges: trees along the top, bottom and east side
fill(16, 0, W - 1, 3, 'T')
fill(16, 46, 17, H - 1, 'T'); fill(W - 2, 46, W - 1, H - 1, 'T')
fill(W - 2, 4, W - 1, 13, 'T'); fill(W - 2, 22, W - 1, 45, 'T')
fill(16, 4, 17, 13, 'T'); fill(16, 22, 17, 45, 'T')

# ---- avenues: Broadway east-west (both exits), Fifth Avenue north-south, two side streets
fill(16, 16, W - 1, 19, 'R')
fill(36, 4, 39, H - 1, 'R')
fill(18, 30, W - 3, 31, 'R')
fill(18, 38, W - 3, 39, 'R')
fill(18, 46, W - 3, H - 1, 'R')
# small parks
fill(18, 4, 23, 7, 'F'); fill(26, 4, 27, 5, 'T'); fill(18, 21, 19, 24, 'F')

# ---- buildings
B = []
def bld(kit, x, y, name, goes=None):
    B.append({'kit': kit, 'karea': 5, 'x': x, 'y': y, 'name': name, 'goes': goes or {'type': 'keep'}})
NONE = {'type': 'none'}
def locked(text): return {'type': 'locked', 'text': text}
HOME = ['house_goldenrod', 'house_goldenrod', 'house_cerulean', 'house_goldenrod']
def homes(xs, y, tag, mix=True):
    for i, x in enumerate(xs):
        bld(HOME[(x + y) % len(HOME)] if mix else 'house_goldenrod', x, y, f'{tag}{i}', NONE)

bld('terminal', 9, 16, 'empire', locked('VOLTMARK TOWER\nThe tallest building in Vellmoor.\nThe observation deck is closed after the last thunderstorm.'))
# north of Broadway
homes([42, 47, 51], 9, 'n')
homes([29, 33], 8, 'nw')
bld('radio_tower', 23, 15, 'tower')
bld('train', 31, 15, 'station')
bld('game_corner', 44, 15, 'gamecorner')
bld('gym_goldenrod', 50, 15, 'gym')
# between Broadway and the first side street
bld('center', 22, 29, 'center')
homes([27, 31], 29, 'a')
bld('dept_store', 42, 29, 'dept')
bld('mart', 49, 29, 'mart')
homes([19, 23, 27, 31], 36, 'b', False)
homes([42, 46, 50], 36, 'c', False)
# between the two side streets
bld('house_goldenrod', 20, 44, 'house1')
homes([24, 28, 32], 44, 'd', False)
homes([42, 46, 50], 44, 'e', False)

# ---- props
PROPS = []
def p(kind, x, y): PROPS.append({'prop': kind, 'x': x, 'y': y})
for (x, y) in [(1, 4), (4, 2), (9, 1), (13, 5), (0, 10), (14, 11), (1, 23), (14, 24), (0, 32), (5, 33), (11, 34), (14, 38), (3, 40), (9, 43), (13, 45), (6, 46)]:
    p('rock', x, y)
for x in (19, 26, 34, 41, 47, 53):
    p('lamp', x, 15)
for x in (20, 27, 34, 40, 47):
    p('lamp', x, 20)
for y in (8, 12, 23, 27, 34, 42):
    p('lamp', 35, y)
for y in (6, 12, 22):
    p('lamp', 40, y)
for (x, y) in [(3, 9), (11, 9), (3, 21), (11, 21), (3, 28), (11, 28)]:
    p('lamp', x, y)
p('mailbox', 26, 15); p('mailbox', 46, 32)

SIGNS = [
    {'x': 22, 'y': 20, 'model': 'sign', 'lines': ['VOLTMARK', 'The city that never powers down. Electric-type Gym on Broadway.']},
    {'x': 34, 'y': 20, 'model': 'sign', 'lines': ['@builtin:notice board']},
    {'x': 53, 'y': 15, 'model': 'gymsign', 'lines': ['@builtin:gym sign']},
    {'x': 7, 'y': 20, 'model': 'sign', 'lines': ['VOLTMARK TOWER', 'Rising over the bay. The observation deck is closed for repairs.']},
    {'x': 35, 'y': 29, 'model': 'sign', 'lines': ['FIFTH AVENUE', 'Department Store ↓ · Game Corner ↑']},
]
NPCS = [
    {'builtin': 'keep', 'ox': 39, 'oy': 15, 'x': 48, 'y': 16, 'dir': 'left'},
    {'builtin': 'keep', 'ox': 9, 'oy': 20, 'x': 5, 'y': 26, 'dir': 'down'},
    {'builtin': 'keep', 'ox': 35, 'oy': 21, 'x': 15, 'y': 20, 'dir': 'up'},
    {'builtin': 'keep', 'ox': 28, 'oy': 7, 'x': 31, 'y': 20, 'dir': 'down'},
    {'builtin': 'keep', 'ox': 32, 'oy': 34, 'x': 29, 'y': 32, 'dir': 'down'},
    {'builtin': 'keep', 'ox': 24, 'oy': 21, 'x': 23, 'y': 32, 'dir': 'right'},
    {'builtin': 'keep', 'ox': 33, 'oy': 10, 'x': 40, 'y': 14, 'dir': 'down'},
    {'builtin': 'keep', 'ox': 35, 'oy': 18, 'x': 44, 'y': 21, 'dir': 'down'},
    {'builtin': 'a12_i12', 'x': 21, 'y': 5, 'dir': 'down'},
    {'kind': 'person', 'sheet': 'guitarist', 'x': 8, 'y': 26, 'dir': 'left', 'wander': False, 'say': ['When the Gym powers up, the whole bay sparkles. Best free show in Vellmoor!']},
    {'kind': 'person', 'sheet': 'gentleman', 'x': 29, 'y': 16, 'dir': 'right', 'wander': False, 'say': ['The trains still run on Electric Pokémon power. Clean and quick.']},
    {'kind': 'person', 'sheet': 'pokefan_m', 'x': 26, 'y': 20, 'dir': 'right', 'wander': True, 'say': ['Everybody here walks fast. Try to keep up!']},
    {'kind': 'person', 'sheet': 'school_kid_f', 'x': 11, 'y': 18, 'dir': 'left', 'wander': False, 'say': ['Voltmark Tower is the tallest building in Vellmoor. I want to go to the top someday!']},
    {'kind': 'person', 'sheet': 'fisherman', 'x': 14, 'y': 18, 'dir': 'up', 'wander': False, 'say': ['You’d be amazed what bites in the bay. Mostly old boots, though.']},
    {'kind': 'person', 'sheet': 'policeman', 'x': 37, 'y': 21, 'dir': 'down', 'wander': False, 'say': ['Look both ways! Traffic here doesn’t slow down for anybody.']},
    {'kind': 'person', 'sheet': 'lady', 'x': 45, 'y': 37, 'dir': 'down', 'wander': True, 'say': ['Every house on this street looks the same. I’ve walked into the wrong one twice!']},
    {'kind': 'person', 'sheet': 'youngster', 'x': 25, 'y': 43, 'dir': 'up', 'wander': True, 'say': ['I’m saving coins for a prize at the Game Corner!']},
]

layout = {'v': 1, 'area': 12, 'name': 'Voltmark', 'kind': 'town', 'w': W, 'h': H, 'style': 'a5', 'treeArea': 5, 'tint': None, 'water': None,
          'grid': [''.join(r) for r in g], 'buildings': B, 'props': PROPS, 'signs': SIGNS, 'npcs': NPCS,
          'exits': [{'side': 'east', 'a': 17, 'b': 19, 'to': 11}, {'side': 'west', 'a': 17, 'b': 19, 'to': 13}],
          'doors': {'tower': {'t': 'say', 'lines': ['The Voltmark Radio Tower. A sign on the door says STAFF ONLY.']}, 'dept': {'t': 'dept'}, 'gamecorner': {'t': 'gc'},
                    'gym': {'t': 'warp', 'map': 'a12_gym', 'x': 8, 'y': 15, 'dir': 'up'},
                    'center': {'t': 'warp', 'map': 'a12_celadoncity_pokemoncenter_1f', 'x': 8, 'y': 19, 'dir': 'up'},
                    'mart': {'t': 'say', 'lines': ['The Mart counter is closed. Try the Department Store!']},
                    'station': {'t': 'say', 'lines': ['The Magnet Train isn’t running today.']},
                    'house1': {'t': 'warp', 'map': 'a12_celadoncity_house1', 'x': 4, 'y': 8, 'dir': 'up'}}}
os.makedirs(OUT, exist_ok=True)
json.dump(layout, open(os.path.join(OUT, 'vm_layout.json'), 'w'), ensure_ascii=False)
print('layout', W, H, len(B), 'buildings', len(PROPS), 'props')
