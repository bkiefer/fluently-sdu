from gubokit import robotics
import numpy as np
from numpy import ndarray
import spatialmath as sm
from scipy.spatial.transform import Rotation
import time

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
        # self.robot.pick_and_place(pick_pose=np.hstack((pick_T.t, Rotation.as_rotvec(Rotation.from_matrix(pick_T.R)))), 
                                #   place_pose=np.hstack((place_T.t, Rotation.as_rotvec(Rotation.from_matrix(place_T.R)))))
        time.sleep(1)

    def frame_to_world(self, frame_pos:ndarray) -> sm.SE3:
        """convert a position in the frame into a 4x4 pose in world frame

        Args:
            frame_pos (ndarray): position in the frame

        Returns:
            sm.SE3: 4x4 pose in world frame
        """
        pose = sm.SE3()
        return pose
    
    def grab(self):
        self.robot.close_gripper()
    
    def release(self):
        self.robot.open_gripper()

if __name__ == "__main__":
    robot_module = RobotModule("192.168.1.100", [0,0,0,0,0,0], gripper_id=0)

    # print(robot_module.robot.getActualTCPPose())
    # pose = sm.SE3.Rt(sm.SO3.EulerVec(robot_module.robot.getActualTCPPose()[3:]), robot_module.robot.getActualTCPPose()[:3])
    # print(pose)
    # print((robot_module.robot.getActualQ()))
    # robot_module.robot.moveL([-0.3, -0., 0.48, 1.15, -2.92, 0])
    robot_module.robot.moveJ([0.330, -1.577, 2.448, -2.428, -1.556, 4.648],  0.3, 0.3)
    input(">>>")
    robot_module.robot.close_gripper()
    input(">>>")
    robot_module.robot.open_gripper()

    