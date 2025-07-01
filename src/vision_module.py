import PIL.Image
import numpy as np
from numpy import ndarray
import cv2
import numpy as np
import matplotlib.pyplot as plt
import copy
import PIL
import time
import spatialmath as sm
from ultralytics import YOLO
from gubokit import vision
from gubokit import utilities
from robot_module import RobotModule
import os

class VisionModule():
    def __init__(self, camera_Ext: sm.SE3, verbose=False):
        # camera initialization
        console_level = 'debug' if verbose else 'info'
        self.logger = utilities.CustomLogger("Vision", "MeMVision.log", console_level=console_level, file_level=None)
        try:
            self.logger.info("Starting vision module")
            self.camera = vision.RealSenseCamera(extrinsic=camera_Ext,
                                                enabled_strams={
                                                'color': [1920, 1080],
                                                'depth': [640, 480],
                                                # 'infrared': [640, 480]
                                                })
        except:
            self.camera = None
            self.logger.warning("The vision module could not be started, the module will run for debug purpose")
        self.packs_yolo_model = YOLO("data/packs_best_model.pt")
        self.cells_yolo_model = YOLO("data/cells_best_model.pt")
        self.set_background()
        
    def set_background(self):
        self.logger.debug("Setting background")
        new_bg = self.get_current_frame()
        # cv2.imwrite("Background.jpg", new_bg)
        self.background = new_bg

    def get_current_frame(self, format="cv2", wait_delay=0) -> np.ndarray:
        """get the current frame from the camera
        Returns:
            np.ndarray: frame
        """
        time.sleep(wait_delay)
        try :
            frame = self.camera.get_color_frame()
        except AttributeError:
            # print("Cannot access camera. For debuggin purpose it will access a file in store")
            frame = cv2.imread("data/camera_frame1.png")
        if format.lower() == "pil":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
            frame = PIL.Image.fromarray(frame)
        return frame

    def get_z_at_pos(self, x, y):
        depth_frame = self.camera.get_depth_frame()
        depth_img = np.asanyarray(depth_frame.get_data())
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_img, alpha=100), cv2.COLORMAP_JET)
        # cv2.imshow("Depth Frame", depth_colormap)
        z = depth_frame.get_distance(x, y)
        return z

    def locate_pack(self, frame: ndarray):
        # result = self.packs_yolo_model(frame)
        result = self.packs_yolo_model.predict(frame, verbose=False)
        if len(result[0].boxes) == 0:
            return None
        label = self.packs_yolo_model.names[int(result[0].boxes[0].cls)]
        confidence = (result[0].boxes[0].conf)
        xywh = result[0].boxes[0].xywh[0]
        # result[0].show()
        # print(f"label: {label}; confidence: {confidence}; xywh: {xywh}")
        return {'shape': label, 'size': (int(xywh[2]), int(xywh[3])), 'cover_on': True, 'location': (int(xywh[0]), int(xywh[1]))}

    def identify_cells(self, frame: ndarray, drawing_frame:ndarray=None) -> dict[tuple[str, float]]:
        """
        classify the cell model from one or multiple frames

        Args:
            frame (list[np.ndarray]): list of frame(s) used for the classification 

        Returns:
            list[tuple[str, float]]: list of model with associated probability
        """
        #cells_probs = [{'model': "AA", 'prob': 0.51}, {'model': "C", 'prob': 0.49},  {'model': "XXX", 'prob': 0.23}, {'model': "XYZ", 'prob': 0.12}]
        result = self.cells_yolo_model.predict(frame, verbose=False) 
        if len(result[0].boxes) == 0:
            return None
        output = {'bbs': [], 'zs': []}
        models = []
        for i, box in enumerate(result[0].boxes):
            model = self.cells_yolo_model.names[int(box.cls)]
            models.append(model)
            confidence = (box.conf)
            x, y, w, h = map(int, box.xywh[0].cpu().numpy())
            centre = (x, y)
            try:
                z = self.get_z_at_pos(*centre)
            except:
                print("depth frame not accessible")
                z = 0
            output['bbs'].append((x, y, w))
            output['zs'].append(z)
            if drawing_frame is not None:
                cv2.circle(drawing_frame, centre, 1, (0, 100, 100), 3)
                cv2.circle(drawing_frame, centre, w//2, (255, 0, 255), 3)
                cv2.putText(drawing_frame, f"id: {i}; {model}",      np.array(centre)+(-30, -20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
                cv2.putText(drawing_frame, f"c: {centre}",  np.array(centre)+(-30, 0), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
                cv2.putText(drawing_frame, f"r: {w//2}; z: {z:0.3f}",    np.array(centre)+(-30,  20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
            
        # set(models) gives us a list with he unique values in the models list, then for each we count how many times it 
        # appears in the list, that's the most voted model
        output['model'] = (max(set(models), key=models.count)) 
        return output

    def cell_detection(self, frame: np.ndarray) -> list[ndarray]:
        # DEPRECATED NOT USE, USE IDENTIFY CELLS INSTEAD
        """detect cells positions based on image

        Args:
            frame (np.ndarray): frame for the detection

        Returns:
            list[ndarray]: positons list
        """
        cells_positions = []
        cp_frame = copy.deepcopy(frame)
        if isinstance(frame, PIL.Image.Image):
            cp_frame = np.array(cp_frame)
            if frame.mode == "RGB":
                cv2.cvtColor(cp_frame, cv2.COLOR_RGB2BGR)
        preprocessed = cv2.cvtColor(cp_frame, cv2.COLOR_BGR2GRAY)
        # kernel_size = 5
        # kernel = np.ones((kernel_size, kernel_size),np.float32) / (kernel_size*kernel_size)
        # gauss = cv2.filter2D(frame, -1, kernel)
        preprocessed = cv2.medianBlur(preprocessed, 5)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        preprocessed = clahe.apply(preprocessed)
        
        kernel = np.ones((5, 5), np.uint8) 
        preprocessed = cv2.morphologyEx(preprocessed, cv2.MORPH_CLOSE, kernel) 
        # img_erosion = cv2.erode(frame, kernel, iterations=1) 
        # img_dilation = cv2.dilate(frame, kernel, iterations=1) 

        # edges = cv2.Canny(preprocessed, 0, 300)
        # vision.show_frames("Detection", [preprocessed])
        # cv2.imshow("Preprocessed", preprocessed)

        circles = cv2.HoughCircles(preprocessed, cv2.HOUGH_GRADIENT, 1, preprocessed.shape[0] / 8, param1=1, param2=80, minRadius=5, maxRadius=60)
        if circles is not None:
            # print(f"found: {len(circles[0])} circles")
            circles = np.uint16(np.around(circles))
            # print(circles)
            cells_positions = circles[0][:, 0:3] # x, y, radius
            drawing_frame = copy.deepcopy(cp_frame)
            for i in circles[0, :]:
                center = (i[0], i[1])
                radius = i[2]
                z = self.get_z_at_pos(*center)
                cv2.putText(drawing_frame, f"c: {center}; r: {radius}; z: {z:0.3f}", np.array(center)+(-50-int(radius/2), - 50-int(radius/2)), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (155, 255, 255), 1)
                cv2.circle(drawing_frame, center, 1, (0, 100, 100), 3)
                cv2.circle(drawing_frame, center, radius, (255, 0, 255), 3)
            cv2.imshow("Detection", drawing_frame)
            # cv2.waitKey(0)
        #else:
            #print("No circles found")
        #    pass
        return cells_positions

    def assess_cells_qualities(self, frame:np.ndarray, bbs_positions: list[ndarray]) -> list[float]:
        """assign to each cell a score based on quality

        Args:
            frame (np.ndarray): frame for assessment
            bbs_positions (list[ndarray]): the position of the bounding boxes to create a close up of the battery cell

        Returns:
            list[float]: the scores evaluated by the system
        """
        cells_qualities = np.random.rand(len(bbs_positions))
        return cells_qualities

    def frame_pos_to_pose(self, frame_pos:ndarray, base_T_TCP) -> sm.SE3:
        """convert a position in the frame into a 4x4 pose in world frame

        Args:
            frame_pos (ndarray): position in the frame

        Returns:
            sm.SE3(sm.SE3): 4x4 pose in world frame
        """
        try:
            Z = self.get_z_at_pos(*frame_pos)
            P = vision.frame_pos_to_3dpos(frame_pos=frame_pos, camera=self.camera, Z=Z)
            base_T_cam = base_T_TCP * self.camera.extrinsic
            tmp = base_T_cam * sm.SE3(P)
            T = sm.SE3.Rt(sm.SO3(base_T_TCP.R), tmp.t) # keep the current orientation of the tcp
        except AttributeError:
            print("Frame pos to pose debug")
            T = sm.SE3([float('inf'), float('inf'), float('inf')])
        return T

    def verify_pickup(self, position: ndarray, radius=0.5) -> list[bool]:
        """verify if a cell hs been picked up

        Args:
            position (ndarray): position of the cell in the image

        Returns:
            bool: if or not the cell was picked up
        """
        print("position: ",position)
        cp_current_frame = copy.deepcopy(self.get_current_frame())
        cp_start_frame = copy.deepcopy(self.background)

        #if isinstance(cp_start_frame, PIL.Image.Image):
        #    cp_start_frame = np.array(cp_start_frame)
        #if cp_start_frame.mode == "RGB":
        #    cp_start_frame = cv2.cvtColor(np.array(cp_start_frame), cv2.COLOR_RGB2BGR)
        #if cp_current_frame.mode == "RGB":
        #    cp_current_frame = cv2.cvtColor(np.array(cp_current_frame), cv2.COLOR_RGB2BGR)

        cp_start_frame = cv2.cvtColor(cp_start_frame, cv2.COLOR_BGR2GRAY)
        current_frame = cv2.cvtColor(cp_current_frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(current_frame, cp_start_frame)
        # cv2.imshow("Diff", diff)
        _, thresh = cv2.threshold(diff, 50, 255, cv2.THRESH_BINARY)
        result = cv2.dilate(thresh, np.ones((5, 5), np.uint8), iterations=2)
        cx, cy = position[0], position[1]
        n_deg, n_r = 8, 10
        voting, votes = n_deg*n_r, 0
        for  deg in np.linspace(0, 2*np.pi, num=n_deg):
            for r in np.linspace(0, radius, num=n_r):
                point = (np.array([cx, cy]) + (np.array([np.cos(deg), np.sin(deg)]) * r)).astype(int)
                votes += result[point[1]][point[0]]/255 # access to opnecv mat x, y inverted if white=255, then we add a vote for a hit otherwise 0
        pickedup = (votes/voting > 0.5)
        # print(f"The cell was pickedup: {pickedup}")
        result_bgr = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
        print("result: ",result_bgr)
        print("picked up: ",pickedup)
        print("center", cx, cy)
        if not pickedup:
            cv2.circle(result_bgr, (cx, cy), 3, (0, 0, 255), 3)
        else:
            cv2.circle(result_bgr, (cx, cy), 3, (0, 255, 0), 3)
        # cv2.imwrite(f"{position}.jpg", result_bgr)
        # vision.show_frames("Verify pick up", [result_bgr])
        # cv2.imshow("Background", self.background)
        # cv2.imshow("Verify pick up", result_bgr)
        # cv2.waitKey(0)
        return pickedup

if __name__ == "__main__":
    cell_m_q, cell_h_q = 0.6, 0.8
    cover_place_pose = sm.SE3([-0.45, -0.12, 0.050]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(np.pi - 20*np.pi/180)
    discard_T = sm.SE3([0.155, -0.495, 0.306]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(np.pi - 20*np.pi/180)
    keep_T = sm.SE3([0.083, -0.308, 0.306]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(np.pi - 20*np.pi/180)
    R = sm.SO3([[-0.003768884463184431, -0.9999801870110973700,  0.0050419336721138118], 
        [0.9999374423980765800, -0.0038217260702308998, -0.0105121691499708400], 
        [0.0105312297618392200,  0.0050019991098505349,  0.9999320342926355500]])
    t = np.array([0.051939876523448010, -0.0323596382860819900,  0.0211982932413351600])
    camera_Ext = sm.SE3.Rt(R, t)
    home_pos = [0.5599642992019653, -1.6431008778014125, 1.8597601095782679, -1.7663117847838343, -1.5613859335528772, -1.4]

    vision_module = VisionModule(camera_Ext=camera_Ext)
    robot_module = RobotModule(ip="192.168.1.100", home_position=home_pos, tcp_length_dict={'small': -0.072, 'big': -0.08}, active_gripper='big', gripper_id=0)
    robot_module.move_to_home()
    
    result = vision_module.locate_pack(vision_module.get_current_frame())
    pose = vision_module.frame_pos_to_pose(result['location'], robot_module.get_TCP_pose())
    for i in range(100):
        robot_module.pick_and_place(pose, cover_place_pose)
        robot_module.move_to_home()
