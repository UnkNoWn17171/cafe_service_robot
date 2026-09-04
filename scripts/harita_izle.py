#!/usr/bin/env python3
# Harita ile Gazebo gercegi arasindaki sapmayi surekli olcer.
# Belirli bir hedefe gitmek gerekmez; serbest surus sonunda ozet basilir.
import math
import rospy
import tf
from gazebo_msgs.msg import ModelStates
from tf.transformations import euler_from_quaternion

rospy.init_node('harita_izle', anonymous=True)
d = tf.TransformListener()
d.waitForTransform('map', 'base_footprint', rospy.Time(0), rospy.Duration(10.0))

kayit = []
print("Olcum her saniye alinir. Bitirmek icin Ctrl+C.\n")

hiz = rospy.Rate(1)
try:
    while not rospy.is_shutdown():
        try:
            m = rospy.wait_for_message('/gazebo/model_states', ModelStates, timeout=2.0)
            i = m.name.index('servis_robot')
            p = m.pose[i]; o = p.orientation
            gx, gy = p.position.x, p.position.y
            gyaw = euler_from_quaternion([o.x, o.y, o.z, o.w])[2]

            (k, r) = d.lookupTransform('map', 'base_footprint', rospy.Time(0))
            myaw = euler_from_quaternion(r)[2]

            sapma = math.hypot(k[0]-gx, k[1]-gy)
            da = math.degrees(myaw - gyaw)
            if da > 180:  da -= 360
            if da < -180: da += 360

            kayit.append((gx, gy, sapma, abs(da)))
            print("  x=%7.3f y=%7.3f   sapma=%.3f m   aci=%5.2f derece" % (gx, gy, sapma, da))
        except Exception:
            pass
        hiz.sleep()
except (rospy.ROSInterruptException, KeyboardInterrupt):
    pass

if not kayit:
    print("\nHic olcum alinamadi.")
else:
    s = [x[2] for x in kayit]
    a = [x[3] for x in kayit]
    en_kotu = max(kayit, key=lambda x: x[2])
    print("\n" + "="*52)
    print("OLCUM SAYISI : %d" % len(kayit))
    print("SAPMA        ortalama %.3f m   en kotu %.3f m" % (sum(s)/len(s), max(s)))
    print("ACI          ortalama %.2f     en kotu %.2f derece" % (sum(a)/len(a), max(a)))
    print("EN KOTU YER  x=%.2f  y=%.2f" % (en_kotu[0], en_kotu[1]))
    print("="*52)
    if max(s) < 0.15 and max(a) < 3.0:
        print("SONUC: GECTI - koordinatlar guvenle kullanilabilir")
    elif max(s) < 0.30:
        print("SONUC: SINIRDA - kullanilabilir, servis mesafesi artirilmali")
    else:
        print("SONUC: KALDI - koordinatlar guvenilir degil, harita yeniden cikarilmali")
