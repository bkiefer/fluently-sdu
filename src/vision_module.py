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
        """initialization of the vision module
        In case the camera is not connected the try except block arn the user and set the camera to None, 
        the functions in this module have try except in case they need to use the camera so that you can
        work without using the actual camera.
        Then load all the models used for classification and localization

        Args:
            camera_Ext (sm.SE3): Extrinsic of the camera
            verbose (bool, optional): Set this to true to see all the debug messages in the console. Defaults to False.
        """
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
        self.qual_cnn = vision.CustomConvNeuralNet(n_classes=2)
        self.qual_cnn.load_model("data/cell_qual_classifier.pth")
        self.set_background()
        
    def set_background(self):
        """Save the current frame as background, mainly used in the verification of the pickup, when the cells are confirmed we save the background and then compare as we pick up
        """
        self.logger.debug("Setting background")
        new_bg = self.get_current_frame()
        self.background = new_bg

    def get_current_frame(self, format="cv2", wait_delay=0)-> np.ndarray:
        """get the current frame from the camera, in case the camera has not been connected a file from storage gets used
        the frame is retrieved as cv2 image but can be converted in pil, this is the format used by the gui canvas

        Args:
            format (str, optional): format of the frame. Defaults to "cv2".
            wait_delay (int, optional): delay before taking the image, could be sued to have a more static and higher quality frame. Defaults to 0.

        Returns:
            np.ndarray: frame from camera/storage
        """
        time.sleep(wait_delay)
        try :
            frame = self.camera.get_color_frame()
        except AttributeError:
            frame = cv2.imread("data/camera_frame.png")
            # frame = cv2.imread("data/camera_frame1.png")
        if format.lower() == "pil":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
            frame = PIL.Image.fromarray(frame)
        return frame

    def get_z_at_pos(self, x, y)-> float:
        """Get the z from the depth sensor of the camera in the position specified

        Args:
            x (int): x position of the point
            y (int): y position of the point

        Returns:
            float: z distance from camera to point xy in camera
        """
        depth_frame = self.camera.get_depth_frame()
        depth_img = np.asanyarray(depth_frame.get_data())
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_img, alpha=100), cv2.COLORMAP_JET)
        # cv2.imshow("Depth Frame", depth_colormap)
        z = depth_frame.get_distance(x, y)
        return z

    def locate_pack(self, frame: ndarray)-> dict: 
        """run the yolo image on the frame and return a dictionary describing the result for the pack

        Args:
            frame (ndarray): image to use for detection/classification

        Returns:
            dict: dictionary with shape(label), size, if the cover is on(it is always true as the classification is don ON the cover), and the location in the frame
        """
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

    def identify_cells(self, frame: ndarray, drawing_frame: ndarray=None)-> dict:
        """
        classify the cell model from one frame using the yolo model

        Args:
            frame np.ndarray: frame used for the classification 
            drawing_frame np.ndarray: if provided the function will draw on this frame the results of the classification

        Returns:
            dict[bbs: list[list[int]], zs: list[float], model: str]: a dctionary with all the bb(bounding boxes, zs associated and the model for all the cell)
        """
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

    def assess_cells_qualities(self, frame:np.ndarray, bbs_positions: list[ndarray])-> list[float]:
        """for each cell tell if is is to keep or not based on a close up and the use of the model

        Args:
            frame (np.ndarray): frame for assessment
            bbs_positions (list[ndarray]): the position of the bounding boxes to create a close up of the battery cell

        Returns:
            list[float]: whether or not to keep the cells 
        """
        cells_keep = []
        img = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        for bb in bbs_positions:
            x, y, w, h = bb
            close_up = img[(y-h//2):(y+h//2), (x-w//2):(x+w//2)]
            cells_keep.append(self.qual_cnn.predict_img(close_up))
        return cells_keep

    def frame_pos_to_pose(self, frame_pos:ndarray, base_T_TCP:sm.SE3, Z=None)-> sm.SE3:
        """convert a position in the frame into a 4x4 pose in world frame

        Args:
            frame_pos (ndarray): position in the frame
            base_T_TCP (sm.SE3): T for base to TCP 
            Z (_type_, optional): distance from camera to pos, can be provided by user or retrieved from depth sensor in camera. Defaults to None.

        Returns:
            sm.SE3: real world pose of the frame point 
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

    def verify_pickup(self, position: ndarray, radius=0.5)-> bool:
        """verify if a cell has been picked up:
        - we take the background and the current frame
        - find the absolute difference between the two
        - threshold the differnce to have white pixel only where there is a difference
        - dilate the thresholded frame to fill in possible missed pixel by the threshold
        - at this point we have a black frame, and white pixels where there was a change from the background, these spots are where cell are pickedup
        - so we start in the position and look in a radius, every white pixel gets added to votes
        - if 51% of the pixel in the circle are white it gets considered pickedup as there are enough diff in the area
        - from the background

        Args:
            position (ndarray): position in the frame
            radius (float, optional): radius around which we check for pixels after the subtraction. Defaults to 0.5.

        Returns:
            bool: whether or not the cell was pickedup 
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
        return pickedup

if __name__ == "__main__":
    R = sm.SO3([[-0.003768884463184431, -0.9999801870110973700,  0.0050419336721138118], 
        [0.9999374423980765800, -0.0038217260702308998, -0.0105121691499708400], 
        [0.0105312297618392200,  0.0050019991098505349,  0.9999320342926355500]])
    t = np.array([0.051939876523448010, -0.0323596382860819900,  0.0211982932413351600])
    camera_Ext = sm.SE3.Rt(R, t)
    vision_module = VisionModule(camera_Ext=camera_Ext)
    