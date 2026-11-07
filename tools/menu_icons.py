"""Draw extra HGSS-style start-menu icons (FLY, POKéMON HERE, ONLINE) in the green menu's frame."""
import os
from PIL import Image
import numpy as np

D = os.path.join(os.path.dirname(__file__), '..', 'sprites', 'ui', 'hgss', 'menu_green')
LIGHT, MID, DARK, SOFT = (242, 250, 244), (94, 182, 140), (30, 88, 58), (176, 210, 192)
SEL = {(40, 104, 66): (255, 226, 82), (242, 250, 244): (255, 255, 255), (94, 182, 140): (52, 206, 130), (30, 88, 58): (18, 72, 42),
       (176, 210, 192): (200, 240, 214), (150, 214, 180): (160, 232, 192), (205, 236, 218): (220, 248, 230)}

GLYPHS = {
    11: [  # FLY: a bird with spread wings
        "......#...........#.....",
        ".....#+#.........#+#....",
        "....#++#.........#++#...",
        "...#+++#.........#+++#..",
        "..#++++#...##....#++++#.",
        "..#+++++#.#++#..#+++++#.",
        "...#++++#.#++#..#++++#..",
        "....#+++##++++##+++#....",
        ".....##+++++++++++##....",
        ".......##+++++++##......",
        ".........#++++#.........",
        "........#+#..#+#........",
        "........##....##........",
    ],
    12: [  # POKéMON HERE: tall grass with a "!" above it
        "..........##..........",
        "..........##..........",
        "..........##..........",
        "..........##..........",
        "......................",
        "..........##..........",
        "...#.............#....",
        "..#+#....#......#+#...",
        "..#+#...#+#....#++#...",
        ".#++#...#+#....#+#..#.",
        ".#+#...#++#...#++#.#+#",
        "#++#...#+#....#+#..#+#",
        "#+#...#++#...#++#.#++#",
        "######################",
    ],
    13: [  # ONLINE: a globe
        ".......########.......",
        ".....##+#++++#+##.....",
        "....#++#++++++#++#....",
        "...#+##++++++++##+#...",
        "..#################...",
        "..#++#++++++++++#++#..",
        "..#++#++++++++++#++#..",
        "..##################..",
        "...#+##++++++++##+#...",
        "....#++#++++++#++#....",
        ".....##+#++++#+##.....",
        ".......########.......",
    ],
}


def make(n, rows):
    base = np.array(Image.open(os.path.join(D, 'icon10_n.png')).convert('RGBA'))
    # clear the inside of the frame back to its two-tone background
    for y in range(2, 24):
        for x in range(2, 38):
            if base[y, x, 3] and tuple(base[y, x, :3]) != (40, 104, 66):
                base[y, x, :3] = LIGHT if y < 13 else MID
    h, w = len(rows), len(rows[0])
    oy, ox = 2 + (22 - h) // 2, 2 + (36 - w) // 2
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == '#':
                base[oy + j, ox + i, :3] = DARK
            elif ch == '+':
                base[oy + j, ox + i, :3] = LIGHT if oy + j >= 13 else SOFT
    Image.fromarray(base).save(os.path.join(D, f'icon{n}_n.png'))
    s = base.copy()
    for y in range(s.shape[0]):
        for x in range(s.shape[1]):
            c = tuple(int(v) for v in s[y, x, :3])
            if s[y, x, 3] and c in SEL:
                s[y, x, :3] = SEL[c]
    Image.fromarray(s).save(os.path.join(D, f'icon{n}_s.png'))


if __name__ == '__main__':
    for n, g in GLYPHS.items():
        make(n, g)
    print('ok')
