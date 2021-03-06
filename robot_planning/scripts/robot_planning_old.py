#!/usr/bin/python3

import rospy
import gpiozero

from std_msgs.msg import String
from std_msgs.msg import Bool
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32MultiArray

class RobotTrajectory():
    def __init__(self):
        rospy.init_node("scara_trajectory", anonymous=True)
        self.desired_joint_state_pub = rospy.Publisher("/desired_joint_states", JointState, queue_size=10)
        self.scara_home_pub = rospy.Publisher("/scara_home", Bool, queue_size = 10)
        self.angle_sub = rospy.Subscriber("/scara_angles", Float32MultiArray, self.callback_angle)
        self.joint_sub = rospy.Subscriber("/joint_states", JointState, self.callback)
        self.allowable_sub = rospy.Subscriber("/scara_move", Bool, self.boolcall)
        self.rate = rospy.Rate(0.25)
        
        self.ready = False
        self.cv_ready = False
        self.home_config = [2, 2, 2]
        self.current_joint_pos = []
        self.at_des_pos = False

    # Setting an empty array as the current joint
    # position, array given by the servos
    def callback(self, data):
        self.current_joint_pos = data.position
        self.rate.sleep()

    # Checking if the joint angles are
    # valid to be acted upon
    def boolcall(self, data):
        self.ready = data.data
        self.rate.sleep()

    # Setting an empty array as the array given by the
    # /scara_angles topic.
    # The method requires validation from /scara_move topic
    def callback_angle(self, data):
        if self.ready:
            bool_msg = Bool()
            bool_msg.data = False
            scara_home_pub.publish(bool_msg)
            
            # gets the data from the /scara_angles topic
            # uses the first three values in the list of six
            # give each value respective joint names
            # publish the data straight to desired_joint_state
            # move the arms into desired positions and when done
            # wait
            joint_msg = JointState()
            joint_msg.name = ["joint_1", "joint_3", "joint_4"]
            joint_msg.position = [data.data[0], data.data[1], data.data[2]]
            self.desired_joint_state_pub.publish(joint_msg)
            while not self.at_desired_pos([data.data[0], 0, data.data[1], data.data[2]]):
                pass

            # set a value for the prismatic joint
            # give the value a name "joint_2"
            # publish the prismatic joint value
            # move the prismatic joint down to pick up the box
            joint_msg.name = ["joint_2"]
            joint_msg.position = [3]
            self.desired_joint_state_pub.publish(joint_msg)
            while not self.at_desired_pos([data.data[0], joint_msg.position[0], data.data[1], data.data[2]]):
                pass

            # publish the values to grab onto the box
            # TODO: logic to grab the block refer to gpiozero library

            # publish the prismatic joint value
            # so that the prismatic joint moves back up
            joint_msg.name = ["joint_2"]
            joint_msg.position = [-3]
            self.desired_joint_state_pub.publish(joint_msg)
            while not self.at_desired_pos([data.data[0], joint_msg.position[0], data.data[1], data.data[2]]):
                pass

            # uses the second three values of the data from /scara_angles
            # moves the arms so that the arms are on top of the correct zone
            # publishes the values to move the arm
            joint_msg.name = ["joint_1", "joint_3", "joint_4"]
            joint_msg.position = [data.data[3], data.data[4], data.data[5]]
            self.desired_joint_state_pub.publish(joint_msg)
            while not self.at_desired_pos([data.data[0], 0, data.data[1], data.data[2]]):
                pass

            # lowers the arm to drop the box
            # publishes the values to lower the
            # prismatic joint
            joint_msg.name = ["joint_2"]
            joint_msg.position = [3]
            self.desired_joint_state_pub.publish(joint_msg)
            while not self.at_desired_pos([data.data[0], joint_msg.position[0], data.data[1], data.data[2]]):
                pass

            # TODO: logic to release the block refer to gpiozero library
            # releasing the grabber to drop the box
            
            # raises the arm up the prismatic joint
            # to get back into home configuration
            # publishes the value to raise the arm
            joint_msg.name = ["joint_2"]
            joint_msg.position = [-3]
            self.desired_joint_state_pub.publish(joint_msg)
            while not self.at_desired_pos([data.data[0], joint_msg.position[0], data.data[1], data.data[2]]):
                pass

            # moves the arm back to a set position
            # set by the variable home_config
            # publishes the values to move the arm to home_config position
            joint_msg.name = ["joint_1", "joint_3", "joint_4"]
            joint_msg.position = self.home_config
            self.desired_joint_state_pub.publish(joint_msg)
            while not self.at_desired_pos([self.home_config[0], 0, self.home_config[1], self.home_config[2]]):
                pass
            
            # when the arm is back at home_config
            # publish a boolean msg to tell the computer vision
            # node to start looking for the box again
            bool_msg = Bool()
            bool_msg.data = True
            scara_home_pub.publish(bool_msg)

        self.rate.sleep()

    def at_desired_pos(self, desired_pos):
        to_move = np.array(desired_pos)
        current_pos = np.array(self.current_joint_pos)
        error = to_move - current_pos
        if error[0] < 0.01 and error[1] < 0.01 and error[2] < 0.01 and error[3] < 0.01:
            return True
        return False

    def run(self):
        rate.sleep(3)
        rospy.spin()

if __name__ == '__main__':
        try:
            rt = RobotTrajectory()
            rt.run()
        except rospy.ROSInterruptionException:
            pass
