#!/usr/bin/env python3
# Gazebo'daki tum modelleri isim + x, y, yaw olarak tek tabloda basar.
import math
import rospy
from gazebo_msgs.msg import ModelStates
from tf.transformations import euler_from_quaternion

rospy.init_node('dunya_listesi', anonymous=True)
m = rospy.wait_for_message('/gazebo/model_states', ModelStates)

print('%-24s %8s %8s %8s' % ('MODEL', 'x', 'y', 'yaw'))
for ad, p in zip(m.name, m.pose):
    o = p.orientation
    yaw = math.degrees(euler_from_quaternion([o.x, o.y, o.z, o.w])[2])
    print('%-24s %8.3f %8.3f %8.1f' % (ad, p.position.x, p.position.y, yaw))
