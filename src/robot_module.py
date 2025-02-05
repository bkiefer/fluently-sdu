from gubokit import robotics
import numpy as np
from numpy import ndarray
import spatialmath as sm
from scipy.spatial.transform import Rotation

class RobotModule:
    def __init__(self, home_position: ndarray):
        # self.robot = robotics.Robot(ip="192.168.1.1", home_jpos=home_position)
        # self.gripper = None # TODO: init gripper
        # self.robot.add_gripper(gripper=self.gripper)
        print("Starting robot module")

    def pick_and_place(self, pick_T: sm.SE3, place_T: sm.SE3):
        """pick and place an object 

        Args:
            pick_T (sm.SE3): position and orientation for pick
            place_T (sm.SE3): position and orientation for place
        """
        self.robot.pick_and_place(pick_pose=np.hstack((pick_T.t, Rotation.as_rotvec(Rotation.from_matrix(pick_T.R)))), 
                                  place_pose=np.hstack((place_T.t, Rotation.as_rotvec(Rotation.from_matrix(place_T.R)))))

    def frame_to_world(self, frame_pos:ndarray) -> sm.SE3:
        """convert a position in the frame into a 4x4 pose in world frame

        Args:
            frame_pos (ndarray): position in the frame

        Returns:
            sm.SE3: 4x4 pose in world frame
        """
        pose = sm.SE3()
        return pose