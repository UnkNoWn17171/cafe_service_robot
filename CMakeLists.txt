cmake_minimum_required(VERSION 3.0.2)
project(cafe_service_robot)

find_package(catkin REQUIRED COMPONENTS
  rospy
)

catkin_package()

#############
## Install ##
#############

# catkin_install_python, kurulum sirasinda shebang satirini hedef sistemin
# dogru python'una gore duzeltir; duz install() bunu yapmaz.
catkin_install_python(PROGRAMS
  scripts/servis_web.py
  scripts/dunya_listesi.py
  scripts/harita_izle.py
  scripts/harita_kontrol.py
  scripts/harita_masa_kontrol.py
  scripts/harita_taban_ciz.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

# Veri klasorleri: paket kopyalandiginda bunlar da gelsin.
install(DIRECTORY launch config maps urdf worlds templates
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
