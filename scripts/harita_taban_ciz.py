#!/usr/bin/env python3
# LiDAR 0.182 m yukseklikte; masa taban plakasi (0.56x0.56, 4 cm) goremiyor.
# Bilinen masa koordinatlarina taban plakalarini elle ciziyoruz.
# Yollar paket-goreli: baska makinede de calisir.
import os
import sys
import rospkg

MAPS  = os.path.join(rospkg.RosPack().get_path('cafe_service_robot'), 'maps')
GIRIS = os.path.join(MAPS, 'kafe_ham.pgm')
CIKIS = os.path.join(MAPS, 'kafe_servis.pgm')
YAML  = os.path.join(MAPS, 'kafe_servis.yaml')
RES = 0.05
OX, OY = -15.0, -15.0
YARI = 0.28          # taban 0.56 m -> yaricap 0.28 m

MASALAR = [
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
]

def pgm_oku(yol):
    with open(yol, 'rb') as f:
        if f.readline().strip() != b'P5':
            sys.exit('P5 formatinda degil')
        s = f.readline()
        while s.startswith(b'#'):
            s = f.readline()
        w, h = map(int, s.split())
        maxv = int(f.readline())
        return w, h, maxv, bytearray(f.read())

w, h, maxv, veri = pgm_oku(GIRIS)
R = int(round(YARI / RES))          # 5 piksel -> 11x11 kare = 0.55 m
print('harita %dx%d, her masaya %dx%d piksel taban ciziliyor' % (w, h, 2*R+1, 2*R+1))

for ad, mx, my in MASALAR:
    sut = int((mx - OX) / RES)
    sat = h - 1 - int((my - OY) / RES)
    if not (R <= sut < w-R and R <= sat < h-R):
        print('  %-14s HARITA DISI, atlandi' % ad)
        continue
    for dy in range(-R, R+1):
        for dx in range(-R, R+1):
            veri[(sat+dy)*w + (sut+dx)] = 0      # 0 = dolu (siyah)
    print('  %-14s cizildi  (%.3f, %.3f)' % (ad, mx, my))

with open(CIKIS, 'wb') as f:
    f.write(b'P5\n# masa taban plakalari elle eklendi\n')
    f.write(b'%d %d\n%d\n' % (w, h, maxv))
    f.write(bytes(veri))

with open(YAML, 'w') as f:
    f.write('image: %s\n' % os.path.basename(CIKIS))
    f.write('resolution: %f\n' % RES)
    f.write('origin: [%f, %f, 0.000000]\n' % (OX, OY))
    f.write('negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n')

print('\nyazildi: %s' % CIKIS)
print('yazildi: %s' % YAML)
