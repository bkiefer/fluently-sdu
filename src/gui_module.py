import PIL.Image
import PIL.ImageTk
from numpy import ndarray
import tkinter as tk
import cv2
import PIL

class MemGui(tk.Tk):
    def __init__(self, camera_frame: PIL.Image):
        super().__init__()
        self.title("MeM use case")
        # self.geometry("800x600+400+400") # 2nd and 3rd number will move the window spawn point (with multiple screen will start from most left screen)
        size = (int(camera_frame.width*1.1), int(camera_frame.height*1.2))
        self.geometry(f"{size[0]}x{size[1]}")
        self.resizable(False, False)
        self.states = []
        self.camera_frame = camera_frame
        self.active_frame = 0
        self.wait_interaction = False
        self.chosen_model = ""
        self.chosen_locations = []

        self.container = tk.Frame(self, width=size[0], height=size[1])  # Fixed frame size
        self.container.pack_propagate(False)  # Prevent resizing of the frame
        self.container.pack()

        self.frames = []
        for screen in (HomeScreen, AutoClassScreen, ManualClassScreen, AutoDetectScreen, ManualDetectScreen, AutoAssessScreen, ManualAssessScreen):
            frame = screen(self.container, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames.append(frame)
        
        self.show_frame(0)

    def show_frame(self, state_id: int):
        """update the state of the gui the current state will be hidden and the new one will be visible

        Args:
            state_id (int): id of new state
        """
        self.frames[int(state_id)].tkraise()

    def ask_for_help(self,  query: str):
        """ask human for help for something

        Args:
            query (str): the question/request for the human
        """
        pass

    def draw_bbs(self, bbs_position: list[ndarray]):
        """draw bounding boxes on the battery on the frame showed for the user

        Args:
            bbs_position (list[ndarray]): postions of bounding boxes
        """
    
    def write_qualities(self, bbs_position: list[ndarray], qualities: list[float]):
        """write the quality of each cell on the frame showed to the user

        Args:
            bbs_position (list[ndarray]): postions of bounding boxes for each cell
            qualities (list[float]): qualities of each cell
        """

    def update_image(self, new_frame: cv2.Mat):
        self.camera_frame = new_frame

class HomeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        canvas_width, canvas_height = 540, 720

        self.canvas = tk.Canvas(self, width=canvas_width, height=canvas_height)
        self.canvas.pack()

        self.draw_image(self.controller.camera_frame)

        # Bind the resizing event to dynamically resize the image
        # self.bind("<Configure>", self.on_resize)
    
    def draw_image(self, img):
        self.tk_image = PIL.ImageTk.PhotoImage(img)
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

    def on_resize(self, event):
        print("on_resize")
        new_width, new_height = event.width, event.height
        resized_image = self.controller.camera_frame.resize((new_width, new_height))
        self.draw_image(resized_image)    

class AutoClassScreen(HomeScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        #TODO: stopped here 

class ManualClassScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        label = tk.Label(self, text="man class", font=("Arial", 16))
        # label.pack(pady=20)

        button1 = tk.Button(self, text="Go to Screen 1", 
                            command=lambda: controller.show_frame(2))
        button1.pack()

        button2 = tk.Button(self, text="Go to Screen 2", 
                            command=lambda: controller.show_frame(0))
        button2.pack()

class AutoDetectScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        label = tk.Label(self, text="auto detect", font=("Arial", 16))
        label.pack(pady=20)

class ManualDetectScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

class AutoAssessScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

class ManualAssessScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

if __name__ == "__main__":
    camera_frame = cv2.imread("./data/NMC21700-from-top.jpg")
    camera_frame = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
    camera_frame = PIL.Image.fromarray(camera_frame)
    app = MemGui(camera_frame=camera_frame)
    app.mainloop()