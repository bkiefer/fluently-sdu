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
from fluently_MQTT_client import FluentlyMQTTClient
import PIL.Image
import PIL.ImageTk
import sys
from numpy import ndarray
import tkinter as tk
from tkinter import ttk
import cv2
import PIL
import numpy as np
import paho.mqtt.client as mqtt
import json

class _BoundingBoxEditor:
    def __init__(self, canvas, frame, tag=''):
        self.canvas = canvas
        self.selected_box = None
        self.dragging = None  # "move" or "resize"
        self.start_x = 0
        self.start_y = 0
        # self.delete_mode = False
        self.frame = frame
        self.label = None
        self.tag = tag

        self.boxes_items = []  # Store drawn objects
        self.bbs_position = []

        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.editable = True

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
            move_handle = self.canvas.create_oval(center_x-5, center_y-5, center_x+5, center_y+5, fill="blue", tags='bbs' + self.tag)
            resize_handle = self.canvas.create_rectangle(x_min-5, y_min-5, x_min+5, y_min+5, fill="red", tags='bbs' + self.tag)
            delete_handle = self.canvas.create_text(x_max, y_min, text="X", fill="red", font=("Arial", 10), tags = 'bbs' + self.tag)
            self.boxes_items.append([move_handle, resize_handle, delete_handle])
        # self.boxes_items.append([box, move_handle, resize_handle, text_bg, text_label, delete_btn, delete_label])        
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
        self.title("MeM use case")
        
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

        """ ========== MODULE SETUP ========== """
        verbose = False
        self.logger = utilities.CustomLogger("MeM", "MeM.log", console_level='info' if not verbose else 'debug')
        self.vision_module = VisionModule(camera_Ext=self.camera_Ext, verbose=verbose)
        self.robot_module = RobotModule(ip="192.168.1.100", home_position=home_pos, tcp_length_dict={'small': -0.072, 'big': -0.08}, active_gripper='big', gripper_id=0, verbose=verbose)
        self.pack_state = PackState()
        self.robot_module.move_to_home()
        # self.logger.toggle_offon()

        """ ========== RESET GUI ========== """
        self.state = {"pack_confirmed" : True, "cells_confirmed" : False, "quals_confirmed" : False}
        self.pack_models = ["Square", "Trapezoid"]
        self.cell_models = ["aaa", "bbb", "ccc"]

        """ ========== LAYOUT GUI ========== """
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        
        self.fncs_container = tk.Frame(self,  bg='antique white')
        self.fncs_container.grid(row=0, column=0, sticky='nsew', padx=(5, 0), pady=(0, 5))
        self.fncs_container.grid_columnconfigure(0, weight=1)
        
        for i, fnc in enumerate([self.add_pack_bb, self.locate_pack, self.remove_pack_cover, self.identify_cells, self.assess_cells_qualities, self.pickup_cells]):
            btn = tk.Button(self.fncs_container, text=fnc.__name__, command=fnc)
            self.fncs_container.rowconfigure(i, weight=1)
            btn.grid(row=i, column=0, sticky='nsew', padx=(5, 5))
        
        self.frame = HomeScreen(self, self)
        self.frame.grid(row=0, column=1, rowspan=2, sticky='nsew')
        self.frame.grid_rowconfigure(0, weight=1)
    
        self.btns_container = tk.Frame(self, bg='antique white')
        self.btns_container.grid(row=1, column=0, sticky='nsew', padx=(5, 0), pady=(5, 0))
        self.btns_container.grid_columnconfigure(0, weight=1)

        self.yes_btn = tk.Button(self.btns_container, text="✔", font=("Arial", 12))
        self.tmp_btns = []
        
        self.pack_bb_drawer = _BoundingBoxEditor(self.frame.canvas, self.frame, tag='pack')
        self.cells_bb_drawer = None
        self.quals_editor = None

        # DEBUG
        self.pack_state.cover_on = False
        self.cells_bb_drawer = _BoundingBoxEditor(self.frame.canvas, self.frame, tag='cells')

    def add_pack_bb(self):
        self.logger.info("START: add pack bounding box")
        self.pack_bb_drawer.editable = True
        self.pack_bb_drawer.clear_bbs()
        self.pack_bb_drawer.add_bb([500, 500, 1000, 1000])
        self.yes_btn.pack(fill="x", side="bottom", padx=(5, 5))
        self.yes_btn.config(command=self.confirm_pack)
        for btn in self.tmp_btns:
            btn.pack_forget()
        for propose in self.pack_models:
            btn = tk.Button(self.btns_container, text=propose, font=("Arial", 12), command= lambda model=propose: self.choose_diff_pack_model(model=model))
            btn.pack(fill="both", padx=(5, 5))
            self.tmp_btns.append(btn)
        self.logger.info("END: add pack bounding box")

    def locate_pack(self):
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

            self.yes_btn.pack(fill="x", side="bottom", padx=(5, 5))
            self.yes_btn.config(command=self.confirm_pack)

            # should come from database instead then hardcoded
            for btn in self.tmp_btns:
                btn.pack_forget()
            for propose in self.pack_models:
                btn = tk.Button(self.btns_container, text=propose, font=("Arial", 12), command= lambda model=propose: self.choose_diff_pack_model(model=model))
                btn.pack(fill="both", padx=(5, 5))
                self.tmp_btns.append(btn)
        else:
            self.pack_state.cover_on = False
            self.state['pack_confirmed'] = True
            self.cells_bb_drawer = _BoundingBoxEditor(self.frame.canvas, self.frame, tag='cells')
            self.logger.info("The cover seems to be already off")
        self.logger.info("END: locate_pack")
    
    def remove_pack_cover(self):
        self.logger.info("START: remove_pack_cover")
        if self.state['pack_confirmed']:
            self.logger.info("requisites ok")
            self.robot_module.pick_and_place(self.pack_state.pose, self.cover_place_pose)
            self.robot_module.move_to_home()
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
        self.cell_bb_drawer.editable = True
        self.cell_bb_drawer.clear_bbs()
        self.cell_bb_drawer.add_bb([500, 500, 1000, 1000])
        self.yes_btn.pack(fill="x", side="bottom", padx=(5, 5))
        self.yes_btn.config(command=self.confirm_cells)
        for btn in self.tmp_btns:
            btn.pack_forget()
        for propose in self.cell_models:
            btn = tk.Button(self.btns_container, text=propose, font=("Arial", 12), command= lambda model=propose: self.choose_diff_cell_model(model=model))
            btn.pack(fill="both", padx=(5, 5))
            self.tmp_btns.append(btn)
        self.logger.info("END: add cell bounding box")

    def identify_cells(self):
        self.logger.info("START: identify_cells")
        if not self.pack_state.cover_on:
            self.logger.info("requisites ok")
            result = self.vision_module.identify_cells(self.camera_frame)
            drawing_bbs = []
            self.pack_state.cells = []
            for bb, z in zip(result['bbs'], result['zs']):
                x, y, w = bb
                pose = self.vision_module.frame_pos_to_pose((x, y), self.robot_module.get_TCP_pose())
                self.pack_state.add_cell(result['model'], width=w, z=z, pose=pose, frame_position=(x, y))
                drawing_bbs.append([x-w//2, y-w//2, x+w//2, y+w//2])
            self.cells_bb_drawer.editable = True
            self.cells_bb_drawer.clear_bbs()
            self.cells_bb_drawer.add_bbs(drawing_bbs)
            self.yes_btn.pack(fill="x", side="bottom", padx=(5, 5))
            self.yes_btn.config(command=self.confirm_cells)

            # should come from database instead then hardcoded
            for btn in self.tmp_btns:
                btn.pack_forget()
            for propose in self.cell_models:
                btn = tk.Button(self.btns_container, text=propose, font=("Arial", 12), command= lambda model=propose: self.choose_diff_cell_model(model=model))
                btn.pack(fill="both", padx=(5, 5))
                self.tmp_btns.append(btn)
            self.logger.debug(self.pack_state)
            self.logger.info(f"END: identified {len(self.pack_state.cells):02d} cells")
        else:
            self.logger.info("requisites not met")
        self.logger.info("END: identify_cells")

    def assess_cells_qualities(self):
        self.logger.info("START: assess_cells_qualities")
        if self.state['cells_confirmed']:
            self.logger.info("requisites ok")
            bbs = []
            drawing_bbs = []
            for cell in self.pack_state.cells:
                bbs.append(cell.frame_position)
                drawing_bbs.append([cell.frame_position[0] - cell.width//2, cell.frame_position[1] - cell.width//2, cell.frame_position[0] + cell.width//2, cell.frame_position[1] + cell.width//2])
            qualities = self.vision_module.assess_cells_qualities(self.camera_frame, bbs)
            self.quals_editor.add_quals(keep_bbs=qualities, bbs=drawing_bbs)
            for qual, cell in zip(qualities, self.pack_state.cells):
                cell.keep = qual > self.cell_h_q
            self.logger.info(f"{sum(q > self.cell_h_q for q in qualities):02d} cells will be kept")

            self.yes_btn.pack(fill="x", side="bottom", padx=(5, 5))
            self.yes_btn.config(command=self.confirm_quals)
        else:
            self.logger.info("requisites not met")
        self.logger.info("END: assess_cells_qualities")
    
    def pickup_cells(self):
        # TODO: 
        # check prerequisites 
        # verify pickup
        self.logger.info("START: pickup_cells")
        if self.state['quals_confirmed']:
            for i, cell in enumerate(self.pack_state.cells):
                if cell.keep:
                    self.robot_module.pick_and_place(cell.pose, self.discard_T)
                    self.logger.info(f"END: cell {i} discarded")
                else:
                    self.robot_module.pick_and_place(cell.pose, self.keep_T)
                    self.logger.info(f"END: cell {i} kept")
                cell.sorted = self.vision_module.verify_pickup(cell.frame_position, cell.width)
                self.write_outcome_picked_cells(scale=self.scale, padx=self.padx, pady=self.pady)
                self.frame.canvas.update() # to write the outcome real time
            self.robot_module.move_to_home()
        else:
            self.logger.info("requisites not met")
        self.logger.info("END: pickup_cells")

    def confirm_pack(self):
        self.logger.info(f"Pack bounding box confirmed")
        self.state['pack_confirmed'] = True
        for btn in self.tmp_btns:
            btn.pack_forget()
        self.yes_btn.pack_forget()
        self.pack_bb_drawer.lock()
        x_min, y_min, x_max, y_max = self.pack_bb_drawer.bbs_position[0]
        center_x = (x_min + x_max) // 2
        center_y = (y_min + y_max) // 2
        self.pack_state.frame_location = [center_x, center_y]
        self.pack_state.size = (x_max - x_min, y_max - y_min)
        self.cells_bb_drawer = _BoundingBoxEditor(self.frame.canvas, self.frame, tag='cells')

    def confirm_cells(self):
        self.logger.info(f"Cells bounding boxes confirmed")
        self.state['cells_confirmed'] = True
        for btn in self.tmp_btns:
            btn.pack_forget()
        self.yes_btn.pack_forget()
        self.cells_bb_drawer.lock()
        for i, bb in enumerate(self.cells_bb_drawer.bbs_position):
            x_min, y_min, x_max, y_max = bb
            center_x = (x_min + x_max) // 2
            center_y = (y_min + y_max) // 2
            self.pack_state.cells[i].frame_position = [center_x, center_y]
            self.pack_state.cells[i].width = x_max - x_min
            self.vision_module.set_background()
        self.quals_editor = _QualitiesEditor(self.frame.canvas, cell_m_q=self.cell_m_q, cell_h_q=self.cell_h_q)
        
    def confirm_quals(self):
        self.logger.info(f"Cells qualities confirmed")
        self.state['quals_confirmed'] = True
        self.yes_btn.pack_forget()
        self.quals_editor.lock()
        for i, keep_cell in enumerate(self.quals_editor.keep_bbs):
            self.pack_state.cells[i].keep = keep_cell
            self.vision_module.set_background()
        
    # def confirm(self, var: str):
    #     self.logger.info(f"{var} now True")
    #     self.state[var] = True
    #     for btn in self.tmp_btns:
    #         btn.pack_forget()
    #     self.yes_btn.pack_forget()

    def choose_diff_pack_model(self, model: str):
        self.logger.info(f"Pack model chosen: {model}")
        self.pack_state.model = model
        self.pack_bb_drawer.set_label(model)
            
    def choose_diff_cell_model(self, model: str):
        self.logger.info(f"Cell model chosen: {model}")
        for cell in self.pack_state.cells:
            cell.model = model

    def ask_for_help(self,  query: str):
        """ask human for help for something

        Args:
            query (str): the question/request for the human
        """
        pass

    # def write_qualities(self, qualities: list[float], frame: tk.Frame, editable=False):
    #     """write the quality of each cell on the frame showed to the user

    #     Args:
    #         bbs_position (list[ndarray]): postions of bounding boxes for each cell
    #         qualities (list[float]): qualities of each cell
    #     """
    #     self.proposed_qualities = qualities    

    def write_outcome_picked_cells(self, scale=1, padx=0, pady=0):
        """mark on the image whether or not the battery cell was picked up

        Args:
            bbs_position (list[ndarray]): postions of bounding boxes
        """
        self.frame.canvas.delete('outcome')
        for cell in self.pack_state.cells:
            if cell.sorted is None:
                break
            txt = "✗" if not cell.sorted else "✓"
            color = "firebrick" if not cell.sorted else "green2"
            x, y = cell.frame_position[0]*scale + padx, cell.frame_position[1]*scale + pady
            self.frame.canvas.create_text(x, y, text=txt, font=("Arial", 35), fill=color, tags='outcome')

    def show_frame_debug(self):
        drawing_frame = self.vision_module.get_current_frame()
        if self.pack_state.frame_location is not None:
            xy_min = (self.pack_state.frame_location[0]-self.pack_state.size[0]//2, self.pack_state.frame_location[1]-self.pack_state.size[1]//2)
            xy_max = (self.pack_state.frame_location[0]+self.pack_state.size[0]//2, self.pack_state.frame_location[1]+self.pack_state.size[1]//2)
            cv2.rectangle(drawing_frame, xy_min, xy_max, color=(0, 0, 255))
        for i, cell in enumerate(self.pack_state.cells):
            cv2.circle(drawing_frame, cell.frame_position, 1, (0, 100, 100), 3)
            cv2.circle(drawing_frame, cell.frame_position, cell.width//2, (255, 0, 255), 3)
            cv2.putText(drawing_frame, f"id: {i}; {cell.model}",      np.array(cell.frame_position)+(-30, -20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
            cv2.putText(drawing_frame, f"c: {cell.frame_position}",  np.array(cell.frame_position)+(-30, 0), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
            cv2.putText(drawing_frame, f"r: {cell.width//2}; z: {cell.z:0.3f}",    np.array(cell.frame_position)+(-30,  20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)
        cv2.imshow("frame", drawing_frame)
        cv2.waitKey(1)

    def after_update(self):
        self.camera_frame = self.vision_module.get_current_frame(format='pil')
        self.scale, self.padx, self.pady = self.frame.draw_image(self.camera_frame)
        # self.show_frame_debug()
        
        """TODO : remove"""
        # if self.state['pack_confirmed'] and self.pack_bb_drawer.editable:
            # self.pack_bb_drawer.lock()
            # self.cells_bb_drawer = _BoundingBoxEditor(self.frame.canvas, self.frame, tag='cells')
            # x_min, y_min, x_max, y_max = self.pack_bb_drawer.bbs_position
        #     center_x = (x_min + x_max) // 2
        #     center_y = (y_min + y_max) // 2
        #     self.pack_state.frame_location = [center_x, center_y]
        if self.pack_bb_drawer is not None:
            self.pack_bb_drawer.draw_boxes(scale=self.scale, padx=self.padx, pady=self.pady)
        """TODO : remove"""
        # if self.state['cells_confirmed'] and self.cells_bb_drawer.editable:
        #     self.cells_bb_drawer.lock()
            # self.quals_editor = _QualitiesEditor(self.frame.canvas, cell_m_q=self.cell_m_q, cell_h_q=self.cell_h_q)
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
        self.canvas.pack(fill='both', expand=True)
    
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
    camera_frame = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
    camera_frame = PIL.Image.fromarray(camera_frame)
    app = MemGui()
    app.after(1, app.after_update)
    app.mainloop()
