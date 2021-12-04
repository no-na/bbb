import png
import re
import random
import os
import colorsys

FONT_SIX = 'images/text/6_12.png'
FONT_EIGHT = 'images/text/8_16.png'
HEIGHT = 400
WIDTH = 640
SCALE = 2
CHROMA_KEY = [255, 0, 255]
WHITE = [255, 255, 255]
RGB_OFFSET = 3
GRAPH_BACK_COLOR = [164, 164, 164]
GRAPH_LEFT_COLOR = [44, 44, 44]
GRAPH_BOTT_COLOR = [133, 133, 133]
GRAPH_BAR_TOP_HLV = [0, 50, 100]
GRAPH_BAR_FRONT_HLV = [0, 26, 100]
GRAPH_BAR_SIDE_HLV = [0, 17, 100]
GRAPH_BAR_MAX_WIDTH = 20
SYSTEM_MID_COLOR = [84, 84, 152]
SYSTEM_SDW_COLOR = [57, 57, 113]
SYSTEM_HLT_COLOR = [118, 118, 171]
GRAPH_DEPTH = 6
FONTS = {
    FONT_SIX: list(png.Reader(filename=FONT_SIX).asRGBA()[2]),
    FONT_EIGHT: list(png.Reader(filename=FONT_EIGHT).asRGBA()[2])
}


class Visualizer:
    pixels = []

    def __init__(self):
        self.pixels = [[128, 128, 128] * WIDTH * SCALE for _ in range(HEIGHT * SCALE)]

    def is_tag(self, string):
        rex = re.compile(r'^\[\[\D:*.*\]\]$')
        if re.match(rex, string):
            return True
        return False

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
                white_replace[0] = WHITE[0]
                white_replace[1] = WHITE[1]
                white_replace[2] = WHITE[2]
                return True
        return False

    def hard_light(self, a, b):
        if b/255 < 0.5:
            return int((2 * b/255 * a/255) * 255)
        else:
            return int((1 - 2 * (1 - b/255) * (1 - a/255)) * 255)

    def draw_pixel(self, x, y, color, mode="normal"):
        pixels = self.pixels
        hard_light = self.hard_light
        scale = SCALE
        offset = RGB_OFFSET
        for k in range(0, scale):
            ry = y * scale + k
            row = pixels[ry]
            for j in range(0, scale):
                rx = (x * scale + j) * offset
                if mode == "normal":
                    row[rx + 0] = color[0]
                    row[rx + 1] = color[1]
                    row[rx + 2] = color[2]
                elif mode == "hard-light":
                    row[rx + 0] = hard_light(row[rx + 0], color[0])
                    row[rx + 1] = hard_light(row[rx + 1], color[1])
                    row[rx + 2] = hard_light(row[rx + 2], color[2])

    def build_character(self, type_case, char, x, y, x_off, y_off, white_replace=None):
        if white_replace is None:
            white_replace = WHITE
        asc = ord(char)
        if asc == 10:  # New Line
            return 10
        if asc < 128:
            ref_pos = [(asc % 16) * x_off, (asc // 16) * y_off]
        else:
            ref_pos = [0, 0]

        for k in range(y, y + y_off):
            row = type_case[ref_pos[1]]
            for j in range(x, x + x_off):
                r = row[ref_pos[0] * 4 + 0]
                g = row[ref_pos[0] * 4 + 1]
                b = row[ref_pos[0] * 4 + 2]
                if white_replace != WHITE and [r, g, b] == WHITE:
                    r = white_replace[0]
                    g = white_replace[1]
                    b = white_replace[2]
                elif white_replace != WHITE and [r, g, b] == [0, 0, 0]:
                    r = max(0, white_replace[0] - 140)
                    g = max(0, white_replace[1] - 140)
                    b = max(0, white_replace[2] - 140)
                if r is not CHROMA_KEY[0] or g is not CHROMA_KEY[1] or b is not CHROMA_KEY[2]:
                    self.draw_pixel(j, k, [r, g, b])
                ref_pos[0] = ref_pos[0] + 1
            ref_pos[0] = (asc % 16) * x_off
            ref_pos[1] = ref_pos[1] + 1
        return asc

    def build_text(self, font, x, y, end_x=None, end_y=None, string: str = None, align: str = "left", overflow: str = "overflow"):
        rex = re.compile(r'\d+')
        offsets = rex.findall(font)
        x_off = int(offsets[0])
        y_off = int(offsets[1])

        wx = x
        wy = y

        if end_x is None:
            end_x = WIDTH
        if end_y is None:
            end_y = HEIGHT

        # Split string into lines
        split_string = re.findall(r'\[\[.+?\]\]|\s|\b\w+\b|\W', string)
        color_replaces = {}
        lines = []
        line = ""
        for s in split_string:
            replace = [255, 255, 255]
            if s == "\n":
                lines.append(line.strip())
                line = ""
            elif self.parse_tag(s, replace) is True:
                color_replaces[(len(lines), len(line))] = replace
            elif x_off * (len(line) + len(s)) < end_x - x:
                if len(line) == 0 and s == " ":
                    continue
                line += s
            else:
                lines.append(line.strip())
                line = s
        lines.append(line.strip())
        print(color_replaces)
        print((0, 10) in color_replaces)
        white_replace = [255, 255, 255]
        for l in range(0, len(lines)):
            for c in range(0, len(lines[l])):
                print("D" + str((l, c)))
                if (l, c) in color_replaces:
                    print("F" + str((l, c)))
                    white_replace = color_replaces[(l, c)]
                self.build_character(FONTS[font], lines[l][c], wx, wy, x_off, y_off, white_replace=white_replace)
                wx = wx + x_off
            if wy + y_off < end_y:
                wx = x
                wy = wy + y_off
            else:
                return

    def build_dot(self, start_x=None, start_y=None, color_high=None, color_mid=None, color_low=None):
        self.draw_pixel(start_x + 1, start_y + 0, color_mid)
        self.draw_pixel(start_x + 2, start_y + 0, color_mid)
        self.draw_pixel(start_x + 3, start_y + 0, color_mid)

        self.draw_pixel(start_x + 0, start_y + 1, color_mid)
        self.draw_pixel(start_x + 1, start_y + 1, WHITE)
        self.draw_pixel(start_x + 2, start_y + 1, color_high)
        self.draw_pixel(start_x + 3, start_y + 1, color_mid)
        self.draw_pixel(start_x + 4, start_y + 1, color_low)

        self.draw_pixel(start_x + 0, start_y + 2, color_mid)
        self.draw_pixel(start_x + 1, start_y + 2, color_high)
        self.draw_pixel(start_x + 2, start_y + 2, color_high)
        self.draw_pixel(start_x + 3, start_y + 2, color_mid)
        self.draw_pixel(start_x + 4, start_y + 2, color_low)

        self.draw_pixel(start_x + 0, start_y + 3, color_mid)
        self.draw_pixel(start_x + 1, start_y + 3, color_mid)
        self.draw_pixel(start_x + 2, start_y + 3, color_mid)
        self.draw_pixel(start_x + 3, start_y + 3, color_mid)
        self.draw_pixel(start_x + 4, start_y + 3, color_low)

        self.draw_pixel(start_x + 1, start_y + 4, color_low)
        self.draw_pixel(start_x + 2, start_y + 4, color_low)
        self.draw_pixel(start_x + 3, start_y + 4, color_low)

    def build_graph(self, start_x=None, start_y=None, end_x=None, end_y=None, data=None):
        legend_x = int((end_x - start_x) * 0.7 + start_x)

        # Test data
        if data is None:
            data = [['Pillar A', 'Pillar B', 'Pillar C', 'Pillar D'], [8, 13, 1, 34]]

        # Background
        for k in range(start_y, end_y):
            for j in range(start_x, legend_x):
                if j < start_x + (GRAPH_DEPTH - (k - start_y)) and k < start_y + GRAPH_DEPTH:
                    color_to_use = None
                elif j == start_x or k == end_y - 1:
                    color_to_use = WHITE
                elif j < start_x + (GRAPH_DEPTH - (k - (end_y - GRAPH_DEPTH))) and k >= end_y - GRAPH_DEPTH:
                    color_to_use = GRAPH_LEFT_COLOR
                elif k >= end_y - GRAPH_DEPTH:
                    color_to_use = GRAPH_BOTT_COLOR
                elif j < start_x + GRAPH_DEPTH:
                    color_to_use = GRAPH_LEFT_COLOR
                else:
                    color_to_use = GRAPH_BACK_COLOR

                if color_to_use is not None:
                    self.draw_pixel(j, k, color_to_use)

        # Bars
        graph_bar_hues = []
        graph_bar_top_rgb = []
        graph_bar_front_rgb = []
        graph_bar_side_rgb = []
        hue_offset = random.randint(0, 360)
        legend_text = ""
        _ = legend_x-4 - start_x+1
        graph_bar_width = min(_ // len(data[0]), GRAPH_BAR_MAX_WIDTH)
        graph_bar_width = _ // len(data[0])
        graph_bar_spacing = int(graph_bar_width * 0.2)
        graph_bar_width = graph_bar_width - graph_bar_spacing

        for i in range(0, len(data[0])):
            graph_bar_hues.append(i * 360 // len(data[0]) + hue_offset)
            if graph_bar_hues[i] >= 360:
                graph_bar_hues[i] = graph_bar_hues[i] - 360
            graph_bar_top_rgb.append(
                colorsys.hls_to_rgb(
                    graph_bar_hues[i] / 360,
                    GRAPH_BAR_TOP_HLV[1] / 100,
                    GRAPH_BAR_TOP_HLV[2] / 100))
            graph_bar_front_rgb.append(
                colorsys.hls_to_rgb(
                    graph_bar_hues[i] / 360,
                    GRAPH_BAR_FRONT_HLV[1] / 100,
                    GRAPH_BAR_FRONT_HLV[2] / 100))
            graph_bar_side_rgb.append(
                colorsys.hls_to_rgb(
                    graph_bar_hues[i] / 360,
                    GRAPH_BAR_SIDE_HLV[1] / 100,
                    GRAPH_BAR_SIDE_HLV[2] / 100))
            graph_bar_top_rgb[i] = (
                int(graph_bar_top_rgb[i][0] * 255),
                int(graph_bar_top_rgb[i][1] * 255),
                int(graph_bar_top_rgb[i][2] * 255))
            graph_bar_front_rgb[i] = (
                int(graph_bar_front_rgb[i][0] * 255),
                int(graph_bar_front_rgb[i][1] * 255),
                int(graph_bar_front_rgb[i][2] * 255))
            graph_bar_side_rgb[i] = (
                int(graph_bar_side_rgb[i][0] * 255),
                int(graph_bar_side_rgb[i][1] * 255),
                int(graph_bar_side_rgb[i][2] * 255))

            bar_depth = GRAPH_DEPTH - 1
            bar_start_y = end_y-1 - int((end_y-1 - start_y) * 0.8 * (data[1][i] / data[1][0])) - bar_depth
            bar_end_y = end_y-1
            for k in range(bar_start_y, bar_end_y):
                bar_start_x = start_x + 1 + graph_bar_spacing + (graph_bar_width + graph_bar_spacing) * i
                bar_end_x = bar_start_x + graph_bar_width
                for j in range(bar_start_x, bar_end_x):
                    if j < bar_start_x + (bar_depth - (k - bar_start_y)) and k < bar_start_y + bar_depth:
                        color_to_use = None
                    elif bar_start_x + graph_bar_width-bar_depth <= j < bar_start_x + graph_bar_width-bar_depth + (
                            bar_depth - (k - bar_start_y)) and k < bar_start_y + bar_depth:
                        color_to_use = graph_bar_top_rgb[i]
                    elif bar_start_x + graph_bar_width-bar_depth <= j < bar_start_x + graph_bar_width-bar_depth + (
                            bar_depth - (k - (bar_end_y - bar_depth))) and k >= bar_end_y - bar_depth:
                        color_to_use = graph_bar_side_rgb[i]
                    elif j >= bar_start_x + graph_bar_width-bar_depth and k >= end_y - bar_depth:
                        color_to_use = GRAPH_BOTT_COLOR
                    elif j >= bar_start_x + graph_bar_width-bar_depth:
                        color_to_use = graph_bar_side_rgb[i]
                    elif k < bar_start_y + bar_depth:
                        color_to_use = graph_bar_top_rgb[i]
                    else:
                        color_to_use = graph_bar_front_rgb[i]

                    if color_to_use is not None:
                        self.draw_pixel(j, k, color_to_use)

            legend_text = legend_text + data[0][i] + os.linesep
            self.build_dot(start_x=legend_x + 2, start_y=start_y + 4 + 12 * i, color_high=graph_bar_top_rgb[i],
                           color_mid=graph_bar_front_rgb[i], color_low=graph_bar_side_rgb[i])

        self.build_text(FONT_SIX, legend_x + 9, start_y + 2, end_x=end_x, end_y=end_y, string=legend_text)

    def build_system_bar(self):
        start_x = 0
        end_x = WIDTH
        start_y = 0
        end_y = 14
        for k in range(start_y, end_y):
            for j in range(start_x, end_x):
                if (k == start_y and j < end_x - 1) or (j == start_x and k < end_y - 1):
                    self.draw_pixel(j, k, SYSTEM_HLT_COLOR)
                elif (k == end_y - 1 and j > start_x) or (j == end_x - 1 and k > start_y):
                    self.draw_pixel(j, k, SYSTEM_SDW_COLOR)
                else:
                    self.draw_pixel(j, k, SYSTEM_MID_COLOR)

    def build_image(self, filename, start_x, start_y, end_x, end_y, mode="normal"):
        _ = png.Reader(filename=filename)
        image_gen = _.asRGBA()[2]
        row = None

        for k in range(start_y, end_y):
            row = next(image_gen)
            for j in range(start_x, end_x):
                color = [
                    row[j * 4 + 0],
                    row[j * 4 + 1],
                    row[j * 4 + 2]
                ]
                if color != CHROMA_KEY:
                    self.draw_pixel(j, k, color, mode=mode)

    def build_background(self):
        backgrounds = os.listdir('images/background/')
        _ = random.randint(0, len(backgrounds) - 1)
        back_name = backgrounds[_]
        self.build_image('images/background/' + back_name, 0, 0, WIDTH, HEIGHT)
        self.build_system_bar()
        self.build_text(FONT_SIX, 1, 1, string=back_name[:-4])

    def finish_image(self):
        f = open('images/output/test.png', 'wb')
        w = png.Writer(width=WIDTH * SCALE, height=HEIGHT * SCALE, bitdepth=8, greyscale=False)
        w.write(f, self.pixels)
        return f.name
