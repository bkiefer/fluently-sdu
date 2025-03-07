import PIL.Image
import numpy as np
from numpy import ndarray
import cv2
import numpy as np
import matplotlib.pyplot as plt
import copy
import PIL
import pyrealsense2 as rs
from gubokit import vision

class VisionModule():
    def __init__(self):
        pass
        # camera initialization
        try:
            self.camera = vision.RealSenseCamera({
                                                    'color': [1280, 720],
                                                    # 'depth': [640, 480],
                                                    # 'infrared': [640, 480]
                                                    })
            print("Starting vision module")
        except RuntimeError:
            print("The vision module could not be started, the module will run for debug purpose")
        self.background = cv2.imread("./data/background.jpg")     
        
    def set_background(self):
        new_bg = self.get_current_frame()
        self.background = new_bg

    def get_current_frame(self, format="cv2") -> np.ndarray:
        """get the current frame from the camera

        Returns:
            np.ndarray: frame
        """
        frame = cv2.imread("./data/NMC21700-from-top.png") # TESTING
        # self.frame = self.camera.get_color_frame()
        if format.lower() == "pil":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
            frame = PIL.Image.fromarray(frame)
        return frame

    def classify_cell(self, frames: list[np.ndarray]) -> dict[tuple[str, float]]:
        """
        classify the cell model from one or multiple frames

        Args:
            frame (list[np.ndarray]): list of frame(s) used for the classification 

        Returns:
            list[tuple[str, float]]: list of model with associated probability
        """
        cells_probs = [{'model': "AA", 'prob': 0.51}, {'model': "C", 'prob': 0.49},  {'model': "XXX", 'prob': 0.23}, {'model': "XYZ", 'prob': 0.12}]
        return cells_probs

    def cell_detection(self, frame: np.ndarray) -> list[ndarray]:
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
        # vision.show_frames("Detection", [preprocessed]) # !!!

        circles = cv2.HoughCircles(preprocessed, cv2.HOUGH_GRADIENT, 1, preprocessed.shape[0] / 8, param1=1, param2=100, minRadius=40, maxRadius=100)
        if circles is not None:
            # print(f"found: {len(circles[0])} circles")
            circles = np.uint16(np.around(circles))
            # print(circles)
            cells_positions = circles[0][:, 0:3] # x, y, radius
            drawing_frame = copy.deepcopy(cp_frame)
            for i in circles[0, :]:
                center = (i[0], i[1])
                radius = i[2]
                # cv2.putText(drawing_frame, f"c: {center}; r: {radius}", np.array(center)+(-50-int(radius/2), - 50-int(radius/2)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (155, 255, 255), 1)
                cv2.circle(drawing_frame, center, 1, (0, 100, 100), 3)
                cv2.circle(drawing_frame, center, radius, (255, 0, 255), 3)
            # vision.show_frames("Detection", [drawing_frame]) # !!!
        else:
            print("No circles found")
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

    def verify_pickup(self, frame: np.ndarray, position: ndarray, radius=0.5) -> list[bool]:
        """verify if a cell hs been picked up

        Args:
            position (ndarray): position of the cell in the image

        Returns:
            bool: if or not the cell was picked up
        """
        start_frame = cv2.cvtColor(self.background, cv2.COLOR_BGR2GRAY)
        cp_frame = copy.deepcopy(frame)
        if isinstance(frame, PIL.Image.Image):
            cp_frame = np.array(cp_frame)
            if frame.mode == "RGB":
                cv2.cvtColor(cp_frame, cv2.COLOR_RGB2BGR)
        current_frame = cv2.cvtColor(cp_frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(current_frame, start_frame)
        _, thresh = cv2.threshold(diff, 70, 255, cv2.THRESH_BINARY)
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
        if not pickedup:
            cv2.circle(result_bgr, (cx, cy), 3, (0, 0, 255), 3)
        else:
            cv2.circle(result_bgr, (cx, cy), 3, (0, 255, 0), 3)
        # vision.show_frames("Verify pick up", [result_bgr]) # !!!
        return pickedup

if __name__ == "__main__":
    camera_frame = cv2.imread("./data/background.jpg")
    vision_module = VisionModule()
    vision_module.classify_cell(camera_frame)
    bbs_positions = vision_module.cell_detection(camera_frame)
    vision_module.assess_cells_qualities(camera_frame, bbs_positions=bbs_positions)
    camera_frame = cv2.imread("./data/frame.jpg")
    for bb in bbs_positions:
        vision_module.verify_pickup(camera_frame, bb)
    
