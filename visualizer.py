import png
import re
import random
import os
import time
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
            ref_pos = [(id % 16) * x_off, (id // 16) * y_off]
        else:
            ref_pos = [0, 0]

        scale_x = 0
        scale_y = 0
        for k in range(y, y+y_off*SCALE):
            row = list(type_case[ref_pos[1]])
            for j in range(x*3, (x+x_off*SCALE)*3, 3):
                r = row[ref_pos[0]*4+0]
                g = row[ref_pos[0]*4+1]
                b = row[ref_pos[0]*4+2]
                if r is not CHROMA_KEY[0] or g is not CHROMA_KEY[1] or b is not CHROMA_KEY[2]:
                    pixels[k][j+0] = r
                    pixels[k][j+1] = g
                    pixels[k][j+2] = b
                scale_x = scale_x + 1
                if scale_x >= SCALE:
                    scale_x = 0
                    ref_pos[0] = ref_pos[0] + 1
            ref_pos[0] = (id % 16) * x_off
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

        type_case_list = list(type_case[2])

        for c in string:
            self.build_character(pixels, type_case_list, c, wx, wy, x_off, y_off)
            wx = wx + x_off*SCALE
            if wx+x_off >= WIDTH*SCALE:
                wx = x
                wy = wy + y_off*SCALE

    def build_background(self, pixels):
        t0 = time.process_time()
        backgrounds = os.listdir('images/background/')
        _ = random.randint(0, len(backgrounds) - 1)
        t1 = time.process_time() - t0
        back_reader = png.Reader(filename='images/background/'+backgrounds[_])
        t2 = time.process_time() - t1
        back_gen = back_reader.asRGBA()[2]
        t3 = time.process_time() - t2

        scale_x = 0
        scale_y = 0
        ref_pos = [0, 0]
        DEBUG_CURRENT_ROW = 0;
        row = next(back_gen)
        for k in range(0, HEIGHT * SCALE):
            for j in range(0, (WIDTH * SCALE) * 3, 3):
                r = row[ref_pos[0] * 4 + 0]
                g = row[ref_pos[0] * 4 + 1]
                b = row[ref_pos[0] * 4 + 2]
                if r is not CHROMA_KEY[0] or g is not CHROMA_KEY[1] or b is not CHROMA_KEY[2]:
                    pixels[k][j + 0] = r
                    pixels[k][j + 1] = g
                    pixels[k][j + 2] = b
                scale_x = scale_x + 1
                if scale_x >= SCALE:
                    scale_x = 0
                    ref_pos[0] = ref_pos[0] + 1
            ref_pos[0] = 0
            scale_y = scale_y + 1
            if scale_y >= SCALE:
                scale_y = 0
                DEBUG_CURRENT_ROW = DEBUG_CURRENT_ROW + 1
                print(DEBUG_CURRENT_ROW)
                row = next(back_gen)

        t4 = time.process_time() - t3

        aa = [0] * WIDTH * SCALE * HEIGHT * 3
        t5 = time.process_time()
        for k in range(0, len(aa)):
            aa[k] = 256
        t6 = time.process_time() - t5
        print(t1)

        print('Build Background Pick File: ', t1)
        print('Build Background Make Reader: ', t2)
        print('Build Background Make List: ', t3)
        print('Build Background Paint Pixels: ', t4)
        print('List Work Example: ', t6)




    def build_test_text(self, text):
        f = open('images/output/test.png', 'wb')
        w = png.Writer(width=WIDTH*SCALE, height=HEIGHT*SCALE, bitdepth=8, greyscale=False)
        # pixels = [[128, 128, 128] * WIDTH] * HEIGHT  <-- EVIL
        pixels = [[128, 128, 128] * WIDTH*SCALE for _ in range(HEIGHT*SCALE)]
        self.build_background(pixels)
        self.build_text(pixels, FONT_SIX, 2*SCALE, 2*SCALE, text)
        w.write(f, pixels)

        return f.name

    def build_text_birch(self, text, x, y, background):
        f = open('images/output/test.png', 'wb')
        w = png.Writer(width=WIDTH * SCALE, height=HEIGHT * SCALE, bitdepth=8, greyscale=False)
        pixels = [[128, 128, 128] * WIDTH * SCALE for _ in range(HEIGHT * SCALE)]
        t0 = time.process_time()
        if background == 'True':
            self.build_background(pixels)
        t1 = time.process_time() - t0
        self.build_text(pixels, FONT_EIGHT, x*SCALE, y*SCALE, text)
        t2 = time.process_time() - t1
        w.write(f, pixels)
        t3 = time.process_time() - t2

        print('Build Background Total: ', t1)
        print('Build Text: ', t2)
        print('Write: ', t3)

        return f.name
