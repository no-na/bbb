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
    pixels = []

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

    def build_character(self, type_case, char, x, y, x_off, y_off, white_replace=None):
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
                    self.pixels[k][j + 0] = r
                    self.pixels[k][j + 1] = g
                    self.pixels[k][j + 2] = b
                scale_x = scale_x + 1
                if scale_x >= SCALE:
                    scale_x = 0
                    ref_pos[0] = ref_pos[0] + 1
            ref_pos[0] = (asc % 16) * x_off
            scale_y = scale_y + 1
            if scale_y >= SCALE:
                scale_y = 0
                ref_pos[1] = ref_pos[1] + 1

    def build_text(self, font, x, y, end_x=None, end_y=None, string: str = None):
        type_reader = png.Reader(filename=font)
        type_case = type_reader.asRGBA()

        rex = re.compile(r'\d+')
        offsets = rex.findall(font)
        x_off = int(offsets[0])
        y_off = int(offsets[1])

        wx = x * SCALE
        wy = y * SCALE

        if end_x is None:
            end_x = WIDTH
        if end_y is None:
            end_y = HEIGHT

        type_case_list = list(type_case[2])  # We don't keep this as a generator because we aren't iterating.

        split_string = re.findall(r'\[\[.+?\]\]|\s|\b\w+\b|\W', string)
        white_replace = [255, 255, 255]
        new_line = False
        for s in split_string:
            if self.parse_tag(s, white_replace) is True:
                continue
            if wx + x_off * len(s) * SCALE >= end_x * SCALE:
                if wy + y_off * SCALE < end_y * SCALE:
                    wx = x * SCALE
                    wy = wy + y_off * SCALE
                    new_line = True
                else:
                    return
            for c in s:
                if c != ' ' or new_line is False:
                    self.build_character(type_case_list, c, wx, wy, x_off, y_off, white_replace=white_replace)
                    wx = wx + x_off * SCALE
                    new_line = False

    def build_graph(self, start_x=None, start_y=None, end_x=None, end_y=None, data=None):
        GRAPH_BACK_COLOR = [164, 164, 164]
        GRAPH_LEFT_COLOR = [44, 44, 44]
        GRAPH_BOTT_COLOR = [133, 133, 133]
        GRAPH_DEPTH = 6
        legend_x = int((end_x - start_x) * 0.8 + start_x)

        scale_x = 0
        scale_y = 0
        for k in range(start_y * SCALE, end_y * SCALE):
            for j in range(start_x * SCALE * 3, (legend_x * SCALE) * 3, 3):
                # (GRAPH_DEPTH - (j - (start_x * SCALE * 3)) // 3)
                use_prev_pixel_x = 0
                use_prev_pixel_y = 0
                color_to_use = None
                if scale_x != 0:
                    use_prev_pixel_x = 3
                if scale_y != 0:
                    use_prev_pixel_y = 1

                if j < (start_x * SCALE * 3) + (GRAPH_DEPTH - (k - (start_y * SCALE))) * SCALE * 3 and k < start_y * SCALE + GRAPH_DEPTH * SCALE:
                    color_to_use = None
                elif j == start_x * SCALE * 3 or k == end_y * SCALE - 1:
                    color_to_use = WHITE
                elif j < start_x * SCALE * 3 + GRAPH_DEPTH * SCALE * 3:
                    color_to_use = GRAPH_LEFT_COLOR
                elif j < (start_x * SCALE * 3) + (GRAPH_DEPTH - (k - (end_y * SCALE - GRAPH_DEPTH * SCALE))) * SCALE * 3 and k >= end_y * SCALE - GRAPH_DEPTH * SCALE:
                    color_to_use = GRAPH_BOTT_COLOR
                else:
                    color_to_use = GRAPH_BACK_COLOR

                if color_to_use is not None:
                    if use_prev_pixel_y != 0 or use_prev_pixel_x != 0:
                        self.pixels[k][j + 0] = self.pixels[k - use_prev_pixel_y][j - use_prev_pixel_x + 0]
                        self.pixels[k][j + 1] = self.pixels[k - use_prev_pixel_y][j - use_prev_pixel_x + 1]
                        self.pixels[k][j + 2] = self.pixels[k - use_prev_pixel_y][j - use_prev_pixel_x + 2]
                    else:
                        self.pixels[k][j + 0] = color_to_use[0]
                        self.pixels[k][j + 1] = color_to_use[0]
                        self.pixels[k][j + 2] = color_to_use[0]

                scale_x = scale_x + 1
                if scale_x >= SCALE:
                    scale_x = 0;
            scale_y = scale_y + 1
            if scale_y >= SCALE:
                scale_y = 0;

        self.build_text(FONT_SIX, legend_x+2, start_y+2, end_x=end_x, end_y=end_y, string="LEGEND")

    def build_background(self):
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
                    self.pixels[k][j + 0] = r
                    self.pixels[k][j + 1] = g
                    self.pixels[k][j + 2] = b
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
        self.pixels = [[128, 128, 128] * WIDTH * SCALE for _ in range(HEIGHT * SCALE)]
        self.build_background()
        self.build_text(FONT_SIX, x, y, end_x=320, end_y=200, string=text)
        self.build_graph(start_x=8, start_y=208, end_x=320, end_y=HEIGHT - 8)
        w.write(f, self.pixels)

        return f.name

    def build_text_birch(self, text, x, y, background):
        f = open('images/output/test.png', 'wb')
        w = png.Writer(width=WIDTH * SCALE, height=HEIGHT * SCALE, bitdepth=8, greyscale=False)
        self.pixels = [[128, 128, 128] * WIDTH * SCALE for _ in range(HEIGHT * SCALE)]
        self.build_background()
        self.build_text(FONT_EIGHT, x, y, text)
        w.write(f, self.pixels)

        return f.name
