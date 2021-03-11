import png
import re
import mysql.connector

FONT_SIX = 'images/text/6_12.png'
FONT_EIGHT = 'images/text/8_16.png'
HEIGHT = 400
WIDTH = 640
CHROMA_KEY = [0, 255, 255]


class Visualizer:
    def build_character(self, pixels, type_case, char, x, y, x_off, y_off):
        id = ord(char)
        print(char)
        print(id)
        character_origin = [(id % 16) * x_off, (id // 16) * y_off]
        print(character_origin[0])
        print(character_origin[1])
        print(type_case)
        print(type_case[character_origin[1]])
        print(type_case[character_origin[1]].length)

        for k in range(y, y+y_off):
            for j in range(x*3, (x+x_off)*3, 3):
                r = type_case[character_origin[1]][character_origin[0]*4+0]
                g = type_case[character_origin[1]][character_origin[0]*4+1]
                b = type_case[character_origin[1]][character_origin[0]*4+2]
                if r is not CHROMA_KEY[0] and g is not CHROMA_KEY[1] and b is not CHROMA_KEY[2]:
                    pixels[k][j*3+0] = r
                    pixels[k][j*3+1] = g
                    pixels[k][j*3+2] = b
                character_origin[0] = character_origin[0] + 1
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

        for c in string:
            self.build_character(pixels, type_case, c, wx, wy, x_off, y_off)
            wx = wx + x_off
            if wx > WIDTH:
                wx = x
                wy = wy + y_off

    def build_test_text(self):
        f = open('images/output/test.png', 'wb')
        w = png.Writer(width=WIDTH, height=HEIGHT, bitdepth=16)
        pixels = [[128, 128, 128] * WIDTH] * HEIGHT
        self.build_text(pixels, FONT_SIX, 2, 2, "Birch Countess")
        w.write(f.name, pixels)

        return f.name
