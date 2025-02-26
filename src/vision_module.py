import PIL.Image
import numpy as np
from numpy import ndarray
import cv2
import numpy as np
import matplotlib.pyplot as plt
import copy
import PIL
import pyrealsense2 as rs
# from gubokit import vision

class VisionModule():
    def __init__(self):
        pass
        # camera initialization
        # self.camera = vision.RealSenseCamera() 
        self.start_frame = cv2.imread("./data/NMC21700-from-top.png")     
        
    def get_current_frame(self, format="cv2") -> cv2.Mat:
        """get the current frame from the camera

        Returns:
            cv2.Mat: frame
        """
        frame = cv2.imread("./data/NMC21700-from-top.png") # TESTING
        # self.frame = self.camera.get_color_frame()
        if format.lower() == "pil":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
            frame = PIL.Image.fromarray(frame)
        return frame

    def classify_cell(self, frames: list[cv2.Mat]) -> dict[tuple[str, float]]:
        """
        classify the cell model from one or multiple frames

        Args:
            frame (list[cv2.Mat]): list of frame(s) used for the classification 

        Returns:
            list[tuple[str, float]]: list of model with associated probability
        """
        cells_probs = [{'model': "AA", 'prob': 0.51}, {'model': "C", 'prob': 0.49},  {'model': "XXX", 'prob': 0.23}, {'model': "XYZ", 'prob': 0.12}]
        return cells_probs

    def cell_detection(self, frame: cv2.Mat) -> list[ndarray]:
        """detect cells positions based on image

        Args:
            frame (cv2.Mat): frame for the detection

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

        edges = cv2.Canny(preprocessed, 100 ,200)
        # vision.show_frames("Edges", [edges])
        circles = cv2.HoughCircles(edges, cv2.HOUGH_GRADIENT, 1, edges.shape[0] / 8, param1=100, param2=30, minRadius=1, maxRadius=100)
        if circles is not None:
            # print(f"found: {len(circles[0])} circles")
            circles = np.uint16(np.around(circles))
            # print(circles)
            cells_positions = circles[0][:, 0:3] # x, y, radius
            drawing_frame = copy.deepcopy(cp_frame)
            for i in circles[0, :]:
                center = (i[0], i[1])
                cv2.circle(drawing_frame, center, 1, (0, 100, 100), 3)
                radius = i[2]
                cv2.circle(drawing_frame, center, radius, (255, 0, 255), 3)
            
            #vision.show_frames("Detection", [drawing_frame]) # !!!
        else:
            print("No circles found")
        return cells_positions

    def assess_cells_qualities(self, frame:cv2.Mat, bbs_positions: list[ndarray]) -> list[float]:
        """assign to each cell a score based on quality

        Args:
            frame (cv2.Mat): frame for assessment
            bbs_positions (list[ndarray]): the position of the bounding boxes to create a close up of the battery cell

        Returns:
            list[float]: the scores evaluated by the system
        """
        cells_qualities = np.random.rand(len(bbs_positions))
        return cells_qualities

    def verify_pickup(self, frame: cv2.Mat, position: ndarray) -> list[bool]:
        """verify if a cell hs been picked up

        Args:
            position (ndarray): position of the cell in the image

        Returns:
            bool: if or not the cell was picked up
        """
        start_frame = cv2.cvtColor(self.start_frame, cv2.COLOR_BGR2GRAY)
        cp_frame = copy.deepcopy(frame)
        if isinstance(frame, PIL.Image.Image):
            cp_frame = np.array(cp_frame)
            if frame.mode == "RGB":
                cv2.cvtColor(cp_frame, cv2.COLOR_RGB2BGR)
        current_frame = cv2.cvtColor(cp_frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(current_frame, start_frame)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        result = cv2.dilate(thresh, np.ones((5, 5), np.uint8), iterations=2)
        pickedup = bool(result[position[1]][position[0]])
        
        print(f"The cell was pickedup: {pickedup}")
        result_bgr = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
        if not pickedup:
            cv2.circle(result_bgr, position, 3, (0, 0, 255), 3)
        else:
            cv2.circle(result_bgr, position, 3, (0, 255, 0), 3)
        
        #vision.show_frames("Verify pick up", [result_bgr]) # !!!
        return pickedup

if __name__ == "__main__":
    camera_frame = cv2.imread("./data/NMC21700-from-top.png")
    # camera_frame = cv2.imread("./data/camera_frame_02.jpg")
    # camera_frame = cv2.imread("./data/Camera02.jpg")
    vision_module = VisionModule()
    vision_module.classify_cell(camera_frame)
    bbs_positions = vision_module.cell_detection(camera_frame)
    vision_module.assess_cells_qualities(camera_frame, bbs_positions=bbs_positions)
    camera_frame = cv2.imread("./data/NMC21700-from-top-one_missing.png")
    for bb in bbs_positions:
        vision_module.verify_pickup(camera_frame, bb)
    
