from vision_module import VisionModule
from robot_module import RobotModule
import spatialmath as sm
import numpy as np
import cv2

robot_module = RobotModule("192.168.1.100", [0, 0, 0, 0, 0, 0], gripper_id=0)
vision_module = VisionModule(camera_Ext=sm.SE3([0,0,0]))

while True:
    frame = vision_module.get_current_frame(wait_delay=0)
    results = vision_module.cell_detection(frame)
    if len(results) != 0:
        for (x, y, r) in results:
            cv2.circle(frame, (x, y), 1, (0, 100, 100), 3)
            cv2.circle(frame, (x, y), r, (255, 0, 255), 3)
    cv2.imshow("Frame", frame)
    ans = chr(0xff & cv2.waitKey(1))
    if ans == 'q':
        break
    # elif ans == 'p':