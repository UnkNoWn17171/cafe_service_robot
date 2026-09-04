# Kafe Servis Robotu

ROS Noetic + Gazebo Classic 11 ortaminda calisan otonom kafe servis robotu.
TurtleBot3 Burger tabanina tepsi ve dikey kol eklenmis; 11 masaya, tezgaha ve
sarj istasyonuna web arayuzunden verilen emirlerle otonom olarak gidiyor.

Konya Teknik Universitesi, Elektrik-Elektronik Muhendisligi.
RAC-Lab 
Demo videosu: https://github.com/UnkNoWn17171/cafe_service_robot/releases/latest


---

## 1. Ne yapiyor

- Sabit bir haritada AMCL ile konumlaniyor, move_base ile rota planliyor.
- Tarayicidan gelen masa emirlerini bir kuyruga alip sirayla isliyor.
- Emir yoksa once tezgaha, orada da emir gelmezse sarj istasyonuna donuyor.
- Calisan bir gorevi tarayicidan iptal edebiliyor; iptal hem gorev dongusunu
  hem move_base hedefini durduruyor.

## 2. Gereksinimler

| Bilesen | Surum |
|---|---|
| Ubuntu | 20.04.6 LTS |
| ROS | Noetic |
| Gazebo | Classic 11 |
| Python | 3.8 |
| Flask | 1.1.1 (apt: python3-flask) |

Bagimliliklar package.xml icinde tanimli; kurulum icin:

    cd ~/catkin_ws
    rosdep install --from-paths src --ignore-src -r -y

> Dunya dosyasi Gazebo model veritabanindan cafe, cafe_table ve
> control_console modellerini cagirir. Bunlar ~/.gazebo/models altinda
> yoksa Gazebo ilk acilista indirmeye calisir; internet yoksa dunya
> eksik acilabilir.

## 3. Kurulum

    cd ~/catkin_ws/src
    git clone https://github.com/UnkNoWn17171/cafe_service_robot.git
    cd ~/catkin_ws
    catkin_make
    source devel/setup.bash

~/.bashrc icine (yoksa ekleyin):

    export TURTLEBOT3_MODEL=burger
    source ~/catkin_ws/devel/setup.bash

## 4. Calistirma

    roslaunch cafe_service_robot servis_demo.launch

Tek komut sunlari ayaga kaldirir:

1. Gazebo + worlds/kafe.world + robotun dogmasi
2. robot_state_publisher (govde tf agaci)
3. map_server + amcl + move_base
4. RViz
5. Flask web arayuzu

Ardindan tarayicidan: **http://localhost:5000**

Kapatmak icin terminale **tek kez** Ctrl+C. Surec kendi kendine kapanir;
ikinci Ctrl+C gerekmez.

> Ayni launch dosyasi calisirken ikinci bir kopyasini baslatmayin. ROS ayni
> isimli node'u gorunce eskisini oldurur; ekrani anlamsiz hata yagmuru kaplar.
> Kontrol: pgrep -af gzserver

## 5. Web arayuzu

13 konum butonu (Masa 1-11, Tezgah, Sarj) + 1 iptal butonu. Ust kisimda
robotun anlik asamasi 1 saniyelik polling ile guncellenir; alt satir son
kullanici eylemini (emir gonderildi / iptal edildi) gosterir.

| Adres | Metot | Isi |
|---|---|---|
| / | GET | Arayuz sayfasi |
| /emir | POST | {"hedef": "Masa 3"} -> kuyruga ekler |
| /iptal | POST | Hedefi ve kuyrugu temizler |
| /durum | GET | {"asama": ..., "mesaj": ...} |

## 6. Mimari

    [Tarayici] --POST /emir--> [Flask thread] --put()--> [queue.Queue]
                                                              |
                                                           get()
                                                              v
                                                  [gorev dongusu thread'i]
                                                              |
                                                        send_goal()
                                                              v
                                                        [move_base] -> robot

    [Tarayici] --GET /durum (1 sn)--> [Flask] --> durum sozlugu
    [Ana thread] --> rospy.spin()

Uc thread var: ana thread rospy.spin() ile kapanma sinyalini bekler,
Flask sunucusu ve gorev dongusu daemon thread olarak calisir.

## 7. Gorev durum makinesi

Kodun cekirdegi **yerim** degiskeni. Robotun fiziksel konumunu degil,
**dongunun bir sonraki turda ne kadar bekleyecegini** belirler:

| yerim | Bekleme | Sure dolunca |
|---|---|---|
| "Tezgah" | 45 sn | Sarja doner |
| "Yolda" | 10 sn | Tezgaha doner |
| "Sarj" | Suresiz | - |

Uretici kural: yerim yalnizca git() True dondugunde bir konum adi alir.
False dondugu her durumda "Yolda" olur:

    yerim = "Tezgah" if git("Tezgah") else "Yolda"

"Yolda", "kod robotun nerede oldugunu bilmiyor" durumunun adidir.
Bilinmeyen durumun da bir ismi olmak zorundadir.

## 8. Tasarim kararlari

**Harita nasil uretildi.**
Lazer 0.182 m yukseklikte tariyor; masa taban plakasi 4 cm yuksekliginde
(0.56 x 0.56 m). Lazer plakayi hic gormuyor, dolayisiyla gmapping masa
ayaklarini haritaya isleyemiyor. Cozum: scripts/harita_taban_ciz.py ile bilinen
masa koordinatlarina taban plakalari haritaya cizildi.
scripts/harita_masa_kontrol.py her masanin cevresinin haritalandigini sayisal
olarak dogruluyor.

**minimumScore: 10000 (gmapping).**
Scan eslestirmeyi tamamen kapatir. Gerekce: TurtleBot3'un Gazebo diff_drive
eklentisi odometrySource=world ile ground-truth odometri veriyor
(turtlebot3_burger.gazebo.xacro), yani lazer duzeltmesi sadece gurultu
ekliyordu. **Gercek robotta asla yapilmaz** - simulasyona ozel bir ayardir.

**inflation_radius: 0.35 (stok 1.0).**
Kafede masa araliklari ~2.8 m. 1.0 m sisme yaricapi koridorlari tamamen
kapatiyordu; global costmap RViz'de bastan asagi kirmiziydi ve planlayici
rota bulamiyordu.

**xy_goal_tolerance: 0.20 (stok 0.05).**
Robot hedefin 5 cm'ine giremeyip yerinde tepiniyor, sonunda ABORTED veriyordu.

**Neden Flask, neden rosbridge degil.**
Gorev mantigi (13 konum, kuyruk, durum makinesi) zaten Python/rospy icinde.
Flask ile iki amaca ozel adres acip mevcut action istemcisini oldugu gibi
kullandim. rosbridge, tarayicinin ham ROS mesajlasmasi yapmasi gerektiginde
avantajli; sabit sayida buton icin daha az yeni parca gerektiren yol Flask.

**Neden launch-prefix yok.**
Onceden `bash -c 'sleep 15; $0 $@'` vardi. Araya bash girince Ctrl+C bash'i
olduruyor, python oksuz kalip 5000 portunu tutmaya devam ediyordu
(OSError: [Errno 98] Address already in use). Gazebo beklemesini zaten
istemci.wait_for_server() yapiyor. Kural: kaynak tutan (port, dosya, cihaz)
bir node'a launch-prefix konmaz.

**Neden app.run() ana thread'de degil.**
rospy.init_node() SIGINT'i yakalayip yalnizca bir kapanma bayragi kaldirir.
Ana thread'i app.run() tutarsa o bayragi kimse gormez, roslaunch sonunda
SIGKILL'e cikar ve port acikta kalir. Bayragi goren rospy.spin() ana
thread'de olmalidir.

## 9. Olculen sonuclar

/move_base/result topic'inden dogrulandi (status: 2 = PREEMPTED, 3 = SUCCEEDED):

| Senaryo | Sonuc |
|---|---|
| Masaya giderken iptal -> 10 sn bekle -> tezgaha don | Gecti |
| Iptal sonrasi yeni emir yutuluyor mu | Yutulmuyor |
| Iptal move_base'e ulasiyor mu | status: 2 olculdu |
| Ctrl+C sonrasi temiz kapanis | Surec ve port serbest |

Ekranda "iptal edildi" yazmasi ispat degildir; ispat karsi taraftan
(move_base) gelen bildirimdedir.

## 10. Paket yapisi

    cafe_service_robot/
    ├── launch/
    │   ├── servis_demo.launch      # ANA: Gazebo + nav + rviz + web
    │   ├── spawn_servis.launch     # Gazebo + robot
    │   ├── kafe_navigation.launch  # map_server + amcl + move_base
    │   └── kafe_mapping.launch     # gmapping (haritayi ureten)
    ├── templates/index.html        # web arayuzu
    ├── config/
    │   ├── gmapping_kafe.yaml      # SLAM ayarlari
    │   └── costmap_kafe.yaml       # TB3 varsayilanlarinin uzerine yazilir
    ├── maps/kafe_ham.* -> kafe_servis.*  # 576x576 @ 0.05 m/px, origin [-15,-15,0]
    ├── urdf/servis_robot.urdf.xacro
    ├── worlds/kafe.world
    └── scripts/                    # web arayuzu + yardimci scriptler
        ├── servis_web.py           # Flask arayuzu + gorev dongusu
        ├── harita_taban_ciz.py     # masa taban plakalarini haritaya cizer
        ├── harita_masa_kontrol.py  # masa cevresi haritalanmis mi
        ├── harita_kontrol.py       # map <-> Gazebo ortusme olcumu
        ├── harita_izle.py          # surerken sapma olcumu
        └── dunya_listesi.py        # Gazebo modellerini x/y/yaw basar

config/costmap_kafe.yaml move_base node'unda **en son** yuklenir, boylece
TurtleBot3'un varsayilanlarini ezer. Dosya ic ice yazilmistir
(global_costmap:, local_costmap:, DWAPlannerROS:), bu yuzden ns= argumani
gerekmez.

## 11. Bilinen sinirlar

- rospy.sleep(BEKLEME_MASA) iptale duyarsiz: masada 7 sn beklerken gelen
  iptal 7 sn'ye kadar gecikebilir. Robot zaten duruyor oldugu icin gorunur
  bir etkisi yok.
- Iptalden hemen sonra yeni hedef gonderilirse actionlib
  "Got a transition callback on a goal handle that we're not tracking"
  hatasi basiyor. Akis etkilenmiyor; duzeltmesi stop_tracking_goal()
  ancak get_state() sorgusunu bozma riski tasidigi icin dokunulmadi.
- URDF'te tepsi icin `<collision>` tanimi yok; Gazebo'da tepsi hicbir seye
  carpmiyor. Costmap footprint'i de stok TurtleBot3 degerlerinde.
- Web arayuzu VM'in libvirt NAT agindan disari acilmiyor. Ayni ag disindan
  erisim icin host makinede port yonlendirme gerekir.
- Acilista URDF ayristiricisi "multiple inconsistent `<name>`" uyarisi basiyor:
  govde materyalleri stok TurtleBot3 tanimindan sonra Gazebo/White ile
  eziliyor. Kasitli; gorsel disinda etkisi yok.
- move_base robot Gazebo'da dogmadan once ayaga kalktigi icin bir kez
  "Timed out waiting for transform from base_footprint to map" basiyor.
  Robot dogunca tf agaci kuruluyor, akis etkilenmiyor.
- Costmap konfigurasyonunda plugins listesi tanimli degil; move_base
  pre-Hydro varsayilanlarina (static + obstacle + inflation) duserek
  calisiyor. Ihtiyac duyulan katmanlar zaten bunlar.
- Flask gelistirme sunucusu kullaniliyor. Simulasyon demosu icin yeterli;
  gercek dagitimda WSGI sunucusu (waitress/gunicorn) gerekir.
