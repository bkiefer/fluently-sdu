from gubokit import robotics
import numpy as np
from numpy import ndarray
import spatialmath as sm
from scipy.spatial.transform import Rotation
import time
from gubokit import utilities

class RobotModule:
    def __init__(self, ip: str, home_position: ndarray, tcp_length_dict, gripper_id=0, active_gripper="small"):
        try:
            self.robot = robotics.Robot(ip=ip, home_jpos=home_position)
            self.gripper = robotics.VacuumGripper(self.robot, gripper_id) # find correct id
            self.active_gripper = active_gripper
            self.tcp_length_dict = tcp_length_dict
            self.tcp_length = self.tcp_length_dict[self.active_gripper]
            self.robot.add_gripper(gripper=self.gripper)
            print("Starting robot module")
        except RuntimeError as e:
            self.robot = None
            print("The robot could not be started, the module will run for debug purpose")
            print(e)

    def change_gripper(self, active_gripper):
        self.active_gripper = active_gripper
        self.tcp_length = self.tcp_length_dict[self.active_gripper]

    def pick_and_place(self, pick_T: sm.SE3, place_T: sm.SE3):
        """pick and place an object 

        Args:
            pick_T (sm.SE3): position and orientation for pick
            place_T (sm.SE3): position and orientation for place
        """
        try:
            print(pick_T)
            actual_pick_T = pick_T * sm.SE3([0, 0, self.tcp_length])
            print(actual_pick_T)
            actual_place_T = place_T * sm.SE3([0, 0, self.tcp_length])
            self.robot.pick_and_place_contact(pick_pose=np.hstack((actual_pick_T.t, Rotation.as_rotvec(Rotation.from_matrix(actual_pick_T.R)))), 
                                    place_pose=np.hstack((actual_place_T.t, Rotation.as_rotvec(Rotation.from_matrix(actual_place_T.R)))))
        except AttributeError:
            print("The robot cannot be accessed running for debug purpose")
            time.sleep(1)
    
    def move_to_cart_pos(self, T, speed=0.1):
        actual_T = T * sm.SE3([0, 0, self.tcp_length])
        try:
            self.robot.move_to_cart_pose(actual_T, speed)
        except AttributeError:
            print("Move to cart pos debug")
            time.sleep(1)

    def grab(self):
        self.robot.close_gripper()
    
    def release(self):
        self.robot.open_gripper()

if __name__ == "__main__":
    robot_module = RobotModule("192.168.1.100", [0, 0, 0, 0, 0, 0], tcp_length_dict={'small': 0.041, 'big': 0.08}, active_gripper='small', gripper_id=0)
    over_pack_T = sm.SE3([-0.28, -0.24, 0.18]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(156.796, "deg")
    discard_T = sm.SE3([-0.247, -0.575, 0.15]) * sm.SE3.Rx(np.pi)
    discard_T =    sm.SE3([0.17079587302315735, -0.4873784390448619, 0.30675627062804295]) * sm.SE3.Rx(np.pi)
    keep_T =    sm.SE3([-0.106, -0.518, 0.15]) * sm.SE3.Rx(np.pi)
    keep_T = sm.SE3([0.11790078219215322, -0.35906727516279763, 0.3022927460811224]) * sm.SE3.Rx(np.pi)
    cell_T_1 = (sm.SE3([-0.2949, -0.2554, 0.110]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(156.796, "deg"))
    cell_T_2 = (sm.SE3([-0.281, -0.288, 0.110]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(156.796, "deg"))
    
    robot_module.robot.teachMode()
    while True:
        input(">>>")
        print(robot_module.robot.getActualTCPPose())
