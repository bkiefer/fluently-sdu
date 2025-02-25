from gubokit import robotics
import numpy as np
from numpy import ndarray
import spatialmath as sm
from scipy.spatial.transform import Rotation

class RobotModule:
    def __init__(self, ip: str, home_position: ndarray):
        self.robot = robotics.Robot(ip=ip, home_jpos=home_position)
        self.gripper = robotics.VacuumGripper(self.robot, 1) # find correct id
        self.robot.add_gripper(gripper=self.gripper)
        # print("Starting robot module")

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
    
    def grab(self):
        self.robot.close_gripper()
    
    def release(self):
        self.robot.open_gripper()

if __name__ == "__main__":
    robot_module = RobotModule("192.168.1.100", [0,0,0,0,0,0])
    # print(robot_module.robot.getActualTCPPose())
    # pose = sm.SE3.Rt(sm.SO3.EulerVec(robot_module.robot.getActualTCPPose()[3:]), robot_module.robot.getActualTCPPose()[:3])
    # print(pose)
    # print((robot_module.robot.getActualQ()))
    # robot_module.robot.moveL([-0.3, -0., 0.48, 1.15, -2.92, 0])
    robot_module.robot.move_to_cart_position(sm.SE3([0, -0.3, 0.4]) * sm.SE3.Rx(180, unit='deg'))
    robot_module.robot.close_gripper()
    print(robot_module.robot.get_gripper_status())
    robot_module.robot.open_gripper()
    print(robot_module.robot.get_gripper_status())

    