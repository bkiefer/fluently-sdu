import spatialmath as sm
import numpy as np

class Cell():
    def __init__(self):
        self.model = ""
        self.size = (0.0, 0.0) # diameter, height
        self.quality = -1.0
        self.pose = sm.SE3()
        self.frame_position = [-1, -1]
        self.sorted = False

    def __repr__(self):
        return f"{self.quality:05.2f}"
        
class PackState():
    def __init__(self, rows: int=1, cols: int=1):
        # rows and cols useful for sanity check
        self.rows = rows
        self.cols = cols
        self.model = "unknown"
        # TODO: relative positions between cells to benefit pick and place action
        self.cells = []
        for _ in range(rows):
            row = []
            for _ in range(cols):
                row.append(Cell())
            self.cells.append(row)
    
    def update_dim(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.model = "unknown"
        self.cells = []
        for _ in range(rows):
            row = []
            for _ in range(cols):
                row.append(Cell())
            self.cells.append(row)
        
    def update_cell(self, i, j, model=None, size=None, quality=None, pose=None, frame_position=None, sorted=None):
        """_summary_

        Args:
            i (_type_): _description_
            j (_type_): _description_
            model (_type_, optional): _description_. Defaults to None.
            size (_type_, optional): _description_. Defaults to None.
            quality (_type_, optional): _description_. Defaults to None.
            pose (_type_, optional): _description_. Defaults to None.
            frame_position (_type_, optional): _description_. Defaults to None.
            sorted (_type_, optional): _description_. Defaults to None.
        """
        if model is not None:
            self.cells[i][j].model = model
        if size is not None:
            self.cells[i][j].size = size
        if quality is not None:
            self.cells[i][j].quality =  quality
        if pose is not None:
            self.cells[i][j].pose = pose
        if frame_position is not None:
            self.cells[i][j].frame_position = frame_position
        if sorted is not None:
            self.cells[i][j].sorted = sorted

    def insert_holes(self, holes: list[tuple[int, int]]):
        """In case of non rectangular shaped battery pack we can still use this, we define the pack with the maximum x and y size, and then add holes

        Args:
            holes (list[tuple[int, int]]): list of where the pack does not have a battery and should have it accordingly to a mapping of rectangular shape
        """
        for hole in holes:
            self.cells[hole[0], hole[1]] = None

    def __repr__(self):
        spacer = "\t\t"
        printable = f"Printing battery qualities of model: {self.model}\n\t"
        for j, _ in enumerate(self.cells[0]):
            printable += " "*2 + str(j) + spacer
        printable += "\n"

        for i, row in enumerate(self.cells):           
            printable += str(i) + "\t"
            for j, cell in enumerate(row):
                printable += str(cell) + spacer
            printable += "\n"
        return printable[:-1] # we add an additional enter

ps = PackState(5, 6)
# print(ps)