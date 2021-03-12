import png
import re
import mysql.connector

FONT_SIX = 'images/text/6_12.png'
FONT_EIGHT = 'images/text/8_16.png'
HEIGHT = 400
WIDTH = 640
SCALE = 2
CHROMA_KEY = [255, 0, 255]


class Visualizer:
    def build_character(self, pixels, type_case, char, x, y, x_off, y_off):
        id = ord(char)
        if id < 128:
            character_origin = [(id % 16) * x_off, (id // 16) * y_off]
        else:
            character_origin = [0, 0]

        scale_x = 0
        scale_y = 0
        for k in range(y, y+y_off):
            for j in range(x*3, (x+x_off)*3, 3):
                row = list(type_case[character_origin[1]])
                r = row[character_origin[0]*4+0]
                g = row[character_origin[0]*4+1]
                b = row[character_origin[0]*4+2]
                if r is not CHROMA_KEY[0] or g is not CHROMA_KEY[1] or b is not CHROMA_KEY[2]:
                    pixels[k][j+0] = r
                    pixels[k][j+1] = g
                    pixels[k][j+2] = b
                scale_x = scale_x + 1
                if scale_x >= SCALE:
                    scale_x = 0
                    character_origin[0] = character_origin[0] + 1
            character_origin[0] = (id % 16) * x_off
            scale_y = scale_y + 1
            if scale_y >= SCALE:
                scale_x = 0
                character_origin[1] = character_origin[1] + 1

    def build_text(self, pixels, font, x, y, string: str):
        type_reader = png.Reader(filename=font)
        type_case = type_reader.asRGBA()

        rex = re.compile(r'\d+')
        offsets = rex.findall(font)
        x_off = int(offsets[0])
        y_off = int(offsets[1])

        wx = x
        wy = y

        type_case_list = list(type_case[2])

        for c in string:
            self.build_character(pixels, type_case_list, c, wx, wy, x_off, y_off)
            wx = wx + x_off*SCALE
            if wx+x_off > WIDTH*SCALE:
                wx = x
                wy = wy + y_off*SCALE

    def build_test_text(self, text):
        f = open('images/output/test.png', 'wb')
        w = png.Writer(width=WIDTH*SCALE, height=HEIGHT*SCALE, bitdepth=8, greyscale=False)
        # pixels = [[128, 128, 128] * WIDTH] * HEIGHT  <-- EVIL
        pixels = [[128, 128, 128] * WIDTH*SCALE for _ in range(HEIGHT*SCALE)]
        self.build_text(pixels, FONT_SIX, 2, 2, text)
        w.write(f, pixels)

        return f.name
