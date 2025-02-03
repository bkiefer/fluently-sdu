import PIL.Image
import PIL.ImageTk
import sys
from numpy import ndarray
import tkinter as tk
from tkinter import ttk
import cv2
import PIL

import tkinter as tk

import tkinter as tk

class _BoundingBoxEditor:
    def __init__(self, canvas, bbs_position):
        self.canvas = canvas
        self.bbs_position = bbs_position
        self.selected_box = None
        self.dragging = None  # "move" or "resize"
        self.start_x = 0
        self.start_y = 0
        
        self.box_items = []  # Store drawn objects
        self.draw_boxes()

        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def spawn_box(self):
        x_min, y_min, x_max, y_max = -5, -5, 5, 5 

        center_x = (x_min + x_max) // 2
        center_y = (y_min + y_max) // 2

        box = self.canvas.create_rectangle(x_min, y_min, x_max, y_max, outline="black", width=2, tags='bbs')
        move_handle = self.canvas.create_oval(center_x-5, center_y-5, center_x+5, center_y+5, fill="blue", tags='bbs')
        resize_handle = self.canvas.create_rectangle(x_min-5, y_min-5, x_min+5, y_min+5, fill="red", tags='bbs')
        text_bg = self.canvas.create_rectangle(x_max-15, y_max-5, x_max, y_max+5, fill="white", outline="white", tags='bbs')
        text_label = self.canvas.create_text(x_max-7, y_max, text=f"{len(self.box_items):02d}", font=("Arial", 5), tags='bbs')

        self.box_items.append((box, move_handle, resize_handle, text_bg, text_label))
        print("asd")

    def draw_boxes(self):
        """Draws bounding boxes with resize/move handles"""
        self.canvas.delete('bbs')
        self.box_items.clear()
        for i, bb in enumerate(self.bbs_position):
            x_min, y_min, x_max, y_max = bb

            center_x = (x_min + x_max) // 2
            center_y = (y_min + y_max) // 2

            box = self.canvas.create_rectangle(x_min, y_min, x_max, y_max, outline="black", width=2, tags='bbs')
            move_handle = self.canvas.create_oval(center_x-5, center_y-5, center_x+5, center_y+5, fill="blue", tags='bbs')
            resize_handle = self.canvas.create_rectangle(x_min-5, y_min-5, x_min+5, y_min+5, fill="red", tags='bbs')
            text_bg = self.canvas.create_rectangle(x_max-15, y_max-5, x_max, y_max+5, fill="white", outline="white", tags='bbs')
            text_label = self.canvas.create_text(x_max-7, y_max, text=f"{i:02d}", font=("Arial", 5), tags='bbs')

            self.box_items.append((box, move_handle, resize_handle, text_bg, text_label))

    def on_click(self, event):
        """Detects which part of a box was clicked (move/resize)"""
        if self.canvas.find_withtag(tk.CURRENT):  # If clicked on an item
            item = self.canvas.find_withtag(tk.CURRENT)[0]
            for i, [box, move_handle, resize_handle, text_bg, text_label] in enumerate(self.box_items):
                if item == move_handle:
                    self.selected_box = i
                    self.dragging = "move"
                    self.start_x, self.start_y = event.x, event.y
                    break   
                elif item == resize_handle:  # Resize box
                    self.selected_box = i
                    self.dragging = "resize"
                    self.start_x, self.start_y = event.x, event.y
                    break  

    def on_drag(self, event):
        """Moves or resizes the selected bounding box"""
        if self.selected_box is None:
            return
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        x_min, y_min, x_max, y_max = self.bbs_position[self.selected_box]

        if self.dragging == "move":
            x_min += dx
            y_min += dy
            x_max += dx
            y_max += dy

        elif self.dragging == "resize":
            x_min += dx
            y_min += dy
        
        self.bbs_position[self.selected_box] = (x_min, y_min, x_max, y_max)
        self.start_x = event.x
        self.start_y = event.y
        self.draw_boxes()

    def on_release(self, event):
        """Resets after dragging"""
        self.selected_box = None
        self.dragging = None

class MemGui(tk.Tk):
    def __init__(self, camera_frame: PIL.Image):
        super().__init__()
        self.title("MeM use case")
        # self.geometry("800x600+400+400") # 2nd and 3rd number will move the window spawn point (with multiple screen will start from most left screen)
        size = (int(camera_frame.width+20), int(camera_frame.height*1.2))
        self.geometry(f"{size[0]}x{size[1]}")
        self.resizable(False, False)
        self.states = []
        
        self.camera_frame = camera_frame
        self.active_frame = 0
        self.wait_interaction = False
        
        self.proposed_models = [{'model': "NMC21700", 'prob': 0.97}, {'model': "CCN12900", 'prob': 0.76}, {'model': "ASD123", 'prob': 0.46}, {'model': "QWE456", 'prob': 0.26}]
        self.chosen_model = ""
        self.proposed_locations = [(80, 80, 140, 140), (240, 240, 300, 300), (400, 400, 460, 460)]
        self.chosen_locations = []
        self.high_quality_threshold = 0.8
        self.mid_quality_threshold = 0.6
        self.proposed_qualities = [0.81, 0.61, 0.41]
        self.chosen_qualities = []
        self.outcomes = [False, True, True]
        
        self.picture_container = tk.Frame(self, width=size[0]//2, height=size[1])
        self.picture_container.pack(side='left', padx=(10, 10))
        
        self.infos_container = tk.Frame(self, width=size[0]//2, height=size[1])
        self.infos_container.pack(side='right', padx=(5, 10), fill='both', expand=True)
        
        debug_btn = tk.Button(self.infos_container, text="debug", command=lambda: self.debug())
        # debug_btn.grid(row=1, column=0, sticky='nsew')


        # self.treeview = ttk.Treeview(self.infos_container)
        # self.treeview.place(x=500, y=300)

        info_bpack = {"model": "Unknown", "grid": (4, 3), "cells": [
                                                                    {"model": "123", "bb":[1, 1, 2, 2], "quality": 0.87, "pickedup":False},
                                                                    {"model": "123", "bb":[3, 3, 4, 4], "quality": 0.67, "pickedup":True },
                                                                    {"model": "123", "bb":[5, 5, 6, 6], "quality": 0.47, "pickedup":False},
                                                                    {"model": "123", "bb":[7, 7, 8, 8], "quality": 0.97, "pickedup":False},
                                                                    {"model": "123", "bb":[1, 1, 2, 2], "quality": 0.87, "pickedup":False},
                                                                    {"model": "123", "bb":[3, 3, 4, 4], "quality": 0.67, "pickedup":True },
                                                                    {"model": "123", "bb":[5, 5, 6, 6], "quality": 0.47, "pickedup":False},
                                                                    {"model": "123", "bb":[7, 7, 8, 8], "quality": 0.97, "pickedup":False},
                                                                    {"model": "123", "bb":[1, 1, 2, 2], "quality": 0.87, "pickedup":False},
                                                                    {"model": "123", "bb":[3, 3, 4, 4], "quality": 0.67, "pickedup":True },
                                                                    {"model": "123", "bb":[5, 5, 6, 6], "quality": 0.47, "pickedup":False},
                                                                    {"model": "123", "bb":[5, 5, 6, 6], "quality": 0.47, "pickedup":False},
                                                                    ]}

        self.update_info(info_bpack)
        
        
        self.frames = []
        self.expand_btn = tk.Button(self, text='▶', command=lambda: self.expand_collapse())
        for screen in (HomeScreen, AutoClassScreen, ManualClassScreen, AutoDetectScreen, ManualDetectScreen, AutoAssessScreen, ManualAssessScreen, PickingUpScreen):
            frame = screen(self.picture_container, self)
            frame.grid(row=0, column=0, sticky='nsew')
            self.frames.append(frame)

        self.show_frame(0)

    def debug(self):
        self.infos_container.pack_forget()
        print(self.x_entry.get())
        self.draw_bbs(self.proposed_locations)
        self.write_qualities(self.proposed_locations, self.proposed_qualities)

    def expand_collapse(self):
        current_window_height = self.winfo_height()
        current_window_width = self.winfo_width()
        if int(self.geometry().split("x")[0]) / self.camera_frame.height > 1: # the menu is alread open close it
            self.geometry(f"{int(self.camera_frame.width+20)}x{current_window_height}")
            self.expand_btn.config(text="▶")
        else:
            self.geometry(f"{current_window_width*2}x{current_window_height}")
            self.expand_btn.config(text="◀")

    def update_info(self, infos):
        # TODO: draw the batteyr pack in the gui with representation of bb (4 int) quality(float)
        idx = 0
        for i in range(infos['grid'][0]):
            for j in range(infos['grid'][1]):
                self.write_cell_state(j*180, i*100+30, infos['cells'][idx])
                idx += 1
                # break
            # break

    def write_cell_state(self, x, y, cell: dict['model': str, 'bb': list[int], 'quality': float, 'pickedup': bool]):
        self.x_min = tk.Entry(self.infos_container, width=4, justify="center")
        self.x_min.insert(0, str(cell['bb'][0]))
        self.x_min.place(x=x, y=y)
        self.y_max = tk.Entry(self.infos_container, width=4, justify="center")
        self.y_max.insert(0, str(cell['bb'][2]))
        self.y_max.place(x=x+75, y=y)
        self.y_min = tk.Entry(self.infos_container, width=4, justify="center")
        self.y_min.insert(0, str(cell['bb'][1]))
        self.y_min.place(x=x, y=y+35)
        self.y_max = tk.Entry(self.infos_container, width=4, justify="center")
        self.y_max.insert(0, str(cell['bb'][3]))
        self.y_max.place(x=x+75, y=y+35)
    
    def show_frame(self, state_id: int):
        """update the state of the gui the current state will be hidden and the new one will be visible

        Args:
            state_id (int): id of new state
        """
        self.frames[int(state_id)].tkraise()
        self.expand_btn.place(x=camera_frame.width-50, y=camera_frame.height*1.2-50)
        # will be done by bt ----
        if state_id > 2:
            self.draw_bbs(self.proposed_locations, self.frames[int(state_id)])
        if state_id > 4:
            self.write_qualities(self.proposed_locations, self.proposed_qualities)
        if state_id > 6:
            self.write_outcome_picked_cell(self.proposed_locations, self.outcomes)

    def ask_for_help(self,  query: str):
        """ask human for help for something

        Args:
            query (str): the question/request for the human
        """
        pass

    def draw_bbs(self, bbs_position: list[ndarray], frame):
        """draw bounding boxes on the battery on the frame showed for the user

        Args:
            bbs_position (list[ndarray]): postions of bounding boxes
        """
        self.bbs_editor = _BoundingBoxEditor(frame.canvas, bbs_position)
        # frame.canvas.create_rectangle(bb[0], bb[1], bb[2], bb[3], fill="", outline="black", width=2)
        # frame.canvas.create_rectangle(bb[2]-15, bb[3]-5, bb[2], bb[3]+5, fill="white", outline="white")
        # frame.canvas.create_text(bb[2]-7, bb[3], text=f"{i:02d}", font=("Arial", 5))

    def write_qualities(self, bbs_position: list[ndarray], qualities: list[float]):
        """write the quality of each cell on the frame showed to the user

        Args:
            bbs_position (list[ndarray]): postions of bounding boxes for each cell
            qualities (list[float]): qualities of each cell
        """
        for frame in self.frames:
            if hasattr(frame, "canvas"):
                for bb, quality in zip(bbs_position, qualities):
                    if quality > self.high_quality_threshold:
                        color = 'green2'
                    elif quality > self.mid_quality_threshold:
                        color = 'yellow2'
                    else:
                        color = 'firebrick1'
                    frame.canvas.create_rectangle(bb[0]-30, bb[1]-25, bb[0]+25, bb[1]+5, fill="gray9", outline="gray9")
                    frame.canvas.create_text(bb[0], bb[1]-10, text=f"{int(quality*100):02d}%", font=("Arial", 10), fill=color)

    def write_outcome_picked_cell(self, bbs_position: list[ndarray], outcomes: list[bool]):
        """mark on the image whether or not the battery cell was picked up

        Args:
            bbs_position (list[ndarray]): postions of bounding boxes
        """
        for frame in self.frames:
            if hasattr(frame, "canvas"):
                for bb, outcome in zip(bbs_position, outcomes):
                    if outcome:
                        frame.canvas.create_text((bb[0]+bb[2])//2, (bb[1]+bb[3])//2, text="✓", font=("Arial", 35), fill='green2')
                    else:
                        frame.canvas.create_text((bb[0]+bb[2])//2, (bb[1]+bb[3])//2, text="✗", font=("Arial", 35), fill='firebrick1')

    def update_image(self, new_frame: cv2.Mat):
        self.camera_frame = new_frame

class HomeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        canvas_width, canvas_height = self.controller.camera_frame.width, self.controller.camera_frame.height
        self.canvas = tk.Canvas(self, width=canvas_width, height=canvas_height)
        self.canvas.pack(pady=(10, 0))
        self.draw_image(self.controller.camera_frame)
    
    def draw_image(self, img):
        self.tk_image = PIL.ImageTk.PhotoImage(img)
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

class AutoClassScreen(HomeScreen):
    def __init__(self, parent:tk.Frame, controller: MemGui):
        super().__init__(parent, controller)
        self.proposed_model = self.controller.proposed_models[0]['model'] 
        self.label = tk.Label(self, text=f"Cells are: {self.proposed_model}", font=("Arial", 10))
        self.label.pack()

        btns_frame = tk.Frame(self)
        btns_frame.pack(side='bottom')
        confirm_btn = tk.Button(btns_frame, text="✓", background='green2', command=lambda: self.confirm())
        confirm_btn.pack(side='left')
        deny_btn = tk.Button(btns_frame, text="✗", background='firebrick1', command=lambda: self.deny())
        deny_btn.pack(side='left')
    
    def confirm(self):
        self.controller.chosen_model = self.proposed_model
        self.controller.show_frame(3)
    
    def deny(self):
        self.controller.show_frame(2)

class ManualClassScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        btns_frame = tk.Frame(self)
        # btns_frame.pack(anchor='center')
        btns_frame.place(relx=0.5, rely=0.5, anchor='center')
        for propose in self.controller.proposed_models[1:]: # we skip the first one as it was already denied bu the user
            button1 = tk.Button(btns_frame, text=f"{propose['model']}: {propose['prob']*100}%", command=lambda: self.chose_model(propose['model']))
            button1.pack()

    def chose_model(self, model: str):
        self.controller.chosen_model = model
        self.controller.show_frame(3)

class AutoDetectScreen(HomeScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.label = tk.Label(self, text=f"Proposed bouding boxes on the screen", font=("Arial", 10))
        self.label.pack()
        btns_frame = tk.Frame(self)
        btns_frame.pack(side='bottom')
        confirm_btn = tk.Button(btns_frame, text="✓", background='green2', command=lambda: self.confirm())
        confirm_btn.pack(side='left')
        deny_btn = tk.Button(btns_frame, text="Add", background='firebrick1', command=lambda: self.add_box())
        deny_btn.pack(side='left')

    def confirm(self):
        self.controller.show_frame(5)
    
    def add_box(self):
        self.controller.bbs_editor.spawn_box()
        # self.controller.show_frame(4)

class ManualDetectScreen(HomeScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        label = tk.Label(self, text="ManualDetectScreen", font=("Arial", 16))
        label.pack(pady=20)


class AutoAssessScreen(HomeScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.label = tk.Label(self, text=f"Proposed scores on the screen", font=("Arial", 10))
        self.label.pack()
        btns_frame = tk.Frame(self)
        btns_frame.pack(side='bottom')
        confirm_btn = tk.Button(btns_frame, text="✓", background='green2', command=lambda: self.confirm())
        confirm_btn.pack(side='left')
        deny_btn = tk.Button(btns_frame, text="Add", background='firebrick1', command=lambda: self.deny())
        deny_btn.pack(side='left')

    def confirm(self):
        self.controller.show_frame(7)
    
    def deny(self):
        self.controller.show_frame(6)

class ManualAssessScreen(HomeScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        label = tk.Label(self, text="ManualAssessScreen", font=("Arial", 16))
        label.pack(pady=20)

class PickingUpScreen(HomeScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        label = tk.Label(self, text="PickingUpScreen", font=("Arial", 16))
        label.pack(pady=20)
        # se rimane cosí si puó rimuovere e usare l'home screen

if __name__ == "__main__":
    camera_frame = cv2.imread("./data/NMC21700-from-top.jpg")
    camera_frame = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
    camera_frame = PIL.Image.fromarray(camera_frame)
    app = MemGui(camera_frame=camera_frame)
    app.show_frame(int(sys.argv[1]))
    app.mainloop()
