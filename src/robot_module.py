from gubokit import robotics
import numpy as np
from numpy import ndarray
import spatialmath as sm
from scipy.spatial.transform import Rotation
import time
from gubokit import utilities

class RobotModule:
    def __init__(self, ip: str, home_position: ndarray, gripper_id=0):
        try:
            self.robot = robotics.Robot(ip=ip, home_jpos=home_position)
            self.gripper = robotics.VacuumGripper(self.robot, gripper_id) # find correct id
            self.robot.add_gripper(gripper=self.gripper)
            print("Starting robot module")
        except RuntimeError:
            self.robot = None
            print("The robot could not be started, the module will run for debug purpose")

    def pick_and_place(self, pick_T: sm.SE3, place_T: sm.SE3):
        """pick and place an object 

        Args:
            pick_T (sm.SE3): position and orientation for pick
            place_T (sm.SE3): position and orientation for place
        """
        try:
            self.robot.pick_and_place(pick_pose=np.hstack((pick_T.t, Rotation.as_rotvec(Rotation.from_matrix(pick_T.R)))), 
                                    place_pose=np.hstack((place_T.t, Rotation.as_rotvec(Rotation.from_matrix(place_T.R)))))
        except AttributeError:
            print("The robot cannot be accessed running for debug purpose")
            time.sleep(1)
    
    def move_to_cart_pos(self, T, speed=0.1):
        try:
            self.robot.move_to_cart_pose(T, speed)
        except AttributeError:
            print("The robot cannot be accessed running for debug purpose")
            time.sleep(1)

    def grab(self):
        self.robot.close_gripper()
    
    def release(self):
        self.robot.open_gripper()

if __name__ == "__main__":
    robot_module = RobotModule("192.168.1.100", [0, 0, 0, 0, 0, 0], gripper_id=0)
    over_pack_T = sm.SE3([-0.28, -0.24, 0.18]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(156.796, "deg")
    discard_T = sm.SE3([-0.247, -0.575, 0.15]) * sm.SE3.Rx(np.pi)
    keep_T =    sm.SE3([-0.106, -0.518, 0.15]) * sm.SE3.Rx(np.pi)
    cell_T_1 = (sm.SE3([-0.2949, -0.2554, 0.110]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(156.796, "deg"))
    cell_T_2 = (sm.SE3([-0.281, -0.288, 0.110]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(156.796, "deg"))
    
    print(robot_module.robot.getActualTCPPose())
