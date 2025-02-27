import PIL.Image
import PIL.ImageTk
import sys
from numpy import ndarray
import tkinter as tk
from tkinter import ttk
import cv2
import PIL
import numpy as np

class _BoundingBoxEditor:
    def __init__(self, canvas, bbs_position, frame):
        self.canvas = canvas
        self.bbs_position = bbs_position
        self.selected_box = None
        self.dragging = None  # "move" or "resize"
        self.start_x = 0
        self.start_y = 0
        # self.delete_mode = False
        self.frame = frame

        self.box_items = []  # Store drawn objects
        self.draw_boxes()
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)

        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def spawn_box(self):
        x_min, y_min, x_max, y_max = 100, 100, 150, 150 
        self.bbs_position.append([x_min, y_min, x_max, y_max])

        center_x = (x_min + x_max) // 2
        center_y = (y_min + y_max) // 2

        box = self.canvas.create_rectangle(x_min, y_min, x_max, y_max, outline="black", width=2, tags='bbs')
        move_handle = self.canvas.create_oval(center_x-5, center_y-5, center_x+5, center_y+5, fill="blue", tags='bbs')
        resize_handle = self.canvas.create_rectangle(x_min-5, y_min-5, x_min+5, y_min+5, fill="red", tags='bbs')
        text_bg = self.canvas.create_rectangle(x_max-15, y_max-5, x_max, y_max+5, fill="white", outline="white", tags='bbs')
        text_label = self.canvas.create_text(x_max-7, y_max, text=f"{len(self.box_items):02d}", font=("Arial", 5), tags='bbs')
        delete_btn = self.canvas.create_rectangle(x_max-7, y_min-7, x_max+7, y_min+7, fill="white", outline="red", tags='bbs')
        delete_label = self.canvas.create_text(x_max, y_min, text="X", fill="red", font=("Arial", 10), tags = 'bbs')

        self.box_items.append([box, move_handle, resize_handle, text_bg, text_label, delete_btn, delete_label])
        if hasattr(self.frame, "number_label"):
            self.frame.number_label.configure(text=f"\nNumber of cells: {len(self.bbs_position)}\n")
       
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

            # if delete_mode:
            delete_btn = self.canvas.create_rectangle(x_max-7, y_min-7, x_max+7, y_min+7, fill="white", outline="red", tags='bbs')
            delete_label = self.canvas.create_text(x_max, y_min, text="X", fill="red", font=("Arial", 10), tags = 'bbs')
            self.box_items.append([box, move_handle, resize_handle, text_bg, text_label, delete_btn, delete_label])
            # else:
            #     self.box_items.append([box, move_handle, resize_handle, text_bg, text_label, None, None])
        
        if hasattr(self.frame, "number_label"):
            self.frame.number_label.configure(text=f"\nNumber of cells: {len(self.bbs_position)}\n")

    def on_click(self, event):
        """Detects which part of a box was clicked (move/resize)"""
        if self.canvas.find_withtag(tk.CURRENT):  # If clicked on an item
            item = self.canvas.find_withtag(tk.CURRENT)[0]
            for i, [box, move_handle, resize_handle, text_bg, text_label, delete_btn, delete_label] in enumerate(self.box_items):
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
                elif item == delete_label: # if clicked on close button, remove bb
                    if len(self.bbs_position) > 1:
                        self.bbs_position.pop(i)
                        self.draw_boxes()
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

class _QualitiesEditor:
    def __init__(self, canvas, bbs_position, qualities):
        self.canvas = canvas
        self.bbs_position = bbs_position
        self.qualities = qualities

        self.h = 0.8
        self.m = 0.6
        
        self.old_quality = None
        self.editing = False
        self.editing_qual_id = None
        self.edit_entry = tk.Entry(self.canvas, width=4, font=("Arial", 7), justify="center")

        self.boxes = []
        self.write_qualities()
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.edit_entry.bind("<Return>", self.on_enter)
        self.edit_entry.bind("<Escape>", self.on_esc)
    
    def write_qualities(self):
        for i, (bb, q) in enumerate(zip(self.bbs_position, self.qualities)):
            x_min, y_min, x_max, y_max = bb
            center_x = (x_min + x_max) // 2
            center_y = (y_min + y_max) // 2
            color = 'green2' if q > self.h else 'yellow2' if q > self.m else 'firebrick1'
            self.canvas.create_rectangle(bb[0]-30, bb[1]-25, bb[0]+25, bb[1]+5, fill="gray9", outline="gray9")
            self.canvas.create_rectangle(x_min, y_min, x_max, y_max, outline="black", width=2, tags='bbs')
            self.canvas.create_oval(center_x-5, center_y-5, center_x+5, center_y+5, fill="blue", tags='bbs')
            qual = self.canvas.create_text(bb[0], bb[1]-10, text=f"{int(q*100):02d}%", font=("Arial", 10), fill=color)
            self.canvas.create_rectangle(x_max-15, y_max-5, x_max, y_max+5, fill="white", outline="white", tags='bbs')
            self.canvas.create_text(x_max-7, y_max, text=f"{i:02d}", font=("Arial", 5), tags='bbs')
            self.boxes.append(qual)

    def on_click(self, event):
        if self.canvas.find_withtag(tk.CURRENT):  # If clicked on an item
            item = self.canvas.find_withtag(tk.CURRENT)[0]
            for i, label_id in enumerate(self.boxes):
                if label_id == item:
                    self.editing_qual_id = i
                    self.editing_item_id = label_id
                    self.old_quality = self.canvas.itemcget(label_id, "text")
                    self.canvas.itemconfig(label_id, state="hidden")
                    self.edit_entry.place(x = self.canvas.coords(label_id)[0]-25, y = self.canvas.coords(label_id)[1]-13)
                    self.editing = True
                    self.edit_entry.focus_set()
        
    def on_enter(self, event):
        new_q = float(self.edit_entry.get()) / 100
        self.qualities[self.editing_qual_id] = new_q
        self.canvas.itemconfig(self.editing_item_id, state="normal")
        self.canvas.itemconfig(self.editing_item_id, text=f"{int(self.edit_entry.get()):02d}%")
        self.canvas.itemconfig(self.editing_item_id, fill='green2' if new_q > self.h else 'yellow2' if new_q > self.m else 'firebrick1')
        self.canvas.winfo_toplevel().focus_set() # defocus entry
        self.edit_entry.delete(0, tk.END)
        self.edit_entry.place_forget()
    
    def on_esc(self, event):
        self.canvas.itemconfig(self.editing_item_id, state="normal")
        self.canvas.winfo_toplevel().focus_set() # defocus entry
        self.edit_entry.delete(0, tk.END)
        self.edit_entry.place_forget()

class MemGui(tk.Tk):
    def __init__(self, camera_frame: PIL.Image):
        super().__init__()
        self.title("MeM use case")
        # self.geometry("800x600+400+400") # 2nd and 3rd number will move the window spawn point (with multiple screen will start from most left screen)
        size = (int(camera_frame.width+20), int(camera_frame.height*1.4))
        self.geometry(f"{size[0]}x{size[1]}")
        self.resizable(False, False)
        self.states = []
        
        self.camera_frame = camera_frame
        self.active_frame = 0
        self.wait_interaction = False
        
        self.proposed_models = []#[{'model': "NMC21700", 'prob': 0.97}, {'model': "CCN12900", 'prob': 0.76}, {'model': "ASD123", 'prob': 0.46}, {'model': "QWE456", 'prob': 0.26}]
        self.chosen_model = ""
        self.proposed_locations = []#[(80, 80, 140, 140), (240, 240, 300, 300), (400, 400, 460, 460)]
        self.chosen_locations = []
        self.proposed_qualities = []
        self.chosen_qualities = []
        self.outcomes = []#[False, True, True]
        self.class_reject = False # !!!
        self.done = False
        
        self.picture_container = tk.Frame(self, width=size[0]//2, height=size[1])
        self.picture_container.pack(side='left', padx=(10, 10))
        
        self.infos_container = tk.Frame(self, width=size[0]//2, height=size[1])
        self.infos_container.pack(side='right', padx=(5, 10), fill='both', expand=True)
        
        debug_btn = tk.Button(self.infos_container, text="debug", command=lambda: self.debug())
        debug_btn.grid(row=1, column=0, sticky='nsew')

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
        # for screen in (HomeScreen, AutoClassScreen, ManualClassScreen, AutoDetectScreen, ManualDetectScreen, AutoAssessScreen, ManualAssessScreen, PickingUpScreen):
        for i, screen in enumerate([HomeScreen, AutoClassScreen, ManualClassScreen, AutoDetectScreen, AutoAssessScreen, AutoSortScreen, ManualSortScreen, HomeScreen]):
            frame = screen(self.picture_container, self, i)
            frame.grid(row=0, column=0, sticky='nsew')
            self.frames.append(frame)

        # self.show_frame(1)

    def debug(self):
        pass

    def expand_collapse(self):
        if self.expand_btn['text'] == "▶": # the menu is already open close it
            self.geometry(f"{int(self.winfo_width()+200)}x{self.winfo_height()}")
            self.expand_btn.config(text="◀")
        else:
            self.geometry(f"{int(self.winfo_width()-200)}x{self.winfo_height()}")
            self.expand_btn.config(text="▶")

    def update_info(self, infos):
        # Maybe a treeview would be better
        idx = 0
        for i in range(infos['grid'][0]):
            for j in range(infos['grid'][1]):
                self.write_cell_state(j*180, i*100+30, infos['cells'][idx])
                idx += 1
                # break
            # break

    def update_proposed_models(self, proposed_models):
        self.proposed_models = proposed_models
        self.frames[1].label.configure(text=f"Cells are: {self.proposed_models[0]['model']}")
        for propose in self.proposed_models[1:]: # we skip the first one as it was already denied by the user
                btn = tk.Button(self.frames[2].btns_frame, text=f"{propose['model']}: {propose['prob']*100}%", command=lambda: self.frames[2].chose_model(propose['model']))
                btn.pack()

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
        self.expand_btn.place(x=self.camera_frame.width-50, y=self.camera_frame.height*1.2-50)
        # if state_id > 2:
        #     self.update_bbs(self.proposed_locations, self.frames[int(state_id)])
        # if state_id == 3:
        #     # self.bbs_editor.delete_mode = True
        #     self.bbs_editor.draw_boxes(delete_mode=True)
        # if state_id > 3:
        #     self.write_qualities(self.proposed_locations, self.proposed_qualities, self.frames[int(state_id)])
        # if len(self.chosen_locations) != 0 and len(self.chosen_qualities) != 0:
        #     self.update_bbs(self.chosen_locations, self.frames[int(state_id)])
        #     self.write_qualities(self.chosen_locations, self.chosen_qualities, self.frames[int(state_id)])
        #     self.write_outcome_picked_cell(self.proposed_locations, self.outcomes)
        self.active_frame = state_id

    def ask_for_help(self,  query: str):
        """ask human for help for something

        Args:
            query (str): the question/request for the human
        """
        pass

    def update_bbs(self, bbs_position: list[ndarray], frame):
        """draw bounding boxes on the battery on the frame showed for the user

        Args:
            bbs_position (list[ndarray]): postions of bounding boxes
        """
        self.proposed_locations = bbs_position
        self.bbs_editor = _BoundingBoxEditor(frame.canvas, bbs_position, frame)

    def write_qualities(self, qualities: list[float], frame: tk.Frame):
        """write the quality of each cell on the frame showed to the user

        Args:
            bbs_position (list[ndarray]): postions of bounding boxes for each cell
            qualities (list[float]): qualities of each cell
        """
        # frames[0].focus_set()
        self.proposed_qualities = qualities
        self.quals_editor = _QualitiesEditor(frame.canvas, bbs_position=self.chosen_locations, qualities=qualities)

    def write_outcome_picked_cell(self, centre: ndarray, outcome: bool, frame: tk.Frame):
        """mark on the image whether or not the battery cell was picked up

        Args:
            bbs_position (list[ndarray]): postions of bounding boxes
        """
        if outcome:
            frame.canvas.create_text(centre[0], centre[1], text="✓", font=("Arial", 35), fill='green2')
        else:
            frame.canvas.create_text(centre[0], centre[1], text="✗", font=("Arial", 35), fill='firebrick1')
        frame.canvas.update()

    def update_image(self, new_frame: ndarray):
        self.camera_frame = new_frame

class HomeScreen(tk.Frame):
    def __init__(self, parent, controller, idx):
        super().__init__(parent)
        self.controller = controller
        self.idx = idx
        canvas_width, canvas_height = self.controller.camera_frame.width, self.controller.camera_frame.height
        self.canvas = tk.Canvas(self, width=canvas_width, height=canvas_height)
        self.canvas.pack(pady=(10, 0))
        self.draw_image(self.controller.camera_frame)
    
    def draw_image(self, img):
        self.tk_image = PIL.ImageTk.PhotoImage(img)
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

class AutoClassScreen(HomeScreen):
    def __init__(self, parent:tk.Frame, controller: MemGui, idx):
        super().__init__(parent, controller, idx)
        self.label = tk.Label(self, text=f"Cells are: ", font=("Arial", 10))
        self.label.pack()

        btns_frame = tk.Frame(self)
        # btns_frame.pack()
        btns_frame.pack()
        confirm_btn = tk.Button(btns_frame, text="✓", background='green2', command=lambda: self.confirm())
        confirm_btn.pack(side='left')
        deny_btn = tk.Button(btns_frame, text="✗", background='firebrick1', command=lambda: self.deny())
        deny_btn.pack(side='left')

        # self.after(1, self.change_label)
    
    # def change_label(self):
    #     if self.controller.proposed_models:
    #         self.proposed_model = self.controller.proposed_models[0]['model'] 
    #     text = f"Cells are: {self.proposed_model}"
    #     self.label.configure(text=text)
    #     self.label.after(1000,self.change_label)

    def confirm(self):
        self.controller.chosen_model = self.controller.proposed_models[0]
        # self.controller.show_frame(self.idx + 2)
        #self.controller.bbs_editor.delete_mode = True
    
    def deny(self):
        # need to comunicate with bt
        self.controller.class_reject = True # !!!
        #pass
        # self.controller.show_frame(self.idx + 1)
        #self.controller.bbs_editor.delete_mode = True

class ManualClassScreen(tk.Frame):
    def __init__(self, parent, controller, idx):
        super().__init__(parent)
        self.controller = controller
        self.idx = idx
        self.btns_frame = tk.Frame(self)
        self.btns_frame.place(relx=0.5, rely=0.5, anchor='center')
        # self.after(1, self.change_label)
        
    # def change_label(self):
    #     if self.controller.proposed_models:
    #         for propose in self.controller.proposed_models[1:]: # we skip the first one as it was already denied by the user
    #             button1 = tk.Button(self.btns_frame, text=f"{propose['model']}: {propose['prob']*100}%", command=lambda: self.chose_model(propose['model']))
    #             button1.pack()
    #     else:
    #         self.after(1, self.change_label)
            
    def chose_model(self, model: str):
        self.controller.chosen_model = model
        # self.controller.show_frame(self.idx + 1)
        #self.controller.bbs_editor.delete_mode = True
        #self.controller.bbs_editor.draw_boxes()

class AutoDetectScreen(HomeScreen):
    def __init__(self, parent, controller, idx):
        super().__init__(parent, controller, idx)
        self.controller = controller

        self.label = tk.Label(self, text=f"Proposed bounding boxes on the screen", font=("Arial", 10))
        self.label.pack()
        self.number_label = tk.Label(self, text="\nNumber of cells:\n", font=("Arial", 10))
        self.number_label.pack()
        btns_frame = tk.Frame(self)
        btns_frame.pack()
        confirm_btn = tk.Button(btns_frame, text="✓", background='green2', command=lambda: self.confirm())
        confirm_btn.pack(side='left')
        add_btn = tk.Button(btns_frame, text="Add", background='firebrick1', command=lambda: self.add_box())
        add_btn.pack(side='left')

        # self.after(1, self.change_label)
    
    # def change_label(self):
    #     if self.controller.proposed_locations:
    #         no_of_cells = len(self.controller.proposed_locations)
    #         text = f"\nNumber of cells: {no_of_cells}\n"
    #         self.number_label.configure(text=text)
    #     self.number_label.after(1, self.change_label)
        
    def confirm(self):
        self.controller.chosen_locations = self.controller.bbs_editor.bbs_position 
        #self.controller.proposed_qualities = np.random.rand(len(self.controller.chosen_locations)) #!!!
        # self.controller.show_frame(self.idx + 1)
        # print("Chosen locations:", self.controller.chosen_locations)
        #print("Generated qualities:", [self.controller.proposed_qualities])

    def add_box(self):
        self.controller.bbs_editor.spawn_box()

class AutoAssessScreen(HomeScreen):
    def __init__(self, parent, controller, idx):
        super().__init__(parent, controller, idx)
        self.label = tk.Label(self, text=f"Proposed scores on the screen", font=("Arial", 10))
        self.label.pack()
        btns_frame = tk.Frame(self)
        btns_frame.pack()
        confirm_btn = tk.Button(btns_frame, text="✓", background='green2', command=lambda: self.confirm())
        confirm_btn.pack(side='left')

    def confirm(self):
        self.controller.chosen_qualities = self.controller.quals_editor.qualities 
        #self.controller.outcomes = np.random.choice([0, 1], len(self.controller.chosen_locations))
        self.controller.outcomes = [(el>=0.5) for el in self.controller.chosen_qualities]
        # print("Generated outcomes:", self.controller.outcomes)
        #print("Generated outcomes:", [(el>=0.5) for el in self.controller.outcomes])
        # print("Chosen qualities:", self.controller.chosen_qualities)
        # self.controller.show_frame(0)

class AutoSortScreen(HomeScreen):
    def __init__(self, parent, controller, idx):
        super().__init__(parent, controller, idx)
        self.controller = controller
        self.label = tk.Label(self, text="Robotic cell sorting in progress...", font=("Arial", 10))
        self.label.pack()
        self.number_label = tk.Label(self, text="\nCells sorted:\n", font=("Arial", 10))
        self.number_label.pack()

    #     self.after(1, self.change_label)
    
    # def change_label(self):
    #     if self.controller.proposed_locations:
    #         no_of_cells = len(self.controller.proposed_locations)

    #         # NOTE: Here it is assumed that the list "outcomes" describes successfully sorted cells?
    #         text=f"\nCells sorted: {sum(self.controller.outcomes)} out of {len(self.controller.chosen_locations)}\n"
    #         self.number_label.configure(text=text)
    #     self.number_label.after(1, self.change_label)      

class ManualSortScreen(HomeScreen):
    def __init__(self, parent, controller, idx):
        super().__init__(parent, controller, idx)
        self.label = tk.Label(self, text=f"Please help extracting the battery cells.", font=("Arial", 10))
        self.label.pack()
        self.number_label = tk.Label(self, text="\nCells sorted:\n", font=("Arial", 10))
        self.number_label.pack()
        btns_frame = tk.Frame(self)
        btns_frame.pack()
        confirm_btn = tk.Button(btns_frame, text="Done", background='green2', command=lambda: self.confirm())
        confirm_btn.pack(side='left')
        # self.after(1, self.change_label)
    
    # def change_label(self):
    #     if self.controller.proposed_locations:
    #         no_of_cells = len(self.controller.proposed_locations)

    #         # NOTE: Here it is assumed that the list "outcomes" describes successfully sorted cells?
    #         text=f"\nCells sorted: {sum(self.controller.outcomes)} out of {len(self.controller.chosen_locations)}\n"
    #         self.number_label.configure(text=text)
    #     self.number_label.after(1, self.change_label)      
        
    def confirm(self):
        self.controller.done = True

if __name__ == "__main__":
    # camera_frame = cv2.imread("./data/NMC21700-from-top.jpg")
    camera_frame = cv2.imread("./data/camera_frame.jpg")
    camera_frame = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
    camera_frame = PIL.Image.fromarray(camera_frame)
    app = MemGui(camera_frame=camera_frame)
    app.show_frame(int(sys.argv[1]))
    app.mainloop()