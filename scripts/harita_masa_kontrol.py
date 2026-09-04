#!/usr/bin/env python3
# kafe.pgm'de her noktanin cevresi haritalanmis mi, sayisal kontrol.
# roscore gerekmez; haritayi diskten okur.
import os
import sys
import rospkg

PGM = os.path.join(rospkg.RosPack().get_path('cafe_service_robot'), 'maps', 'kafe_ham.pgm')
RES = 0.05
OX, OY = -15.0, -15.0

NOKTALAR = [
    ('cafe_table',    3.523, -0.449),
    ('cafe_table_7',  0.677, -0.570),
    ('cafe_table_0',  3.615, -3.172),
    ('cafe_table_3',  0.672, -3.217),
    ('cafe_table_9', -1.838, -3.287),
    ('cafe_table_1',  3.682, -6.076),
    ('cafe_table_4',  0.833, -6.033),
    ('cafe_table_8', -1.784, -6.010),
    ('cafe_table_2',  3.776, -8.787),
    ('cafe_table_5',  0.910, -8.867),
    ('cafe_table_6', -1.678, -8.987),
    ('SARJ',          4.107,  8.581),
    ('TEZGAH',       -0.226,  2.758),
]

def pgm_oku(yol):
    with open(yol, 'rb') as f:
        if f.readline().strip() != b'P5':
            sys.exit('P5 formatinda degil')
        s = f.readline()
        while s.startswith(b'#'):
            s = f.readline()
        w, h = map(int, s.split())
        f.readline()
        return w, h, f.read()

w, h, veri = pgm_oku(PGM)
print('harita: %dx%d px = %.1f x %.1f m' % (w, h, w*RES, h*RES))
print('%-14s %7s %7s   %s' % ('NOKTA', 'x', 'y', 'SONUC'))

R = 10   # +-0.5 m pencere
for ad, mx, my in NOKTALAR:
    sut = int((mx - OX) / RES)
    sat = h - 1 - int((my - OY) / RES)
    if not (R <= sut < w-R and R <= sat < h-R):
        print('%-14s %7.3f %7.3f   HARITA DISI' % (ad, mx, my))
        continue
    engel = bos = bilinmeyen = 0
    for dy in range(-R, R+1):
        for dx in range(-R, R+1):
            px = veri[(sat+dy)*w + (sut+dx)]
            if   px < 100: engel += 1
            elif px > 220: bos += 1
            else:          bilinmeyen += 1
    toplam = (2*R+1)**2
    yuzde_bilinmeyen = 100*bilinmeyen//toplam
    if yuzde_bilinmeyen > 40:
        sonuc = 'GRI  %d%% bilinmiyor  <-- surulmeli' % yuzde_bilinmeyen
    elif engel >= 5:
        sonuc = 'OK   engel var (%d px), bos %d%%' % (engel, 100*bos//toplam)
    else:
        sonuc = 'BOS  engel yok (%d px)' % engel
    print('%-14s %7.3f %7.3f   %s' % (ad, mx, my, sonuc))
