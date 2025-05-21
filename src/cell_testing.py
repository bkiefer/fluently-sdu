import PIL.Image
import numpy as np
from numpy import ndarray
import cv2
import numpy as np
import matplotlib.pyplot as plt
import PIL
import spatialmath as sm
from gubokit import utilities
from robot_module import RobotModule
from vision_module import VisionModule
import time

R = sm.SO3([[-0.003768884463184431, -0.9999801870110973700,  0.0050419336721138118], 
            [0.9999374423980765800, -0.0038217260702308998, -0.0105121691499708400], 
            [0.0105312297618392200,  0.0050019991098505349,  0.9999320342926355500]])
t = np.array([0.051939876523448010, -0.0323596382860819900,  0.0211982932413351600])
E = sm.SE3.Rt(R, t)

over_pack_rotvec = [-0.3090592371772158, -0.35307448825989896, 0.4, -0.6206856204961252, 3.057875096728538, 0.00340990937801082]
over_ws_rotvec = [-0.2586273936588753, -0.3016785796195318, 0.18521682703909298, -0.5923558488917048, 3.063479683639857, 0.0030940693262241515]
discard_T =    sm.SE3([0.17079587302315735, -0.4873784390448619, 0.30675627062804295]) * sm.SE3.Rx(np.pi)
keep_T = sm.SE3([0.11790078219215322, -0.35906727516279763, 0.3022927460811224]) * sm.SE3.Rx(np.pi)

robot_module = RobotModule("192.168.1.100", [0, 0, 0, 0, 0, 0], tcp_length_dict={'small': -0.041, 'big': -0.08}, active_gripper='big', gripper_id=0)
robot_module.robot.moveL(over_pack_rotvec)
vision_module = VisionModule(camera_Ext=E) 

# ans= ''
# while ans != 'q':
    # frame = vision_module.get_current_frame()
    # ans = chr(0xff & cv2.waitKey(1))
    # cv2.imshow("frame", frame)

frame = vision_module.get_current_frame(wait_delay=1)
results = vision_module.classify_cell(frame, frame)
bbs = results['bbs']
zs = results['zs']

target_Ts = []
for _ in range(len(bbs)):
    if np.random.rand() < 0.5:
        target_Ts.append(keep_T)
        print("keep_T")
    else:
        target_Ts.append(discard_T)
        print("discard_T")

cv2.imshow("frame", frame)
# we need the position of the TCP WHEN THE PHOTO GET TAKEN
base_T_TCP = utilities.rotvec_to_T(robot_module.robot.getActualTCPPose())
for i, (bb, z, target_T) in enumerate(zip(bbs, zs, target_Ts)):
    cv2.waitKey(0)
    cell_T = vision_module.frame_pos_to_pose(frame_pos=bb, camera=vision_module.camera, Z=z, base_T_TCP=base_T_TCP)
    robot_module.pick_and_place(cell_T, target_T)