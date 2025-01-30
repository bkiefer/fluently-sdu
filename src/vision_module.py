import numpy as np
from numpy import ndarray
import cv2
import numpy as np

class VisionModule():
    def __init__(self):
        # camera initialization
        pass

    def get_current_frame(self) -> cv2.Mat:
        """get the current frame from the camera

        Returns:
            cv2.Mat: frame
        """
        frame = None
        return frame
    
    def classify_cell(self, frames: list[cv2.Mat]) -> list[tuple[str, float]]:
        """
        classify the cell model from one or multiple frames

        Args:
            frame (list[cv2.Mat]): list of frame(s) used for the classification 

        Returns:
            list[tuple[str, float]]: list of model with associated probability
        """
        cells_probs = []
        return cells_probs

    def cell_detection(self, frame: cv2.Mat) -> list[ndarray]:
        """detect cells positions based on image

        Args:
            frame (cv2.Mat): frame for the detection

        Returns:
            list[ndarray]: positons list
        """
        cells_positions = []
        return cells_positions

    def assess_cells_qualities(self, frame:cv2.Mat, bbs_positions: list[ndarray]) -> list[float]:
        """assign to each cell a score based on quality

        Args:
            frame (cv2.Mat): frame for assessment
            bbs_positions (list[ndarray]): the position of the bounding boxes to create a close up of the battery cell

        Returns:
            list[float]: the scores evaluated by the system
        """
        cells_qualities = []
        return cells_qualities
    
    def verify_pickup(self, position: ndarray) -> bool:
        """verify if a cell hs been picked up

        Args:
            position (ndarray): position of the cell in the image

        Returns:
            bool: if or not the cell was picked up
        """
        current_frame = self.get_current_frame()
        pickedup = False
        return pickedup

