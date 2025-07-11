import py_trees as pt
import time
from robot_module import RobotModule
from battery_pack_module import PackState
from rdf_store import RdfStore
from vision_module import VisionModule
from behaviors import *
from viewer import BtViewer
import spatialmath as sm
import numpy as np
import PIL.Image
import PIL.ImageTk
import sys
from numpy import ndarray
import tkinter as tk
from tkinter import ttk
import cv2
import PIL
import numpy as np
import argparse
from fluently_mqtt_client import FluentlyMQTTClient

class _BoundingBoxEditor:
    def __init__(self, canvas, frame, tag='', move_color='blue'):
        self.canvas = canvas
        self.selected_box = None
        self.dragging = None  # "move" or "resize"
        self.start_x = 0
        self.start_y = 0
        self.frame = frame
        self.label = None
        self.tag = tag
        self.move_color = move_color

        self.boxes_items = []  # Store drawn objects
        self.bbs_position = []

        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.editable = True

    def set_color_icon(self, color: str):
        self.move_color = color

    def set_label(self, label):
        self.label = label

    def add_bb(self, bb):
        self.bbs_position.append(bb)

    def add_bbs(self, bbs):
        for bb in bbs:
            self.add_bb(bb)
    
    def clear_bbs(self):
        self.bbs_position = []
        self.canvas.delete('bbs' + self.tag)
        self.boxes_items.clear()

    def lock(self):
        self.editable = False
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")

    def _draw_box(self, label, x_min=500, y_min=500, x_max=1000, y_max=1000, scale=1, padx=0, pady=0):
        x_min = ((x_min * scale) + padx)
        x_max = ((x_max * scale) + padx)
        y_min = ((y_min * scale) + pady)
        y_max = ((y_max * scale) + pady)
        center_x = (x_min + x_max) // 2
        center_y = (y_min + y_max) // 2
        self.canvas.create_rectangle(x_min, y_min, x_max, y_max, outline="black", width=2, tags='bbs' + self.tag)
        self.canvas.create_rectangle(x_max-len(label)*10, y_max-9, x_max, y_max+9, fill="white", outline="white", tags='bbs' + self.tag) # label bg
        self.canvas.create_text(x_max-len(label)*5, y_max, text=label, font=("Arial", 10), tags='bbs' + self.tag) # label txt
        if self.editable:
            self.canvas.create_rectangle(x_max-7, y_min-7, x_max+7, y_min+7, fill="white", outline="red", tags='bbs' + self.tag) # delete_bg
            move_handle = self.canvas.create_oval(center_x-5, center_y-5, center_x+5, center_y+5, fill=self.move_color, tags='bbs' + self.tag)
            resize_handle = self.canvas.create_rectangle(x_min-5, y_min-5, x_min+5, y_min+5, fill="red", tags='bbs' + self.tag)
            delete_handle = self.canvas.create_text(x_max, y_min, text="X", fill="red", font=("Arial", 10), tags = 'bbs' + self.tag)
            self.boxes_items.append([move_handle, resize_handle, delete_handle])
        self.canvas.lift("bbs" + self.tag)

    def draw_boxes(self, scale=1, padx=0, pady=0):
        """Draws bounding boxes with resize/move handles"""
        self.canvas.delete('bbs' + self.tag)
        self.boxes_items.clear()
        for i, bb in enumerate(self.bbs_position):
            label = self.label if self.label is not None else f"{i:02d}"
            self._draw_box(label, *bb, scale=scale, padx=padx, pady=pady)
        
        if hasattr(self.frame, "number_label"):
            self.frame.number_label.configure(text=f"\nNumber of cells: {len(self.bbs_position)}\n")

    def on_click(self, event):
        """Detects which part of a box was clicked (move/resize)"""
        if self.canvas.find_withtag(tk.CURRENT):  # If clicked on an item
            item = self.canvas.find_withtag(tk.CURRENT)[0]
            for i, [move_handle, resize_handle, delete_handle] in enumerate(self.boxes_items):
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
                elif item == delete_handle: # if clicked on close button, remove bb
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
    def __init__(self, canvas, cell_m_q,  cell_h_q, editable=True):
        self.canvas = canvas
        self.bbs_position = []
        self.keep_bbs = []

        self.m, self.h = cell_m_q, cell_h_q        
        
        self.old_quality = None
        self.editing = False
        self.editing_qual_id = None
        self.edit_entry = tk.Entry(self.canvas, width=4, font=("Arial", 7), justify="center")

        self.boxes = []
        self.editable = editable
        
        self.canvas.bind("<ButtonPress-1>", self.on_click)
    
    def lock(self):
        self.editable = False
        self.canvas.unbind("<ButtonPress-1>")

    def add_quals(self, keep_bbs, bbs):
        self.bbs_position = bbs
        self.keep_bbs = keep_bbs

    def clear_quals(self):
        self.bbs_position = []
        self.keep_bbs = []
        self.canvas.delete('quals')
        self.boxes.clear()

    def write_qualities(self, scale=1, padx=0, pady=0):
        self.canvas.delete('quals')
        self.boxes.clear()
        for i, (bb, keep) in enumerate(zip(self.bbs_position, self.keep_bbs)):
            x_min = ((bb[0] * scale) + padx)
            y_min = ((bb[1] * scale) + pady)
            if self.editable:
                self.canvas.create_rectangle(x_min-5, y_min-5, x_min+5, y_min+5, fill="gray20", outline="white", tags='quals') # delete_bg
            if keep:
                txt_box = self.canvas.create_text(x_min, y_min, text="✔", font=("Arial", 10), fill="green2", tag='quals')
            else:
                txt_box = self.canvas.create_text(x_min, y_min, text="✘", font=("Arial", 10), fill="firebrick1", tag='quals')
            self.boxes.append(txt_box)

    def on_click(self, event):
        if self.canvas.find_withtag(tk.CURRENT):  # If clicked on an item
            item = self.canvas.find_withtag(tk.CURRENT)[0]
            for i, label_id in enumerate(self.boxes):
                if label_id == item:
                    self.keep_bbs[i] = not self.keep_bbs[i]
        
class MemGui(tk.Tk):
    def __init__(self):
        super().__init__()        
        """ ========== WORKSPACE SETUP ========== """
        self.cell_m_q, self.cell_h_q = 0.6, 0.8
        self.cover_place_pose = sm.SE3([-0.45, -0.12, 0.050]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(np.pi - 20*np.pi/180)
        self.discard_T = sm.SE3([0.155, -0.495, 0.306]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(np.pi - 20*np.pi/180)
        self.keep_T = sm.SE3([0.083, -0.308, 0.306]) * sm.SE3.Rx(np.pi) * sm.SE3.Rz(np.pi - 20*np.pi/180)
        R = sm.SO3([[-0.003768884463184431, -0.9999801870110973700,  0.0050419336721138118], 
            [0.9999374423980765800, -0.0038217260702308998, -0.0105121691499708400], 
            [0.0105312297618392200,  0.0050019991098505349,  0.9999320342926355500]])
        t = np.array([0.051939876523448010, -0.0323596382860819900,  0.0211982932413351600])
        self.camera_Ext = sm.SE3.Rt(R, t)
        home_pos = [0.5599642992019653, -1.6431008778014125, 1.8597601095782679, -1.7663117847838343, -1.5613859335528772, -1.4]
        self.swap_q = [ 0.3724, -1.8346, 2.1107, -1.0513, 1.5848, -0.4372]
        self.pack_models = ['Trapezoid', 'Square', 'unknown']
        self.cell_models = ['aaa', '18650', '21700', 'bbb', 'ccc', 'unknown']
        self.cells_icon_color = {'aaa': "#0373e2", '18650': "#17d627", '21700': "#b140a7",
                                 'bbb': "#f1a10a", 'ccc': "#684115", 'unknown': ''}

        """ ========== MODULE SETUP ========== """
        parser = argparse.ArgumentParser(description="My script with options")
        parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
        args = parser.parse_args()
        self.verbose = args.verbose
        self.logger = utilities.CustomLogger('MeM', 'MeM.log', console_level='info' if not self.verbose else 'debug')
        self.vision_module = VisionModule(camera_Ext=self.camera_Ext, verbose=self.verbose)
        self.robot_module = RobotModule(ip="192.168.1.100", home_position=home_pos, tcp_length_dict={'small': -0.072, 'big': -0.08}, active_gripper='big', gripper_id=0, verbose=self.verbose)
        self.pack_state = PackState()
        self.robot_module.move_to_home()
        self.voice_module = FluentlyMQTTClient(client_id="fluentlyClient", verbose=self.verbose)

        """ ========== RESET GUI ========== """
        self.state = {'pack_fastened': False, 'pack_confirmed' : False, 'cells_confirmed' : False, 'quals_confirmed' : False}
        self.changing_pack_model, self.changing_cell_model = False, False

        """ ========== LAYOUT GUI ========== """
        self.layout_gui()

        """ ========== DRAWER GUI ========== """
        self.pack_bb_drawer = _BoundingBoxEditor(self.home_frame.canvas, self.home_frame, tag='pack')
        self.cells_bb_drawer = None
        self.quals_editor = None        
        
    def skip_parts(self):
        self.logger.info("Skipping some parts")
        # self.camera_frame = self.vision_module.get_current_frame(format='pil')
        # self.camera_frame = cv2.imread("data/camera_frame1.png")
        # self.camera_frame = cv2.cvtColor(self.camera_frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        # self.camera_frame = PIL.Image.fromarray(self.camera_frame)
        
        # self.confirm_pack_fastened()
        # self.classify_pack()
        # self.locate_pack()
        # self.confirm_pack()
        # To skip the pack localization and classification
        # self.pack_state.cover_on = False
        # self.cells_bb_drawer = _BoundingBoxEditor(self.home_frame.canvas, self.home_frame, tag='cells')
        # self.classify_cells()
        # self.locate_cells()
        # self.confirm_cells()
        # self.assess_cells_qualities()
        # self.confirm_quals()

    def layout_gui(self):
        self.title("MeM use case")
        self.geometry("1280x720")

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=5)
        self.grid_columnconfigure(0, weight=1)
        self.configure(bg="#4b5661")

        self.top_frame = tk.Frame(self, bg='#1e2a38')
        self.top_frame.grid(row=0, column=0, sticky='nsew', padx=(5, 5), pady=(5, 5))
        self.top_frame.grid_rowconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(1, weight=2)
        self.mid_frame = tk.Frame(self, bg="#1e2a38")
        self.mid_frame.grid(row=1, column=0, sticky='nsew', padx=(5, 5), pady=(5, 5))
        self.mid_frame.grid_rowconfigure(0, weight=5)
        self.mid_frame.grid_rowconfigure(1, weight=1)
        self.mid_frame.grid_columnconfigure(0, weight=1)
        self.mid_frame.grid_columnconfigure(1, weight=2)
        
        self.fncs_frame = tk.Frame(self.mid_frame,  bg='#e6f0f7')
        self.fncs_frame.grid(row=0, column=0, rowspan=2, sticky='nsew', padx=(5, 5), pady=(5, 5))
        self.fncs_frame.columnconfigure(0, weight=1)
        self.fncs_frame.grid_propagate(False)
        
        self.home_frame = HomeScreen(self.mid_frame, self)
        self.home_frame.config(background='#2e3f4f')
        self.home_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 5), pady=(5, 5))
        self.home_frame.rowconfigure(0, weight=1)
        self.home_frame.columnconfigure(0, weight=1)
        self.home_frame.grid_propagate(False)

        self.progress_bar_frame = tk.Frame(self.top_frame,  bg='#e6f0f7')
        self.progress_bar_frame.grid(row=0, column=0, sticky='nsew', padx=(5, 5), pady=(5, 5))
        self.progress_bar_frame.columnconfigure(0, weight=1)
        self.progress_bar_frame.rowconfigure(0, weight=1)
        self.progress_bar_frame.grid_propagate(False)
        
        self.info_frame = tk.Frame(self.top_frame, background='#f0f4f7')
        self.info_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 5), pady=(5, 5))
        self.info_cols = 4
        self.info_rows = 5
        [self.info_frame.columnconfigure(i, weight=1) for i in range(self.info_cols)]
        [self.info_frame.rowconfigure(i, weight=1, minsize=10) for i in range(self.info_rows)]
        self.info_frame.grid_propagate(False)

        self.btns_frame = tk.Frame(self.mid_frame, bg='#dde9f3')
        self.btns_frame.grid(row=1, column=1, sticky='nsew', padx=(5, 5), pady=(5, 5)) # padx is 15 to have this frame the same size as the others
        self.btns_frame.columnconfigure(0, weight=1)
        # self.btns_frame.columnconfigure(1, weight=1)
        self.btns_frame.rowconfigure(0, weight=1)
        self.btns_frame.grid_propagate(False)

        style = ttk.Style(self)
        style.theme_use("default")

        style.configure("custom.Horizontal.TProgressbar", troughcolor='white', background='#2c3e50')

        self.progress_bar = ttk.Progressbar(self.progress_bar_frame, style="custom.Horizontal.TProgressbar", orient='horizontal', mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky='nsew', padx=(5, 5), pady=(15, 15))
        self.progress_bar['value'] = 50

        self.dropdown = ttk.Combobox(self.btns_frame, textvariable=tk.StringVar(), state='readonly', style="CustomCombobox.TCombobox")
        self.dropdown.bind("<<ComboboxSelected>>", self.defocus)

        self.create_layout_info()
        self.update_info()

        self.fncs = {
                        "Robot": [self.move_robot_home, self.move_robot_change_tool_pose, self.remove_pack_cover, self.pickup_cells], 
                        "Vision": [self.classify_pack, self.locate_pack, self.check_cover_off, self.classify_cells, self.locate_cells, self.assess_cells_qualities], 
                        "Human": [self.swap_tool, self.confirm_pack_fastened, self.add_pack_bb, self.choose_diff_pack_model, self.confirm_pack, 
                                  self.add_cell_bb, self.choose_diff_cell_model, self.confirm_cells, self.confirm_quals], 
                        }
        fncs_idx, col = 0, 0
        [self.fncs_frame.columnconfigure(i, weight=1) for i in range(2)]
        for i, cat in enumerate(self.fncs):
            if i == len(self.fncs)-1:
                fncs_idx = 0
                col = 1
            self.human_label = tk.Label(self.fncs_frame, text=f"{cat} functions:", background='#f0f4f7', fg='#2c3e50')
            self.human_label.grid(row=fncs_idx, column=col, sticky='nsew', padx=(5, 5), pady=(5, 0))
            self.fncs_frame.rowconfigure(fncs_idx, weight=1)
            fncs_idx += 1
            for fnc in self.fncs[cat]:
                btn = tk.Button(self.fncs_frame, text=fnc.__name__.capitalize().replace("_", " "),command=fnc)
                btn.grid(row=fncs_idx, column=col, sticky='nsew', padx=(5, 5))
                self.fncs_frame.rowconfigure(fncs_idx, weight=1)
                fncs_idx += 1

    def defocus(self, event):
        self.dropdown.selection_clear()
        if self.changing_pack_model:
            self.pack_state.model = self.dropdown.get()
            if self.pack_bb_drawer is not None:
                self.pack_bb_drawer.set_label(self.pack_state.model)
        elif self.changing_cell_model:
            self.pack_state.cell_model = self.dropdown.get()
            for c in self.pack_state.cells:
                c.model = self.pack_state.cell_model
            self.cells_bb_drawer.set_color_icon(self.cells_icon_color[self.pack_state.cell_model])
        self.update_info()

    def create_layout_info(self):
        self.pmodel_label = tk.Label(self.info_frame, background='#f0f4f7', fg='#2c3e50')
        self.pmodel_label.grid(row=0, column=0, sticky='nsew', padx=(0, 0), pady=(0, 0))
        self.cover_on_label = tk.Label(self.info_frame, background='#f0f4f7', fg='#2c3e50')
        self.cover_on_label.grid(row=1, column=0, sticky='nsew', padx=(0, 0), pady=(0, 0))
        self.psize_label = tk.Label(self.info_frame, background='#f0f4f7', fg='#2c3e50')
        self.psize_label.grid(row=2, column=0, sticky='nsew', padx=(0, 0), pady=(0, 0))
        self.fpos_label = tk.Label(self.info_frame, background='#f0f4f7', fg='#2c3e50')
        self.fpos_label.grid(row=3, column=0, sticky='nsew', padx=(0, 0), pady=(0, 0))
        self.rpos_label = tk.Label(self.info_frame, background='#f0f4f7', fg='#2c3e50')
        self.rpos_label.grid(row=4, column=0, sticky='nsew', padx=(0, 0), pady=(0, 0))
        
        self.cmodel_label = tk.Label(self.info_frame, background='#f0f4f7', fg='#2c3e50')
        self.cmodel_label.grid(row=0, column=1, sticky='nsew', padx=(0, 0), pady=(0, 0))
        self.nr_cells_label = tk.Label(self.info_frame, background='#f0f4f7', fg='#2c3e50')
        self.nr_cells_label.grid(row=0, column=2, sticky='nsew', padx=(0, 0), pady=(0, 0))
        self.cells_labels = []

        self.extra_label = tk.Label(self.info_frame, background='#f0f4f7', fg='#2c3e50')
        self.extra_label.grid(row=0, column=3, sticky='nsew', padx=(0, 0), pady=(0, 0))

    def update_info(self):
        self.pmodel_label.configure(text=f"Pack model: {self.pack_state.model}")
        self.cover_on_label.configure(text=f"Cover on: {self.pack_state.cover_on if self.pack_state.cover_on is not None else 'unknown'}")
        self.psize_label.configure(text=f"Pack size: {self.pack_state.size if self.pack_state.size is not None else 'unknown'}")
        self.fpos_label.configure(text=f"Location in frame: {self.pack_state.frame_location if self.pack_state.frame_location is not None else 'unknown'}")
        self.rpos_label.configure(text=f"Real world position: {self.pack_state.pose.t if self.pack_state.pose is not None else 'unknown'}")
        self.cmodel_label.configure(text=f"Cells model : {self.pack_state.cell_model}")
        self.nr_cells_label.configure(text=f"# cells: {len(self.pack_state.cells) if len(self.pack_state.cells)!=0 else 'unknown'}")
        self.extra_label.configure(text=f"Active tcp: {self.robot_module.active_gripper}")
        if len(self.cells_labels) == 0:
            for i, cell in enumerate(self.pack_state.cells):
                label = tk.Label(self.info_frame, text=f"{i:02d}: "+cell.to_string_short(), background='#f0f4f7', fg='#2c3e50')
                label.grid(row=(i%(self.info_rows-1))+1, column=(i//self.info_cols)+1, sticky='nsew', padx=(0, 0), pady=(0, 0))
                self.cells_labels.append(label)
        for i, c_label in enumerate(self.cells_labels):
            c_label.configure(text=f"{i:02d}: "+self.pack_state.cells[i].to_string_short())

    def confirm_pack_fastened(self):
        self.logger.info("START: pack fastened confirmed")
        self.state['pack_fastened'] = True
        self.logger.info("END: pack fastened confirmed")

    def add_pack_bb(self):
        self.logger.info("START: add pack bounding box")
        self.pack_bb_drawer.editable = True
        self.pack_bb_drawer.clear_bbs()
        x, y = self.home_frame.canvas.winfo_width() // 2, self.home_frame.canvas.winfo_height() // 2
        self.pack_bb_drawer.add_bb([x-100, y-100, x+100, y+100])
        self.logger.info("END: add pack bounding box")

    def locate_pack_deprecated(self):
        self.logger.info("START: locate_pack")
        result = self.vision_module.locate_pack(self.camera_frame)
        if result is not None:
            self.pack_state.model = result['shape']
            self.pack_state.size = result['size']
            self.pack_state.cover_on = result['cover_on']
            self.pack_state.frame_location = result['location']
            self.pack_state.pose = self.vision_module.frame_pos_to_pose(result['location'], self.robot_module.get_TCP_pose())
            self.logger.debug(self.pack_state)
            self.logger.info("pack located")
            
            x_min, y_min = self.pack_state.frame_location[0] - self.pack_state.size[0]//2, self.pack_state.frame_location[1] - self.pack_state.size[1]//2
            x_max, y_max = self.pack_state.frame_location[0] + self.pack_state.size[0]//2, self.pack_state.frame_location[1] + self.pack_state.size[1]//2
            self.pack_bb_drawer.editable = True
            self.pack_bb_drawer.clear_bbs()
            self.pack_bb_drawer.set_label(self.pack_state.model)
            self.pack_bb_drawer.add_bb([x_min, y_min, x_max, y_max])
            self.update_info()
        else:
            self.pack_state.cover_on = False
            self.state['pack_confirmed'] = True
            self.logger.info("The cover seems to be already off")
        self.logger.info("END: locate_pack")
    
    def classify_pack(self):
        self.logger.info("START: classify pack")
        if self.state['pack_fastened'] and not self.state['pack_confirmed']:
            result = self.vision_module.locate_pack(self.camera_frame)
            if result is not None:
                self.pack_state.model = result['shape']
                self.pack_state.size = result['size']
                self.pack_state.cover_on = result['cover_on']
                self.pack_bb_drawer.set_label(self.pack_state.model)
                self.logger.debug(self.pack_state)
                self.logger.info("pack classified")
                self.update_info()
        else:
            self.logger.info("Requisites not met")
        self.logger.info("END: classify pack")

    def locate_pack(self):
        self.logger.info("START: locate pack")
        result = self.vision_module.locate_pack(self.camera_frame)
        if self.state['pack_fastened'] and not self.state['pack_confirmed']:
            if result is not None:
                self.pack_state.frame_location = result['location']
                self.pack_state.pose = self.vision_module.frame_pos_to_pose(result['location'], self.robot_module.get_TCP_pose())
                self.logger.debug(self.pack_state)
                self.logger.info("pack located")
                self.pack_state.size = result['size']
                x_min, y_min = self.pack_state.frame_location[0] - self.pack_state.size[0]//2, self.pack_state.frame_location[1] - self.pack_state.size[1]//2
                x_max, y_max = self.pack_state.frame_location[0] + self.pack_state.size[0]//2, self.pack_state.frame_location[1] + self.pack_state.size[1]//2
                self.pack_bb_drawer.editable = True
                self.pack_bb_drawer.clear_bbs()
                self.pack_bb_drawer.set_label(self.pack_state.model)
                self.pack_bb_drawer.add_bb([x_min, y_min, x_max, y_max])
                self.update_info()
        else:
            self.logger.info("Requisites not met")
        self.logger.info("END: locate pack")

    def check_cover_off(self):
        self.logger.info("START: check cover off")
        result = self.vision_module.locate_pack(self.camera_frame)
        if result is None:
            self.pack_state.cover_on = False
            self.state['pack_confirmed'] = True
            self.logger.info("The cover seems to be off")
        else:
            self.logger.info("The cover seems to be on still")
        self.logger.info("END: check cover off")

    def swap_tool(self):
        self.logger.info("START: swap tool")
        if self.robot_module.active_gripper == "small":
            self.robot_module.change_gripper("big")
        elif self.robot_module.active_gripper == "big":
            self.robot_module.change_gripper("small")
        self.update_info()
        self.logger.info("END: swap tool")

    def move_robot_home(self):
        self.logger.info("START: robot move to home")
        self.robot_module.move_to_home()
        self.logger.info("END: robot move to home")
    
    def move_robot_change_tool_pose(self):
        self.logger.info("START: move_robot_change_tool_pose")
        self.robot_module.robot.moveJ(self.swap_q)
        self.logger.info("END: move_robot_change_tool_pose")
    
    def choose_diff_pack_model(self):
        self.logger.info("START: Choose diff pack model")
        self.dropdown.grid(row=0, column=0, sticky='nsew', padx=(25, 5), pady=(25, 25))
        # TODO: should come from database not hardocoded
        self.dropdown['values'] = self.pack_models
        self.dropdown.current(self.pack_models.index(self.pack_state.model))
        self.changing_pack_model = True
        self.changing_cell_model = False
        self.logger.info("END: Choose diff pack model")

    def confirm_pack(self):
        self.logger.info(f"Pack bounding box confirmed")
        self.state['pack_confirmed'] = True
        self.pack_bb_drawer.lock()
        self.dropdown.grid_forget()
        x_min, y_min, x_max, y_max = self.pack_bb_drawer.bbs_position[0]
        center_x = (x_min + x_max) // 2
        center_y = (y_min + y_max) // 2
        self.pack_state.frame_location = [center_x, center_y]
        self.pack_state.pose = self.vision_module.frame_pos_to_pose([center_x, center_y], self.robot_module.get_TCP_pose())
        self.pack_state.size = (x_max - x_min, y_max - y_min)
        self.changing_pack_model = False
        self.update_info()

    def remove_pack_cover(self):
        self.logger.info("START: remove_pack_cover")
        if self.state['pack_confirmed']:
            self.logger.info("requisites ok")
            self.robot_module.pick_and_place(self.pack_state.pose, self.cover_place_pose)
            self.robot_module.move_to_home()
            time.sleep(0.5)
            self.camera_frame = self.vision_module.get_current_frame(format='pil')
            if self.vision_module.locate_pack(self.camera_frame) is None:
                self.logger.info("cover removed!")
                self.pack_state.cover_on = False
            else:
                self.logger.info("cover not removed correctly")
        else:
            self.logger.info("requisites not met")
        self.logger.info("END: remove_pack_cover")

    def add_cell_bb(self):
        self.logger.info("START: add cell bounding box")
        
        self.cells_bb_drawer = _BoundingBoxEditor(self.home_frame.canvas, self.home_frame, tag='cells') if self.cells_bb_drawer is None else self.cells_bb_drawer
        self.cells_bb_drawer.editable = True
            
        x, y = self.home_frame.canvas.winfo_width() // 2, self.home_frame.canvas.winfo_height() // 2
        self.cells_bb_drawer.add_bb([x-50, y-50, x+50, y+50])
        self.logger.info("END: add cell bounding box")

    def identify_cells_deprecated(self):
        self.logger.info("START: identify_cells deprecated")
        if not self.pack_state.cover_on:
            self.logger.info("requisites ok")
            result = self.vision_module.identify_cells(self.camera_frame)
            drawing_bbs = []
            self.pack_state.cells = []

            # sometime the depth sensor does not correctly pick up the z, the cells are all the sae model so height as well so we can just fill in
            median_z = np.median([z for z in result['zs'] if z!= 0])

            for bb, z in zip(result['bbs'], result['zs']):
                x, y, w = bb
                cell_z = median_z if abs(z-median_z) > 0.01 else z
                pose = self.vision_module.frame_pos_to_pose((x, y), self.robot_module.get_TCP_pose(), Z=cell_z)
                self.pack_state.add_cell(result['model'], width=w, z=cell_z, pose=pose, frame_position=(x, y))
                drawing_bbs.append([x-w//2, y-w//2, x+w//2, y+w//2])
        
            self.cells_bb_drawer = _BoundingBoxEditor(self.home_frame.canvas, self.home_frame, tag='cells')
            self.cells_bb_drawer.editable = True
            self.cells_bb_drawer.clear_bbs()
            self.cells_bb_drawer.add_bbs(drawing_bbs)
            self.logger.debug(self.pack_state)
            self.logger.info(f"END: identified {len(self.pack_state.cells):02d} cells")
        else:
            self.logger.info("requisites not met")
        self.update_info()
        self.logger.info("END: identify_cells deprecated")

    def classify_cells(self):
        self.logger.info("START: classify cells")
        if self.pack_state.cover_on == False:
            self.logger.info("requisites ok")
            result = self.vision_module.identify_cells(self.camera_frame)
            self.pack_state.cell_model = (result['model'])
            if self.cells_bb_drawer is not None:
                self.cells_bb_drawer.set_color_icon(self.cells_icon_color[self.pack_state.cell_model])
            self.logger.debug(self.pack_state)
            self.logger.info(f"classified cells as {self.pack_state.cell_model}")
        else:
            self.logger.info("requisites not met")
        self.update_info()
        self.logger.info("END: classify cell")
        
    def locate_cells(self):
        self.logger.info("START: locate cells")
        if self.pack_state.cover_on == False:
            self.logger.info("requisites ok")
            result = self.vision_module.identify_cells(self.camera_frame)
            drawing_bbs = []
            self.pack_state.cells = []

            # sometime the depth sensor does not correctly pick up the z, the cells are all the sae model so height as well so we can just fill in
            median_z = np.median([z for z in result['zs'] if z!= 0])

            for bb, z in zip(result['bbs'], result['zs']):
                x, y, w = bb
                cell_z = median_z if abs(z-median_z) > 0.01 else z
                pose = self.vision_module.frame_pos_to_pose((x, y), self.robot_module.get_TCP_pose(), Z=cell_z)
                self.pack_state.add_cell(self.pack_state.cell_model, width=w, z=cell_z, pose=pose, frame_position=(x, y))
                drawing_bbs.append([x-w//2, y-w//2, x+w//2, y+w//2])
        
            self.cells_bb_drawer = _BoundingBoxEditor(self.home_frame.canvas, self.home_frame, tag='cells')
            self.cells_bb_drawer.editable = True
            self.cells_bb_drawer.clear_bbs()
            self.cells_bb_drawer.add_bbs(drawing_bbs)
            self.cells_bb_drawer.set_color_icon(self.cells_icon_color[self.pack_state.cell_model])
            self.logger.debug(self.pack_state)
            self.logger.info(f"localized {len(self.pack_state.cells):02d} cells")
        else:
            self.logger.info("requisites not met")
        self.update_info()
        self.logger.info("END: locate cells")

    def choose_diff_cell_model(self):
        self.logger.info("START: Choose diff cell model")
        self.dropdown.grid(row=0, column=0, sticky='nsew', padx=(25, 5), pady=(25, 25))
        self.changing_cell_model = True
        self.changing_pack_model = False
        # TODO: should come from database not hardocoded
        self.dropdown['values'] = self.cell_models
        self.dropdown.current(self.cell_models.index(self.pack_state.cell_model))
        self.logger.info("END: Choose diff cell model")

    def confirm_cells(self):
        self.logger.info(f"Cells bounding boxes confirmed")
        self.state['cells_confirmed'] = True
        self.cells_bb_drawer.lock()
        self.dropdown.grid_forget()
        for i, bb in enumerate(self.cells_bb_drawer.bbs_position):
            x_min, y_min, x_max, y_max = bb
            center_x = (x_min + x_max) // 2
            center_y = (y_min + y_max) // 2
            try:
                self.pack_state.cells[i].frame_location = [center_x, center_y]
                self.pack_state.cells[i].pose = self.vision_module.frame_pos_to_pose((center_x, center_y), self.robot_module.get_TCP_pose(), Z=self.pack_state.cells[i].z)
                self.pack_state.cells[i].width = x_max - x_min
                self.pack_state.cells[i].model = self.pack_state.cell_model # in case it has been changed
            except IndexError:
                if len(self.pack_state.cells) != 0:
                    z_cell = self.pack_state.cells[0].z
                else: # case in which the human has done everything by itself
                    z_cell = np.median([self.vision_module.get_z_at_pos(x=bb[0]+bb[2]//2, y=bb[1]+bb[3]//2) for bb in self.cells_bb_drawer.bbs_position])
                self.pack_state.add_cell(model=self.pack_state.cell_model, width=x_max-x_min, z=z_cell, 
                                         pose=self.vision_module.frame_pos_to_pose((center_x, center_y), self.robot_module.get_TCP_pose(), Z=z_cell), 
                                         frame_position=(center_x, center_y))
                    
                    
        self.vision_module.set_background()
        self.changing_cell_model = False
        self.logger.debug(self.pack_state)
        self.update_info()

    def assess_cells_qualities(self):
        self.logger.info("START: assess_cells_qualities")
        if self.state['cells_confirmed']:
            self.quals_editor = _QualitiesEditor(self.home_frame.canvas, cell_m_q=self.cell_m_q, cell_h_q=self.cell_h_q)
            self.logger.info("requisites ok")
            bbs = []
            drawing_bbs = []
            for cell in self.pack_state.cells:
                bbs.append(cell.frame_location)
                drawing_bbs.append([cell.frame_location[0] - cell.width//2, cell.frame_location[1] - cell.width//2, cell.frame_location[0] + cell.width//2, cell.frame_location[1] + cell.width//2])
            qualities = self.vision_module.assess_cells_qualities(self.camera_frame, bbs)
            self.quals_editor.add_quals(keep_bbs=qualities, bbs=drawing_bbs)
            for qual, cell in zip(qualities, self.pack_state.cells):
                cell.keep = qual > self.cell_h_q
            self.logger.info(f"{sum(q > self.cell_h_q for q in qualities):02d} cells will be kept")
        else:
            self.logger.info("requisites not met")
        self.update_info()
        self.logger.info("END: assess_cells_qualities")
    
    def confirm_quals(self):
        self.logger.info(f"Cells qualities confirmed")
        self.state['quals_confirmed'] = True
        self.quals_editor.lock()
        for i, keep_cell in enumerate(self.quals_editor.keep_bbs):
            self.pack_state.cells[i].keep = keep_cell
            self.vision_module.set_background()
            self.update_info()

    def pickup_cells(self):
        self.logger.info("START: pickup_cells")
        if self.state['quals_confirmed']:
            for i, cell in enumerate(self.pack_state.cells):
                if not cell.sorted:
                    if cell.keep:
                        self.robot_module.pick_and_place(cell.pose, self.keep_T)
                        self.logger.info(f"END: cell {i} kept")
                    else:
                        self.robot_module.pick_and_place(cell.pose, self.discard_T)
                        self.logger.info(f"END: cell {i} discarded")
                    self.robot_module.move_to_home()
                    time.sleep(0.5)
                    cell.sorted = self.vision_module.verify_pickup(cell.frame_location, cell.width)
                    self.update_info()
                    self.write_outcome_picked_cells(scale=self.scale, padx=self.padx, pady=self.pady)
                    self.home_frame.canvas.update() # to write the outcome real time
            self.robot_module.move_to_home()
        else:
            self.logger.info("requisites not met")
        self.logger.info("END: pickup_cells")
                   
    def ask_for_help(self,  query: str):
        """ask human for help for something

        Args:
            query (str): the question/request for the human
        """
        pass

    def write_outcome_picked_cells(self, scale=1, padx=0, pady=0):
        """mark on the image whether or not the battery cell was picked up

        Args:
            bbs_position (list[ndarray]): postions of bounding boxes
        """
        self.home_frame.canvas.delete('outcome')
        for cell in self.pack_state.cells:
            if cell.sorted is None:
                break
            txt = "✗" if not cell.sorted else "✓"
            color = "firebrick" if not cell.sorted else "green2"
            x, y = cell.frame_location[0]*scale + padx, cell.frame_location[1]*scale + pady
            self.home_frame.canvas.create_text(x, y, text=txt, font=("Arial", 35), fill=color, tags='outcome')

    def show_frame_debug(self):
        drawing_frame = self.vision_module.get_current_frame()
        if self.pack_state.frame_location is not None:
            xy_min = (self.pack_state.frame_location[0]-self.pack_state.size[0]//2, self.pack_state.frame_location[1]-self.pack_state.size[1]//2)
            xy_max = (self.pack_state.frame_location[0]+self.pack_state.size[0]//2, self.pack_state.frame_location[1]+self.pack_state.size[1]//2)
            cv2.rectangle(drawing_frame, xy_min, xy_max, color=(0, 0, 255))
        for i, cell in enumerate(self.pack_state.cells):
            cv2.circle(drawing_frame, cell.frame_location, 1, (0, 100, 100), 3)
            cv2.circle(drawing_frame, cell.frame_location, cell.width//2, (255, 0, 255), 3)
            cv2.putText(drawing_frame, f"id: {i}; {cell.model}",      np.array(cell.frame_location)+(-30, -20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
            cv2.putText(drawing_frame, f"c: {cell.frame_location}",  np.array(cell.frame_location)+(-30, 0), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
            cv2.putText(drawing_frame, f"r: {cell.width//2}; z: {cell.z:0.3f}",    np.array(cell.frame_location)+(-30,  20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
        cv2.imshow("frame", drawing_frame)
        cv2.waitKey(1)

    def after_update(self):
        self.camera_frame = self.vision_module.get_current_frame(format='pil')
        self.scale, self.padx, self.pady = self.home_frame.draw_image(self.camera_frame)
        voice_command = self.voice_module.get_intent()
        if  voice_command is not None:
            self.logger.info(f"New voice command: {voice_command}")
        if self.verbose:
            self.show_frame_debug()
        if self.pack_bb_drawer is not None:
            self.pack_bb_drawer.draw_boxes(scale=self.scale, padx=self.padx, pady=self.pady)
        if self.cells_bb_drawer is not None:
            self.cells_bb_drawer.draw_boxes(scale=self.scale, padx=self.padx, pady=self.pady)
        if self.quals_editor is not None:
            self.quals_editor.write_qualities(scale=self.scale, padx=self.padx, pady=self.pady)
        if self.state['quals_confirmed']:
            self.write_outcome_picked_cells(scale=self.scale, padx=self.padx, pady=self.pady)
        self.after(1, self.after_update)

class HomeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.canvas = tk.Canvas(self)
        self.canvas.grid(row=0, column=0, sticky='nsew', padx=(0, 0), pady=(0, 0))
    
    def draw_image(self, img):
        scale = min(self.canvas.winfo_width() / img.size[0], self.canvas.winfo_height() / img.size[1])
        padx, pady = 0, 0
        if scale > .01:
            new_size = (int(scale * img.size[0]), int(scale * img.size[1]))
            resized_img = img.resize(new_size)
            padx = (self.canvas.winfo_width() - new_size[0]) // 2
            pady = (self.canvas.winfo_height() - new_size[1]) // 2
        else:
            resized_img = img
        self.tk_image = PIL.ImageTk.PhotoImage(resized_img)
        self.canvas.delete('image')
        self.canvas.create_image(self.canvas.winfo_width()//2, self.canvas.winfo_height()//2, anchor=tk.CENTER, image=self.tk_image, tags='image')
        self.canvas.lower('image')
        return scale, padx, pady

if __name__ == "__main__":
    camera_frame = cv2.imread("./data/camera_frame.png")
    camera_frame = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
    camera_frame = PIL.Image.fromarray(camera_frame)
    app = MemGui()
    app.after(1, app.after_update)
    app.mainloop()
