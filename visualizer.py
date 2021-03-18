import png
import re
import random
import os

FONT_SIX = 'images/text/6_12.png'
FONT_EIGHT = 'images/text/8_16.png'
HEIGHT = 400
WIDTH = 640
SCALE = 2
CHROMA_KEY = [255, 0, 255]
WHITE = [255, 255, 255]


class Visualizer:
    def parse_tag(self, string, white_replace):
        rex = re.compile(r'^\[\[\D:*.*\]\]$')
        if re.match(rex, string):
            rex = re.compile(r'\W')
            split = list(filter(None, re.split(rex, string)))
            if split[0] == 'C':
                white_replace[0] = int(split[1])
                white_replace[1] = int(split[2])
                white_replace[2] = int(split[3])
                return True
            if split[0] == 'c':
                white_replace[0] = 255
                white_replace[1] = 255
                white_replace[2] = 255
                return True
        return False

    def build_character(self, pixels, type_case, char, x, y, x_off, y_off, white_replace=None):
        if white_replace is None:
            white_replace = WHITE
        asc = ord(char)
        if asc < 128:
            ref_pos = [(asc % 16) * x_off, (asc // 16) * y_off]
        else:
            ref_pos = [0, 0]

        scale_x = 0
        scale_y = 0
        for k in range(y, y + y_off * SCALE):
            row = type_case[ref_pos[1]]
            for j in range(x * 3, (x + x_off * SCALE) * 3, 3):
                r = row[ref_pos[0] * 4 + 0]
                g = row[ref_pos[0] * 4 + 1]
                b = row[ref_pos[0] * 4 + 2]
                if white_replace != WHITE and [r, g, b] == WHITE:
                    r = white_replace[0]
                    g = white_replace[1]
                    b = white_replace[2]
                if r is not CHROMA_KEY[0] or g is not CHROMA_KEY[1] or b is not CHROMA_KEY[2]:
                    pixels[k][j + 0] = r
                    pixels[k][j + 1] = g
                    pixels[k][j + 2] = b
                scale_x = scale_x + 1
                if scale_x >= SCALE:
                    scale_x = 0
                    ref_pos[0] = ref_pos[0] + 1
            ref_pos[0] = (asc % 16) * x_off
            scale_y = scale_y + 1
            if scale_y >= SCALE:
                scale_y = 0
                ref_pos[1] = ref_pos[1] + 1

    def build_text(self, pixels, font, x, y, string: str):
        type_reader = png.Reader(filename=font)
        type_case = type_reader.asRGBA()

        rex = re.compile(r'\d+')
        offsets = rex.findall(font)
        x_off = int(offsets[0])
        y_off = int(offsets[1])

        wx = x
        wy = y

        type_case_list = list(type_case[2])  # We don't keep this as a generator because we aren't iterating.

        split_string = re.findall(r'\[\[.+?\]\]|\s|\b\w+\b', string)
        white_replace = [255, 255, 255]
        new_line = False
        for s in split_string:
            if self.parse_tag(s, white_replace) is True:
                continue
            if wx + x_off * len(s) * SCALE >= WIDTH * SCALE:
                wx = x
                wy = wy + y_off * SCALE
                new_line = True
            for c in s:
                if c != ' ' or new_line is False:
                    self.build_character(pixels, type_case_list, c, wx, wy, x_off, y_off)
                    wx = wx + x_off * SCALE
                    new_line = False

    def build_background(self, pixels):
        backgrounds = os.listdir('images/background/')
        _ = random.randint(0, len(backgrounds) - 1)
        _ = png.Reader(filename='images/background/' + backgrounds[_])
        back_gen = _.asRGBA()[2]

        scale_x = 0
        scale_y = 0
        ref_pos = 0

        row = None
        for k in range(0, HEIGHT * SCALE):
            if scale_y == 0:
                row = next(back_gen)
            for j in range(0, (WIDTH * SCALE) * 3, 3):
                r = row[ref_pos * 4 + 0]
                g = row[ref_pos * 4 + 1]
                b = row[ref_pos * 4 + 2]
                if r is not CHROMA_KEY[0] or g is not CHROMA_KEY[1] or b is not CHROMA_KEY[2]:
                    pixels[k][j + 0] = r
                    pixels[k][j + 1] = g
                    pixels[k][j + 2] = b
                scale_x = scale_x + 1
                if scale_x >= SCALE:
                    scale_x = 0
                    ref_pos = ref_pos + 1
            ref_pos = 0
            scale_y = scale_y + 1
            if scale_y >= SCALE:
                scale_y = 0

        # aa = [0] * WIDTH * SCALE * HEIGHT * 3
        # for k in range(0, len(aa)):
        #     aa[k] = 256

    def build_test_text(self, text, x, y):
        f = open('images/output/test.png', 'wb')
        w = png.Writer(width=WIDTH * SCALE, height=HEIGHT * SCALE, bitdepth=8, greyscale=False)
        # pixels = [[128, 128, 128] * WIDTH] * HEIGHT  <-- EVIL
        pixels = [[128, 128, 128] * WIDTH * SCALE for _ in range(HEIGHT * SCALE)]
        self.build_background(pixels)
        self.build_text(pixels, FONT_SIX, x * SCALE, y * SCALE, text)
        w.write(f, pixels)

        return f.name

    def build_text_birch(self, text, x, y, background):
        f = open('images/output/test.png', 'wb')
        w = png.Writer(width=WIDTH * SCALE, height=HEIGHT * SCALE, bitdepth=8, greyscale=False)
        pixels = [[128, 128, 128] * WIDTH * SCALE for _ in range(HEIGHT * SCALE)]
        self.build_background(pixels)
        self.build_text(pixels, FONT_EIGHT, x * SCALE, y * SCALE, text)
        w.write(f, pixels)

        return f.name
