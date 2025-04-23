import spatialmath as sm
import numpy as np

class Cell():
    def __init__(self):
        self.model = "unknown"
        self.radius = 0.0
        self.height = 0.0
        self.quality = -1.0
        self.pose = sm.SE3()
        self.frame_position = [-1, -1]
        self.sorted = False

    def __repr__(self):
        return f"mod: {self.model:^10} r: {self.radius:05.2f} h: {self.height:05.2f} f_pos: [{self.frame_position[0]:03d}, {self.frame_position[1]:03d}]  ok: {str(self.sorted)[0]} q: {self.quality:05.2f}"
        
class PackState():
    def __init__(self, rows: int=1, cols: int=1):
        self.model = "unknown"
        self.cell_model = "unknown"
        self.cover_on = True
        self.size = None
        self.location = None
        self.pose = None
        self.update_dim(rows=rows, cols=cols)
    
    def update_dim(self, rows: int, cols: int):
        self.cells = []
        self.rows = rows
        self.cols = cols
        for _ in range(rows):
            row = []
            for _ in range(cols):
                row.append(Cell())
            self.cells.append(row)

    def update_cell(self, i, j, model=None, radius=None, height=None, quality=None, pose=None, frame_position=None, sorted=None):
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
        if radius is not None:
            self.cells[i][j].radius = radius
        if height is not None:
            self.cells[i][j].height = height
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
        printable = f"\nPrinting battery pack state of model: {self.model}\n■■| "
        lenght_cell_str = len(str(self.cells[0][0]))
        h_line = "■■"
        for j, _ in enumerate(self.cells[0]):
            header = f"{str(j):^{lenght_cell_str}}" + " | "
            tmp = "-" * len(header)
            h_line += "|" + tmp[1:]
            printable += header
        printable += "\n"
        printable += (h_line + "|")
        printable += "\n"

        for i, row in enumerate(self.cells):           
            printable += str(i) + " | "
            for j, cell in enumerate(row):
                printable += (str(cell) + " | ")
            printable += "\n"
        return printable

if __name__ == "__main__":
    ps = PackState(2, 2)
    print(ps)