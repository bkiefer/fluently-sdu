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
        if confidence < 0.4:
            return None
        xywh = result[0].boxes[0].xywh[0]
        # result[0].show()
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
                self.logger.warning("depth frame not accessible")
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

    def assess_cells_qualities(self, frame:np.ndarray, bbs_positions: list[ndarray]) -> list[float]:
        """assign to each cell a score based on quality

        Args:
            frame (np.ndarray): frame for assessment
            bbs_positions (list[ndarray]): the position of the bounding boxes to create a close up of the battery cell

        Returns:
            list[float]: the scores evaluated by the system
        """
        cells_keeps = np.random.choice([True, False], len(bbs_positions))
        return cells_keeps

    def frame_pos_to_pose(self, frame_pos:ndarray, base_T_TCP, Z=None) -> sm.SE3:
        """convert a position in the frame into a 4x4 pose in world frame

        Args:
            frame_pos (ndarray): position in the frame

        Returns:
            sm.SE3(sm.SE3): 4x4 pose in world frame
        """
        try:
            
            Z = self.get_z_at_pos(*frame_pos) if Z is None else Z
            P = vision.frame_pos_to_3dpos(frame_pos=frame_pos, camera=self.camera, Z=Z)
            base_T_cam = base_T_TCP * self.camera.extrinsic
            tmp = base_T_cam * sm.SE3(P)
            T = sm.SE3.Rt(sm.SO3(base_T_TCP.R), tmp.t) # keep the current orientation of the tcp
        except AttributeError:
            self.logger.debug("Frame pos to pose debug")
            T = sm.SE3([-1, -1, -1])
        return T

    def verify_pickup(self, position: ndarray, radius=0.5) -> list[bool]:
        """verify if a cell hs been picked up

        Args:
            position (ndarray): position of the cell in the image

        Returns:
            bool: if or not the cell was picked up
        """
        cp_current_frame = copy.deepcopy(self.get_current_frame())
        cp_start_frame = copy.deepcopy(self.background)
        cp_start_frame = cv2.cvtColor(cp_start_frame, cv2.COLOR_BGR2GRAY)
        current_frame = cv2.cvtColor(cp_current_frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(current_frame, cp_start_frame)
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
        self.logger.warning("pickedup, generate a random value")
        return np.random.choice([True, False])
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
    
    foldername = "data/pics_18650"
    for f in os.listdir(foldername):
        print(f)
        frame = cv2.imread(os.path.join(foldername, f))
        vision_module.identify_cells(frame, drawing_frame=frame)
        cv2.imshow("detection", frame)
        cv2.waitKey(0)