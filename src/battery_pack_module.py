import spatialmath as sm
from gubokit import utilities
#import utilities

class Cell():
    def __init__(self, model=None, width=None, z=None, quality=None, pose=None, frame_position=None, sorted=None):
        self.model = "unknown" if model is None else model
        self.width = 0.0 if width is None else width
        self.z = 0.0 if z is None else z
        self.keep = None if quality is None else quality
        self.pose = None if pose is None else pose
        self.frame_location = None if frame_position is None else frame_position
        self.sorted = None if sorted is None else sorted
        self.string_mode = ""

    def to_string_short(self):
        cell_str = ""
        cell_str += f"f_pos: {utilities.bool_to_str_fancy(not self.frame_location is None)}"
        cell_str += f"XYZ: {utilities.bool_to_str_fancy(not self.pose is None)}"
        cell_str += f"keep: {utilities.bool_to_str_fancy(self.keep)} "
        cell_str += f"pick: {utilities.bool_to_str_fancy(self.sorted)}"
        return cell_str

    def __repr__(self):
        cell_str = ""
        cell_str += f"f_pos: [{self.frame_location[0]:03d},{self.frame_location[1]:03d}] "
        if self.pose is not None:
            cell_str += f"XYZ:[{self.pose.t[0]:02.0f},{self.pose.t[1]:02.0f},{self.pose.t[2]:02.0f}]"
        else:
            cell_str += f"XYZ:unknown"
        cell_str += f"keep: {utilities.bool_to_str_fancy(self.keep)} "
        cell_str += f"pick: {utilities.bool_to_str_fancy(self.sorted)}"
        return cell_str

class PackState():
    def __init__(self, rows: int=1, cols: int=1):
        self.model = "unknown"
        self.model_confirmed = False
        self.cell_model = "unknown"
        self.cover_on = True
        self.size = None
        self.frame_location = None
        self.location_confirmed = False
        self.pose = None
        self.cells = []
        self.cells_confirmed = False
        self.quals = None # Either none, 'set' or 'confirmed'
        self.fastened = True
        self.pickup_attempted = False
        # self.update_dim(rows=rows, cols=cols)

    def update_dim(self, rows: int, cols: int):
        self.cells = []
        self.rows = rows
        self.cols = cols
        for _ in range(rows):
            row = []
            for _ in range(cols):
                row.append(Cell())
            self.cells.append(row)

    def add_cell(self, model: str=None, width: float=None, z: float=None, quality: bool=None, pose: sm.SE3=None, frame_position: tuple[int, int]=None, sorted: bool=None):
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
        self.cells.append(Cell(model=model, width=width, z=z, quality=quality, pose=pose, frame_position=frame_position, sorted=sorted))

    def update_cell(self, i, j, model=None, width=None, z=None, quality=None, pose=None, frame_position=None, sorted=None):
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
        if width is not None:
            self.cells[i][j].width = width
        if z is not None:
            self.cells[i][j].z = z
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
        printable = "\n" + "="*50 + f" Battery pack state " + "="*50 + "\n"
        printable += f"model: {self.model}\n"
        printable += f"pos: {self.frame_location}\n"
        printable += f"size: {self.size}\n"
        if self.pose is not None:
            printable += f"pose: {utilities.T_to_rotvec(self.pose)}\n"
        printable += f"cover_on: {self.cover_on}\n"
        printable += f"cell_model: {self.cell_model}\n"
        if len(self.cells) != 0:
            printable += " ========== CELLS: ==========\n"
            for i, cell in enumerate(self.cells):
                printable +=  f"{i:02d} " + str(cell) + "\n"
        return printable

if __name__ == "__main__":
    ps = PackState(2, 2)
    print(ps)
