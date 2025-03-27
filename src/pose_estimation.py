from vision_module import VisionModule
from robot_module import RobotModule
import spatialmath as sm
import numpy as np
import cv2
from gubokit import utilities

robot_module = RobotModule(ip="192.168.1.100", home_position=[0, 0, 0, 0, 0, 0], gripper_id=0)
# robot_module.robot.move_to_cart_pose(sm.SE3([-0.4, -0.2, 0.6]) * sm.SE3.Rx(np.pi))

camera_Ext = sm.SE3([0.033, 0.055, -0.122])
vision_module = VisionModule(camera_Ext=camera_Ext)
frame = vision_module.get_current_frame()
cv2.imshow("frame", frame)
cv2.waitKey(0)

p = (0,0) # bolt on plastic black component for pose = sm.SE3([-0.4, -0.2, 0.6]) * sm.SE3.Rx(np.pi)
cell_h = 0.035

camera_pose = utilities.rotvec_to_T(robot_module.robot.getActualTCPPose()) * vision_module.camera.extrinsic # or viceversa
camera_z = camera_pose.t[2]
pos_3d = vision_module. frame_pos_to_3d(p, vision_module.camera, cell_heigth=cell_h, camera_z=camera_z)
print("POS 3d", pos_3d)
pose = sm.SE3(pos_3d)  * sm.SE3.Rx(np.pi)

print(pose)
pos_3d = (np.array([-0.442, -0.236, 0.035])) # position that we want from the algorithm, real position of the top of the black nut