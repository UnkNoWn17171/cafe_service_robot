#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kafe servis robotu: web arayuzu + gorev durum makinesi.

Flask sunucusu ve actionlib gorev dongusu ayri thread lerde calisir.
"""

import os
import queue
import threading

import actionlib
import rospkg
import rospy
from flask import Flask, jsonify, render_template, request
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from tf.transformations import quaternion_from_euler

# ======================= AYARLAR =======================
BEKLEME_SARJ  = 5.0      # acilista sarj istasyonunda bekleme (sn)
BEKLEME_MASA  = 7.0      # masada servis beklemesi (sn)
BOSTA_SINIR   = 45.0     # tezgahta emir beklerken sinir (sn)
BEKLEME_IPTAL = 10.0     # iptalden sonra durdugu yerde emir bekleme (sn)
HEDEF_SINIR   = 120.0    # tek hedefe gitmek icin sinir sure (sn)
TEPSI_ALMA    = 3.0      # tezgahta tepsi alma suresi (sn)
PORT          = 5000

KONUMLAR = {
    "Sarj":    ( 4.107,  8.581,  1.2660),
    "Tezgah":  (-0.226,  2.758, -2.2000),
    "Masa 1":  ( 0.677,  0.280, -1.5708),
    "Masa 2":  ( 3.523,  0.401, -1.5708),
    "Masa 3":  (-1.838, -2.437, -1.5708),
    "Masa 4":  ( 0.672, -2.367, -1.5708),
    "Masa 5":  ( 3.615, -2.322, -1.5708),
    "Masa 6":  (-1.784, -5.160, -1.5708),
    "Masa 7":  ( 0.833, -5.183, -1.5708),
    "Masa 8":  ( 3.682, -5.226, -1.5708),
    "Masa 9":  (-1.678, -8.137, -1.5708),
    "Masa 10": ( 0.910, -8.017, -1.5708),
    "Masa 11": ( 3.776, -7.937, -1.5708),
}
# =======================================================

emirler = queue.Queue()
iptal_bayragi = threading.Event()
durum = {'asama': 'Baslatiliyor...', 'mesaj': '-'}


def durum_yaz(metin):
    durum['mesaj'] = metin
    rospy.loginfo(metin)


def asama_yaz(metin):
    durum['asama'] = metin


def hedef_yap(ad):
    """Sozlukteki (x, y, yaw) degerini move_base'in anladigi pakete cevirir."""
    x, y, yaw = KONUMLAR[ad]
    g = MoveBaseGoal()
    g.target_pose.header.frame_id = "map"
    g.target_pose.header.stamp = rospy.Time.now()
    g.target_pose.pose.position.x = x
    g.target_pose.pose.position.y = y
    q = quaternion_from_euler(0.0, 0.0, yaw)
    g.target_pose.pose.orientation.x = q[0]
    g.target_pose.pose.orientation.y = q[1]
    g.target_pose.pose.orientation.z = q[2]
    g.target_pose.pose.orientation.w = q[3]
    return g


def git(ad):
    """Hedefe gonder ve varana kadar bekle. Basarili ise True doner.

    False dondugu her durumda robotun nerede oldugu belirsizdir;
    cagiran taraf yerim'i "Yolda" yapmak zorundadir.
    """
    if iptal_bayragi.is_set():          # iptal bekliyorsa hic gonderme
        return False
    asama_yaz("Gidiliyor: %s" % ad)
    istemci.send_goal(hedef_yap(ad))
    if not istemci.wait_for_result(rospy.Duration(HEDEF_SINIR)):
        istemci.cancel_goal()
        durum_yaz("ZAMAN ASIMI - %s" % ad)
        return False
    if iptal_bayragi.is_set():          # beklerken iptal geldiyse
        durum_yaz("Durduruldu")
        return False
    if istemci.get_state() == actionlib.GoalStatus.SUCCEEDED:
        durum_yaz("Varildi: %s" % ad)
        return True
    durum_yaz("ULASILAMADI: %s" % ad)
    return False


def gorev_dongusu():
    durum_yaz("move_base bekleniyor...")
    istemci.wait_for_server()
    durum_yaz("Hazir.")

    asama_yaz("Sarj istasyonunda, %d sn bekleniyor" % int(BEKLEME_SARJ))
    rospy.sleep(BEKLEME_SARJ)

    yerim = "Tezgah" if git("Tezgah") else "Yolda"

    while not rospy.is_shutdown():
        # --- 1) Neredeysem o kadar beklerim
        if yerim == "Tezgah":
            asama_yaz("Tezgahta emir bekleniyor (%d sn)" % int(BOSTA_SINIR))
            bekleme = BOSTA_SINIR
        elif yerim == "Yolda":
            asama_yaz("Durduruldu, emir bekleniyor (%d sn)" % int(BEKLEME_IPTAL))
            bekleme = BEKLEME_IPTAL
        else:                            # Sarj
            asama_yaz("Sarj istasyonunda, emir bekleniyor")
            bekleme = None               # None = suresiz bekle

        # --- 2) Emri bekle
        try:
            emir = emirler.get(timeout=bekleme)
        except queue.Empty:
            emir = None                  # sure doldu, emir gelmedi

        # --- 3) Bekleme bitti, eski iptal artik gecersiz
        iptal_bayragi.clear()

        # --- 4) Sure doldu: nereden bekliyorsam ona gore don
        if emir is None:
            if yerim == "Tezgah":
                durum_yaz("%d sn emir yok, sarja donuluyor" % int(BOSTA_SINIR))
                yerim = "Sarj" if git("Sarj") else "Yolda"
            else:                        # Yolda
                durum_yaz("%d sn emir yok, tezgaha donuluyor" % int(BEKLEME_IPTAL))
                yerim = "Tezgah" if git("Tezgah") else "Yolda"
            continue

        # --- 5) Elle basilan konum butonu
        if emir in ("Sarj", "Tezgah"):
            yerim = emir if git(emir) else "Yolda"
            continue

        # --- 6) Masa emri
        if yerim == "Sarj":
            asama_yaz("Tepsi almak icin tezgaha gidiliyor")
            if not git("Tezgah"):
                yerim = "Yolda"
                continue
            rospy.sleep(TEPSI_ALMA)

        if not git(emir):
            yerim = "Yolda"
            continue

        asama_yaz("%s - servis, %d sn bekleniyor" % (emir, int(BEKLEME_MASA)))
        rospy.sleep(BEKLEME_MASA)

        yerim = "Tezgah" if git("Tezgah") else "Yolda"


def dongu_sarmali():
    try:
        gorev_dongusu()
    except rospy.ROSInterruptException:
        pass


# ---------------------- ROS ----------------------
rospy.init_node('servis_web')
istemci = actionlib.SimpleActionClient('move_base', MoveBaseAction)

# ---------------------- FLASK ----------------------
# roslaunch node'un calisma dizinini ~/.ros yapar; templates/ orada degil.
# Mutlak yolu paketten aliyoruz.
paket = rospkg.RosPack().get_path('cafe_service_robot')
app = Flask(__name__, template_folder=os.path.join(paket, 'templates'))


@app.route('/')
def anasayfa():
    return render_template('index.html')


@app.route('/emir', methods=['POST'])
def emir_al():
    veri = request.get_json(silent=True) or {}
    hedef = veri.get('hedef')
    if hedef not in KONUMLAR:
        return jsonify({'ok': False, 'hata': 'bilinmeyen hedef'}), 400
    emirler.put(hedef)
    return jsonify({'ok': True, 'hedef': hedef, 'bekleyen': emirler.qsize()})


@app.route('/iptal', methods=['POST'])
def iptal_et():
    iptal_bayragi.set()
    istemci.cancel_all_goals()
    while not emirler.empty():
        try:
            emirler.get_nowait()
        except queue.Empty:
            break
    durum_yaz("IPTAL - hedef ve kuyruk temizlendi")
    return jsonify({'ok': True})


@app.route('/durum')
def durum_ver():
    return jsonify(durum)


# ---------------------- CALISTIRMA ----------------------
def web_sunucu():
    """Flask'i ayri thread'de calistirir.

    Ana thread'i app.run() tutarsa Ctrl+C sonrasi surec olmez:
    rospy.init_node SIGINT'i yakalayip sadece kapanma bayragini kaldirir,
    app.run() o bayragi hic gormez ve doner durur. Bayragi goren
    rospy.spin() ana thread'de olmali.
    """
    try:
        app.run(host='0.0.0.0', port=PORT,
                debug=False, use_reloader=False, threaded=True)
    except Exception as hata:
        # Sunucu ayaga kalkmadiysa node sessizce yasamasin.
        rospy.logerr("Web sunucu baslatilamadi: %s" % hata)
        rospy.signal_shutdown("web sunucu hatasi")


threading.Thread(target=dongu_sarmali, daemon=True).start()
threading.Thread(target=web_sunucu, daemon=True).start()
rospy.loginfo("Web arayuzu: http://localhost:%d" % PORT)
rospy.spin()
