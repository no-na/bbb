import png
import re
import mysql.connector

FONT_SIX = 'images/text/6_12.png'
FONT_EIGHT = 'images/text/8_16.png'
HEIGHT = 400
WIDTH = 640
CHROMA_KEY = [255, 0, 255]


class Visualizer:
    def build_character(self, pixels, type_case, char, x, y, x_off, y_off):
        id = ord(char)
        character_origin = [(id % 16) * x_off, (id // 16) * y_off]
        print(character_origin)

        for k in range(y, y+y_off):
            for j in range(x*3, (x+x_off)*3, 3):
                print("Cursor: %2d,%2d" % (j, k))
                row = list(type_case[character_origin[1]])
                r = row[character_origin[0]*4+0]
                g = row[character_origin[0]*4+1]
                b = row[character_origin[0]*4+2]
                if r is not CHROMA_KEY[0] or g is not CHROMA_KEY[1] or b is not CHROMA_KEY[2]:
                    pixels[k][j+0] = r
                    pixels[k][j+1] = g
                    pixels[k][j+2] = b
                    print("Painting at %2d,%2d" % (j, k))
                character_origin[0] = character_origin[0] + 1
            character_origin[0] = (id % 16) * x_off
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
            wx = wx + x_off
            if wx > WIDTH:
                wx = x
                wy = wy + y_off

    def build_test_text(self):
        f = open('images/output/test.png', 'wb')
        w = png.Writer(width=WIDTH, height=HEIGHT, bitdepth=8, greyscale=False)
        pixels = [[128, 128, 128] * WIDTH] * HEIGHT
        self.build_text(pixels, FONT_SIX, 2, 2, "a")
        w.write(f, pixels)

        return f.name
