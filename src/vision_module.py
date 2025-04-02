import PIL.Image
import numpy as np
from numpy import ndarray
import cv2
import numpy as np
import matplotlib.pyplot as plt
import copy
import PIL
from gubokit import vision
import time
import spatialmath as sm
from gubokit import vision

class VisionModule():
    def __init__(self, camera_Ext: sm.SE3):
        pass
        # camera initialization
        try:
            self.camera = vision.RealSenseCamera(extrinsic=camera_Ext,
                                                    enabled_strams={
                                                    'color': [1280, 720],
                                                    'depth': [640, 480],
                                                    # 'infrared': [640, 480]
                                                    })
            print("Starting vision module")
        except RuntimeError:
            self.camera = None
            print("The vision module could not be started, the module will run for debug purpose")
        
        self.set_background() #!
        
    def set_background(self):
        new_bg = self.get_current_frame()
        # cv2.imwrite("Background.jpg", new_bg)
        self.background = new_bg

    def get_current_frame(self, format="cv2", wait_delay=2) -> np.ndarray:
        """get the current frame from the camera

        Returns:
            np.ndarray: frame
        """
        time.sleep(wait_delay)
        try :
            frame = self.camera.get_color_frame()
        except AttributeError:
            print("Cannot access camera. For debuggin purpose it will acess a file in store")
            frame = None
        if format.lower() == "pil":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
            frame = PIL.Image.fromarray(frame)
        return frame

    def locate_pack(self, frame: ndarray):
        cp_frame = copy.deepcopy(frame)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # cv2.imshow("Remove color", hsv)
        # cv2.waitKey(0)
        mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([120, 70, 200]))
        cp_frame[mask > 0] = [255, 255, 255]  # Set removed color to white

        ans = chr(0 & 0xFF)
        l_t, h_t = 85, 90
        contrast, brightness = 1.5, 20
        # while ans != 'q':
        #     print(f"contrast: {contrast}, brightness: {brightness}")
        #     print(f"low: {l_t}, high: {h_t}")
        #     enhanced = cv2.convertScaleAbs(cp_frame, alpha=contrast, beta=brightness)
        #     cv2.imshow("Enhanced", enhanced)
        #     gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
        #     cv2.imshow("Gray", gray)
        #     edges = cv2.Canny(gray, l_t, h_t)
        #     cv2.imshow("Edges", edges)
        #     ans = chr(cv2.waitKey(0) & 0xFF)
        #     if ans == 'x':
        #         contrast -= 0.1
        #     if ans == 'c':
        #         contrast += 0.1
        #     if ans == 'r':
        #         brightness -= 5
        #     if ans == 't':
        #         brightness += 5
        #     if ans == 'w':
        #         l_t -= 5
        #     if ans == 'e':
        #         l_t += 5
        #     if ans == 's':
        #         h_t -= 5
        #     if ans == 'd':
        #         h_t += 5
        gray = cv2.cvtColor(cp_frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY)
        cv2.imshow("Shape", thresh)
        # cv2.waitKey(0)
        edges = cv2.Canny(thresh, l_t, h_t)
        lines = cv2.HoughLinesP(gray, rho=0.1, theta=np.pi/180, threshold=10, minLineLength=0, maxLineGap=100)
        # edges2 = cv2.Canny(gray, l_t, h_t)
        # edges = cv2.erode(edges, kernel=np.array([[0,1,0], [0,1,0], [0,0,0]], np.uint8), iterations=2)
        # edges = cv2.dilate(edges, kernel=np.array([[0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0]], np.uint8), iterations=1)
        # edges = cv2.dilate(edges, kernel=np.array([[0,0,0,0,0], [0,0,0,0,0], [1,1,1,1,1], [0,0,0,0,0], [0,0,0,0,0]], np.uint8), iterations=1)
        cv2.imshow("Shape", edges)
        # cv2.waitKey(0)
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(gray, (x1, x2), (y1, y2), color=(0,0,255))
        cv2.imshow("line", cp_frame)
        cv2.waitKey(0)

        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # print(len(contours))
        # for contour in contours:
        #     length, area = cv2.arcLength(contour, closed=True), cv2.contourArea(contour)
        #     if length < 200:
        #         continue
        #     epsilon = 0.01 * cv2.arcLength(contour, True)
        #     approx = cv2.approxPolyDP(contour, epsilon, True)
        #     x, y, w, h = cv2.boundingRect(approx)
        #     cv2.drawContours(cp_frame, [approx], -1, (0, 255, 0), 2)
        #     cv2.drawContours(cp_frame, [contour], -1, (255, 0, 0), 2)
        #     cv2.rectangle(cp_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        #     cv2.putText(cp_frame, str(cv2.contourArea(contour)), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        #     print("area", str(area))
        #     print("length", str(length))
        # cv2.imshow("Shape", cp_frame)
        # cv2.waitKey(0)
        return {'shape': 'trapezoid', 'size': (0, 0), 'cover_on': True, 'location': (0, 0)}

    def classify_cell(self, frames: list[ndarray]) -> dict[tuple[str, float]]:
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
        # vision.show_frames("Detection", [preprocessed])
        # cv2.imshow("Preprocessed", preprocessed)

        circles = cv2.HoughCircles(preprocessed, cv2.HOUGH_GRADIENT, 1, preprocessed.shape[0] / 8, param1=1, param2=80, minRadius=40, maxRadius=100)
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
            # cv2.imshow("Detection", drawing_frame)
            # cv2.waitKey(0)
            # vision.show_frames("Detection", [drawing_frame])
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

    def frame_pos_to_3d(self, frame_pos:ndarray, camera, cell_heigth, camera_z) -> sm.SE3:
        """convert a position in the frame into a 4x4 pose in world frame

        Args:
            frame_pos (ndarray): position in the frame

        Returns:
            sm.SE3: 4x4 pose in world frame
        """
        return vision.frame_pos_to_3dpos(frame_pos=frame_pos, camera=camera, Z=(camera_z - cell_heigth))

    def verify_pickup(self, position: ndarray, radius=0.5) -> list[bool]:
        """verify if a cell hs been picked up

        Args:
            position (ndarray): position of the cell in the image

        Returns:
            bool: if or not the cell was picked up
        """
        cp_current_frame = copy.deepcopy(self.get_current_frame())
        cp_start_frame = copy.deepcopy(self.background)
        # if isinstance(start_frame, PIL.Image.Image):
        #     cp_start_frame = np.array(cp_start_frame)
        #     if start_frame.mode == "RGB":
        #         cv2.cvtColor(cp_start_frame, cv2.COLOR_RGB2BGR)
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
    vision_module = VisionModule(camera_Ext=sm.SE3([0,0,0]))

    square_frames = [cv2.imread("data/i4.0_frames/square01.png"), cv2.imread("data/i4.0_frames/square02.png"), cv2.imread("data/i4.0_frames/square03.png")]
    trapez_frames = [cv2.imread("data/i4.0_frames/trapezoid01.png"), cv2.imread("data/i4.0_frames/trapezoid02.png"), cv2.imread("data/i4.0_frames/trapezoid03.png")]
    empty_frames = [cv2.imread("data/i4.0_frames/empty1.png"), cv2.imread("data/i4.0_frames/empty2.png"), cv2.imread("data/i4.0_frames/empty3.png")]
    # vision_module.locate_pack(square_frames[0])
    # vision_module.locate_pack(frame2)
    # result = vision_module.frame_pos_to_3d((822, 177), vision_module.camera, cell_heigth=0.035, camera_z=0.9)
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")
    results = model(trapez_frames[0])
    results[0].show()
    # ans = 0xff & 0
    # i = 0
    # filenames = [
    #     "trapezoid1.png", "trapezoid2.png", "trapezoid3.png",
    #     "square1.png", "square2.png", "square3.png",
    #     "empty1.png", "empty2.png", "empty3.png"
    #     ]
    # while ans != 'q':
    #     frame = vision_module.get_current_frame(wait_delay=0)    
    #     cv2.imshow("frame", frame)
    #     ans = chr(cv2.waitKey(1) & 0xff)
    #     if ans == 's':
    #         cv2.imwrite(filenames[i], frame)
    #         i += 1
    
    # vision_module.classify_cell(camera_frame)
    # bbs_positions = vision_module.cell_detection(camera_frame)
    # vision_module.assess_cells_qualities(camera_frame, bbs_positions=bbs_positions)
    # input("Remove one cell")
    # camera_frame = vision_module.get_current_frame()
    # cv2.imshow("cam", camera_frame)
    # for bb in bbs_positions:
    #     vision_module.verify_pickup(bb)
