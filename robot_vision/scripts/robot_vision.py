#!/usr/bin/python

import rospy
import tf

from geometry_msgs.msg import Transform
from tf2_msgs.msg import TFMessage
from std_msgs.msg import String
from std_msgs.msg import Bool
from fiducial_msgs.msg import FiducialTransform

import modern_robotics as mr
import numpy as np

# TODO: Check if the AruCo markers have stopped moving
# TODO: Check which AruCo marker transforms are valid (e.g. still on unpicked.)
# TODO: Check which AruCo marker is on the right side of the table
# TODO: Publish (x, y, z, theta, phi, psi) realtive to space frame to topic

class RobotVision():
    def __init__(self):
        rospy.init_node("scara_cv", anonymous=True)
        self.block_transform_pub = rospy.Publisher("block_transform", FiducialTransform, queue_size=10)
        self.block_ready_pub = rospy.Publisher("block_ready", String, queue_size=10)
        self.fid_transform_sub = rospy.Subscriber("/fiducial_transforms", FiducialTransform, self.callback)
        self.scara_home_sub = rospy.Subscriber("/scara_home", Bool, self.ready_callback)
        self.listner = tf.TransformListener()
        self.rate = rospy.Rate(1)

        self.ready_msg = String() # Used to tell robot_kinematics that transform frame is a valid pickup location 
        self.tf_msg = FiducialTransform() # Used to send the transform frame of block
        # TODO: Get actual measurements and orientation for this transform
        self.Tbase_cam = np.array([
                                        [1, 0, 0, 0.1],
                                        [0, 1, 0, 0.0],
                                        [0, 0, 1, 0.5],
                                        [0, 0, 0, 1.0]
                                  ])
        self.old_distance = 0
        self.motion_stopped = False
        self.robot_ready = False 
        pass

    def ready_callback(self, data):
        self.robot_ready = data.data
        pass

    def callback(self, data):
        # rospy.loginfo(data.transforms) # data.transforms -> list()
        try:
            if (len(data.transforms)) and self.robot_ready:
                (trans, rot)  = self.listner.lookupTransform("/0", 
                        f"/fiducial_{data.transforms[0].fiducial_id}", rospy.Time(0))
                # Check if a block is still moving
                if not is_moving(trans):
                    (fid_id, trans, rot) = self.find_block_transform(data)
                    self.update_tf_msg(fid_id, trans, rot)
                    self.pub.publish(self.tf_msg)
                    pass
                
                rospy.loginfo(data.transforms[0].fiducial_id)
                rospy.loginfo(dist)
                pass
            else:
                pass
        except tf.LookupException as LE:
            rospy.loginfo(LE)
            pass
        except tf.ConnectivityException as CE:
            rospy.loginfo(CE)
            pass
        pass

    def run(self):
        rospy.sleep(3)
        rospy.spin()
        pass

    def marker_distance(trans: list)->float:
        pos = np.array([trans[0], trans[1], trans[2]])
        return np.linalg.norm(pos)
        pass

    def is_moving(self, trans:list)->bool:
        if not self.motion_stopped:
            dist = self.marker_distance(trans)
            if dist == self.old_distance:
                self.motion_stopped = True
                result = True
            else:
                self.old_distance = dist
                result = False
        else:
            result = False

        rospy.sleep(1) # TODO: Might have to use a counter method instead of sleep
        return result
        pass

    def find_block_transform(self, data)->tuple:
        fiducials = {}
        max_dist_id = None 
        max_dist = 0
        # TODO: Will change this algo to be less random when Tbase_cam is defined
            # It will check for the position of the block on the robot side of the rotating plate 
            # And return transforms for it if found
        for tf in data.transforms:
            fid_id = tf.fiducial_id
            (trans, rot)  = self.listner.lookupTransform("/0", 
                    f"/fiducial_{fid_id}", rospy.Time(0))
            curr_dist = marker_distance(trans)
            if curr_dist > max_dist:
                max_dist = curr_dist
                max_dist_id = fid_id
            pass
        (trans, rot)  = self.listner.lookupTransform("/0", 
                f"/fiducial_{max_dist_id}", rospy.Time(0))
        return (max_dist_id, trans, rot)
        pass

    def find_block_transform(self, data)->tuples:
        fiducials = {}
        max_dist_id = None
        max_dist = 0
        for tf in data.transforms:
            fid_id = tf.fiducial_id
            (trans, rot) = self.listner.looupTransform("/0", f"/fiducial_{fid_id}", rospy.Time(0))
            Rcam_block = self.rotation_matrix(rot)
            Pcam_block = np.array([
                                    [trans[0]],
                                    [trans[1]],
                                    [trans[2]]
            ])
            Tcam_block = np.block([
                                    [Rcam_block , Pcam_block],
                                    [0, 0, 0, 1]
                                  ])
            Tbase_block = self.Tbase_cam @ Tcam_block
            curr_dist = marker_distance(trans)
        pass

    def rotation_matrix(self, rotation)->np.array:
        # Rotation in radians
        theta_x = rotation[0]
        theta_y = rotation[1]
        theta_z = rotation[2]

        rx = np.array([
                            [1, 0, 0],
                            [0, np.cos(theta_x), -np.sin(theta_x)],
                            [0, np.sin(theta_x), np.cos(theta_x)]
        ])
        ry = np.array([
                            [np.cos(theta_y), 0, np.sin(theta_y)],
                            [0, 1, 0],
                            [-np.sin(theta_y), 0, np.cos(theta_y)]
        ])
        rz = np.array([
                            [np.cos(theta_z), -np.sin(theta_z), 0],
                            [np.sin(theta_z), np.cos(theta_z), 0],
                            [0, 0, 1]
        ])
        return rz @ ry @ rx
        pass

if __name__ == "__main__":
    try:
        rv = RobotVision()
        rv.run()
        pass
    except rospy.ROSInterruptException:
        pass
    pass
