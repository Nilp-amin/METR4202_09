#!/usr/bin/python3

import rospy
import math
import pigpio
import os

from std_msgs.msg import Bool
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32MultiArray


class RobotTrajectory():
    """
    A class to represent the movement of servos given specific joint angles
    """    
    def __init__(self):
        """
        Constructs all the necessary attributes for RobotTrajectory object
        """        
        rospy.init_node("scara_trajectory", anonymous=True)
        self.desired_joint_state_pub = rospy.Publisher("/desired_joint_states", JointState, queue_size=1)
        self.scara_home_pub = rospy.Publisher("/scara_home", Bool, queue_size = 1)
        self.joint_sub = rospy.Subscriber("/scara_angles", Float32MultiArray, self.ik_joints_callback, queue_size=1)
        self.rate = rospy.Rate(2)

        # Setup gripper
        self.gripper_pin = 17
        self.drop_gripper_pos = 1400
        self.grab_gripper_pos = 700
        self.gripper = pigpio.pi()
        self.search_postion = [math.pi/2, 2.6, 0, 0] 
        self.wait_time = 5
        self.prismatic_wait_time = 3

    def ik_joints_callback(self, joint_angles):
        """
        Function that is called when data is published to /scara_angles
        Logic involved with trajectory planning and picking up and moving blocks
        Publishes to joint angles to servos on robot /desired_joint_states
        Publishes True when robot has returned to home configuration and is ready for more angles

        Args:
            joint_angles (std_msgs/Float32MultiArray): Array of 6 angles (theta1, theta3, theta4, theta1, theta3, theta4)
                                                        where first three are joint angles for picking up block and last three for 
                                                        placing block
        """
        # Extract pickup angles from message
        pickup_theta_1 = joint_angles.data[0]
        pickup_theta_2 = -self.search_postion[1]
        pickup_theta_3 = joint_angles.data[1]
        pickup_theta_4 = joint_angles.data[2]

        # Extract dropoff angles from message
        dropoff_theta_1 = joint_angles.data[3]
        dropoff_theta_2 = self.search_postion[1]
        dropoff_theta_3 = joint_angles.data[4]
        dropoff_theta_4 = joint_angles.data[5]

        # First publish that the robot is moving to target
        scara_home_msg = Bool()
        scara_home_msg.data = False 
        self.scara_home_pub.publish(scara_home_msg)

        # First move directly above the block
        joint_msg = JointState()
        joint_msg.name = ["joint_1", "joint_3", "joint_4"]
        joint_msg.position = [pickup_theta_1, pickup_theta_3, pickup_theta_4]
        joint_msg.velocity = [2, 2, 2]
        self.desired_joint_state_pub.publish(joint_msg)
        rospy.sleep(self.wait_time)

        # Now lower the gripper onto the block
        joint_msg.name = ["joint_2"]
        joint_msg.position = [pickup_theta_2]
        joint_msg.velocity = [2]
        self.desired_joint_state_pub.publish(joint_msg)
        rospy.sleep(self.prismatic_wait_time)
        self.gripper.set_servo_pulsewidth(self.gripper_pin, self.grab_gripper_pos)

        # Move gripper above collision zone
        joint_msg.name = ["joint_2"]
        joint_msg.position = [dropoff_theta_2]
        joint_msg.velocity = [2]
        self.desired_joint_state_pub.publish(joint_msg)
        rospy.sleep(self.prismatic_wait_time)

        # Move robot to drop off zone
        joint_msg.name = ["joint_1", "joint_3", "joint_4"]
        joint_msg.position = [dropoff_theta_1, dropoff_theta_3, dropoff_theta_4]
        joint_msg.velocity = [2, 2, 2]
        self.desired_joint_state_pub.publish(joint_msg)
        rospy.sleep(self.wait_time)
        
        #Drop off block
        self.gripper.set_servo_pulsewidth(self.gripper_pin, self.drop_gripper_pos)
        
        # Move robot back to search position
        joint_msg.name = ["joint_1", "joint_2", "joint_3", "joint_4"]
        joint_msg.position = self.search_postion 
        joint_msg.velocity = [2, 1, 2, 2]
        self.desired_joint_state_pub.publish(joint_msg)
        rospy.sleep(self.prismatic_wait_time)

        # publish that the robot is in search position
        scara_home_msg.data = True
        self.scara_home_pub.publish(scara_home_msg)
        

    def run(self):
        """
        Initialises robot to home config and runs spin() with a small sleep before hand to account for any errors
        """
        #Initialise to home config
        rospy.sleep(3)
        joint_msg = JointState()
        joint_msg.name = ["joint_1", "joint_2", "joint_3", "joint_4"]
        joint_msg.position = self.search_postion
        joint_msg.velocity = [2, 1, 2, 2]
        self.desired_joint_state_pub.publish(joint_msg)
        # Run
        rospy.spin()


if __name__ == "__main__":
    try:
        rt = RobotTrajectory()
        rt.run()
    except rospy.ROSInterruptionException:
        print("An error occurred running the Planning node.")
        pass

