from vision_module import VisionModule
from robot_module import RobotModule
import spatialmath as sm
import numpy as np

camera_Ext = sm.SE3([0.033, 0.055, -0.122])

vision_module = VisionModule(camera_Ext=camera_Ext)
robot_module = RobotModule(ip="192.168.1.100", home_position=[0, 0, 0, 0, 0, 0], gripper_id=0)

p = (822, 177)
cell_h = 0.035

camera_pose = robot_module.robot.getActualTCPPose() * camera_Ext # or viceversa
camera_z = camera_pose.t[2]
pos_3d = vision_module. frame_pos_to_3d(p, vision_module.camera, cell_heigth=cell_h, camera_z=camera_z)
pose = sm.SE3(pos_3d)  * sm.SE3.Rx(np.pi)