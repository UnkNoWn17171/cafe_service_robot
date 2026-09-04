#!/usr/bin/env python3
# Haritanin Gazebo gercegiyle ortusmesini olcer.
import math
import rospy
import tf
from gazebo_msgs.msg import ModelStates
from tf.transformations import euler_from_quaternion

rospy.init_node('harita_kontrol', anonymous=True)

m = rospy.wait_for_message('/gazebo/model_states', ModelStates)
i = m.name.index('servis_robot')
p = m.pose[i]
o = p.orientation
gx, gy = p.position.x, p.position.y
gyaw = euler_from_quaternion([o.x, o.y, o.z, o.w])[2]

d = tf.TransformListener()
d.waitForTransform('map', 'base_footprint', rospy.Time(0), rospy.Duration(5.0))
(konum, donus) = d.lookupTransform('map', 'base_footprint', rospy.Time(0))
myaw = euler_from_quaternion(donus)[2]

dx, dy = konum[0] - gx, konum[1] - gy
da = math.degrees(myaw - gyaw)
if da > 180:  da -= 360
if da < -180: da += 360

print("GAZEBO  : x=%7.3f  y=%7.3f  yaw=%7.1f" % (gx, gy, math.degrees(gyaw)))
print("MAP(tf) : x=%7.3f  y=%7.3f  yaw=%7.1f" % (konum[0], konum[1], math.degrees(myaw)))
print("FARK    : dx=%6.3f dy=%6.3f  mesafe=%.3f m  aci=%.2f derece"
      % (dx, dy, math.hypot(dx, dy), da))
