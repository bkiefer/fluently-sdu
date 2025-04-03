from vision_module import VisionModule
from robot_module import RobotModule
import spatialmath as sm
import numpy as np
import cv2
from gubokit import utilities

robot_module = RobotModule("192.168.1.100", [0, 0, 0, 0, 0, 0], gripper_id=0)
vision_module = VisionModule(camera_Ext=sm.SE3([0,0,0]))
over_ws_pose = [-0.25459073314393055, -0.3016784540487311, 0.2547053979663029, -0.5923478428527734, 3.063484429352879, 0.003118486651508924]
pack_T = sm.SE3([-0.2957, -0.3202, 0.149]) * sm.SE3.Rx(np.pi)
bin_T = sm.SE3([-0.03655, -0.5088, 0.20]) * sm.SE3.Rx(np.pi)
cell_T = sm.SE3([-0.2968, -0.3108, 0.15]) * sm.SE3.Rx(np.pi)
robot_module.robot.moveL(over_ws_pose)
# robot_module.robot.teachMode()
robot_module.robot.endTeachMode()

while True:
    frame = vision_module.get_current_frame(wait_delay=0)
    ans = chr(0xff & cv2.waitKey(1))
    if ans == 'q':
        break
    elif ans == '1':
        pack_data = vision_module.locate_pack(frame)
        if pack_data is not None:
            pt1 = (pack_data['location'][0] - pack_data['size'][0]//2, pack_data['location'][1] - pack_data['size'][1]//2)
            pt2 = (pack_data['location'][0] + pack_data['size'][0]//2, pack_data['location'][1] + pack_data['size'][1]//2)
            cv2.rectangle(frame, pt1, pt2, (0, 255, 0), 3)
            cv2.putText(frame, (str(pack_data['shape'])), (pt1[0], pt1[1]), cv2.FONT_HERSHEY_SIMPLEX,  2, (255, 0, 0), 1)
    elif ans == '2':
        # print(utilities.rotvec_to_T(robot_module.robot.getActualTCPPose()))
        robot_module.pick_and_place(pack_T, bin_T)
        robot_module.robot.moveL(over_ws_pose)
    elif ans == '3':
        cells_results = vision_module.cell_detection(frame)
    elif ans == '4':
        # print(utilities.rotvec_to_T(robot_module.robot.getActualTCPPose()))
        robot_module.pick_and_place(cell_T, bin_T)
        robot_module.robot.moveL(over_ws_pose)
    elif ans == '5':
        print(utilities.rotvec_to_T(robot_module.robot.getActualTCPPose()))
    try:
        cv2.rectangle(frame, pt1, pt2, (0, 255, 0), 3)
        cv2.putText(frame, (str(pack_data['shape'])), (pt1[0], pt1[1]), cv2.FONT_HERSHEY_SIMPLEX,  2, (255, 0, 0), 1)
    except:
        pass
    try:
        if len(cells_results) != 0:
                for (x, y, r) in cells_results:
                    cv2.circle(frame, (x, y), 1, (0, 100, 100), 3)
                    cv2.circle(frame, (x, y), r, (255, 0, 255), 3)
    except:
        pass
    cv2.imshow("Frame", frame)
