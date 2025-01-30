from gubokit import  robotics, ros, utilities
import rclpy
import numpy as np
import os
import spatialmath as sm
import time
from pathlib import Path

def main(args=None):
    rclpy.init(args=args)
    joint_publisher = ros.JointPublisher(topic_name='joint_states')
    pose_array_publisher = ros.PoseArrayPublisher(topic_name='poses')
    pose_array_publisher.send_poses([])
    
    robot_base = sm.SE3.Rt(np.eye(3), [-0.5, -0.3, 0.74])
    robot = robotics.SimRobotBackend(str(Path(__file__).parent.parent) + "/urdf/ur5e.urdf", tcp_frame_urdf="tool0", robot_base=robot_base)

    # T = sm.SE3([-0.05, 0.2, 0.84])
    # pose_array_publisher.send_poses(T)

    # input(">>>")
    robot.q = [0, 0, 0, 0, 0, np.pi]
    joint_publisher.send_joint(robot.q)
    
    # robot.set_joint_limit(1, (-1.2, 1.2))
    # robot.set_joint_limits_usage(True)
    
    pose_array_publisher.destroy_node()
    joint_publisher.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()