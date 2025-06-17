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
import paho.mqtt.client as mqtt
import json

class FluentlyMQTTClient:
    def __init__(self, client_id: str, broker: str = "localhost", port: int = 1883):
        self.client = mqtt.Client(client_id=client_id)
        self.broker = broker
        self.port = port
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.message_callback = None
        self.connect()
        self.start()
        self.subscribe("nlu/intent")
        self.intent = []
        self.state = 1
        self.command_given = False

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")

    def on_message(self, client, userdata, msg):
        message = msg.payload.decode()
        topic = msg.topic
        print(f"Received message on topic '{topic}': {message}")
        self.intent.append(message)
        if self.message_callback:
            self.message_callback(topic, message)

    def connect(self):
        self.client.connect(self.broker, self.port, keepalive=60)

    def start(self):
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic: str):
        self.client.subscribe(topic)
        print(f"Subscribed to topic '{topic}'")

    def publish(self, message_: str):
        topic = "tts/behaviour"
        message ={  "id": "fluently",
            "text": message_,
            "motion": "",
            "delay": 0}
        try:
            json_message = json.dumps(message)
            self.client.publish(topic, json_message)
            print(message_)
        except (TypeError, ValueError) as e:
            print(f"Failed to serialize message to JSON: {e}")

    def set_message_callback(self, callback):
        self.message_callback = callback

    def get_intent(self):
        if len(self.intent) >=1:
            ans = self.intent[-1]
            self.intent = []
            return ans
        else:
            return None
        
    def clear_intents(self):
        self.intent.clear()

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
        x_min, y_min, x_max, y_max = 500, 500, 1000, 1000 
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
            
            self.canvas.lift("bbs")
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
    def __init__(self, canvas, bbs_position, qualities, cell_m_q,  cell_h_q, editable=False):
        self.canvas = canvas
        self.bbs_position = bbs_position
        self.qualities = qualities

        self.m, self.h = cell_m_q, cell_h_q        
        
        self.old_quality = None
        self.editing = False
        self.editing_qual_id = None
        self.edit_entry = tk.Entry(self.canvas, width=4, font=("Arial", 7), justify="center")

        self.boxes = []
        self.write_qualities()
        if editable:
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
        try:
            new_q = float(self.edit_entry.get()) / 100
            if not 0 < new_q < 1: 
                raise ValueError
            self.qualities[self.editing_qual_id] = new_q
            self.canvas.itemconfig(self.editing_item_id, text=f"{int(self.edit_entry.get()):02d}%")
            self.canvas.itemconfig(self.editing_item_id, fill='green2' if new_q > self.h else 'yellow2' if new_q > self.m else 'firebrick1')
            
        except:
            print("Inserted value not supported")
        finally:
            self.canvas.itemconfig(self.editing_item_id, state="normal")
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
        self.states = []
        
        self.camera_frame = camera_frame
        self.active_frame = 0
        
        # TODO: specify a correct one
        self.cover_place_pose = sm.SE3([0.068, -0.387, 0.306]) * sm.SE3.Rx(np.pi)
        self.cell_m_q, self.cell_h_q = 0.6, 0.8
        self.discard_T = sm.SE3([0.168, -0.487, 0.306]) * sm.SE3.Rx(np.pi)
        self.keep_T =    sm.SE3([0.110, -0.348, 0.302]) * sm.SE3.Rx(np.pi)
        R = sm.SO3([[-0.003768884463184431, -0.9999801870110973700,  0.0050419336721138118], 
            [0.9999374423980765800, -0.0038217260702308998, -0.0105121691499708400], 
            [0.0105312297618392200,  0.0050019991098505349,  0.9999320342926355500]])
        t = np.array([0.051939876523448010, -0.0323596382860819900,  0.0211982932413351600])
        self.camera_Ext = sm.SE3.Rt(R, t)

        # self.vision_module = VisionModule(camera_Ext=self.camera_Ext)
        # self.robot_module = RobotModule(ip="192.168.1.100", home_position=[0, 0, 0, 0, 0, 0], tcp_length_dict={'small': -0.072, 'big': -0.08}, active_gripper='big', gripper_id=0)
        # self.pack_state = PackState()

        self.proposed_models = []
        self.proposed_packs = None
        self.chosen_pack = ""
        self.chosen_model = ""
        self.proposed_locations = []
        self.chosen_locations = []
        self.chosen_pack_location = None
        self.proposed_qualities = []
        self.chosen_qualities = []
        self.outcomes = []
        self.class_reject = False # !!!
        self.done = False
        self.first_name = None
        self.last_name = None
        self.confirm = False
        self.gripper = ""
        self.removal_strategy = ""

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        
        self.btns_container = tk.Frame(self,  bg='antique white')
        self.btns_container.grid(row=0, column=0, sticky='nsew', padx=(5, 0))
        self.btns_container.grid_columnconfigure(0, weight=1)
        
        for i, fnc in enumerate([self.locate_pack, self.remove_pack_cover, self.identify_cells, self.assess_cells_qualities, self.pickup_cells]):
            btn = tk.Button(self.btns_container, text=fnc.__name__, command=fnc)
            btn.grid(row=i, column=0, sticky='nsew')
        
        self.frames = []
        self.frame = HomeScreen(self, self)
        self.frame.grid(row=0, column=1, sticky='nsew')
        self.frame.grid_rowconfigure(0, weight=1)

        self.reset_gui()

    def locate_pack(self):
        # TODO: check prerequisites
        print("locate_pack")
        # result = self.vision_module.locate_pack(self.camera_frame)
        # TODO: fill pack object with info
        # and draw on canvas
    
    def remove_pack_cover(self):
        # TODO: check prerequisites
        print("remove_pack_cover")
        # self.robot_module.pick_and_place(self.pack_state.pose, self.cover_place_pose)

    def identify_cells(self):
        # TODO: check prerequisites
        print("identify_cells")
        # result = self.vision_module.identify_cells(self.camera_frame)
        # print(result)
        # TODO: fill pack object with info
        # and draw on canvas

    def assess_cells_qualities(self):
        # TODO: check prerequisites
        print("assess_cells_qualities")
        # bbs = []
        # for cell in self.pack_state.cells:
        #     bbs.append(cell.frame_position)
        # result = self.vision_module.assess_cells_qualities(self.camera_frame, bbs)
        # print(result)
        # TODO: fill pack object with info
        # and draw on canvas
    
    def pickup_cells(self):
        # TODO: check prerequisites
        print("pickup_cells")
        # for cell in self.pack_state.cells:
        #     if cell.quality < self.cell_h_q:
        #         self.robot_module.pick_and_place(cell.pose, self.discard_T)
        #     else:
                # self.robot_module.pick_and_place(cell.pose, self.keep_T)

    def update_proposed_models(self, proposed_models):
        self.proposed_models = proposed_models
        self.frames[1].label.configure(text=f"Cells are: {self.proposed_models[0]}")
        for propose in self.proposed_models[1:]: # we skip the first one as it was already denied by the user
            btn = tk.Button(self.frames[2].btns_frame, text=f"{propose}", command=lambda model = propose: self.frames[2].chose_model(model))
            btn.pack()

    def update_proposed_packs(self, proposed_packs):
        self.proposed_packs = proposed_packs
        self.frames[15].label.configure(text=f"Pack is: {self.proposed_packs[0]}")
        for propose in self.proposed_packs[1:]: # we skip the first one as it was already denied by the user
            btn = tk.Button(self.frames[16].btns_frame, text=f"{propose}", command=lambda model = propose: self.frames[16].chosen_pack(model))
            btn.pack()

    def write_cell_state(self, x, y, cell: dict['model': str, 'bb': list[int], 'quality': float, 'pickedup': bool]):
        self.x_min = tk.Entry(self.btns_container, width=4, justify="center")
        self.x_min.insert(0, str(cell['bb'][0]))
        self.x_min.place(x=x, y=y)
        self.y_max = tk.Entry(self.btns_container, width=4, justify="center")
        self.y_max.insert(0, str(cell['bb'][2]))
        self.y_max.place(x=x+75, y=y)
        self.y_min = tk.Entry(self.btns_container, width=4, justify="center")
        self.y_min.insert(0, str(cell['bb'][1]))
        self.y_min.place(x=x, y=y+35)
        self.y_max = tk.Entry(self.btns_container, width=4, justify="center")
        self.y_max.insert(0, str(cell['bb'][3]))
        self.y_max.place(x=x+75, y=y+35)
    
    def show_frame(self):
        """update the state of the gui the current state will be hidden and the new one will be visible

        Args:
            state_id (int): id of new state
        """
        self.frame.tkraise()
        # self.expand_btn.place(x=self.camera_frame.width-50, y=self.camera_frame.height*1.2-50)
        self.frame.draw_image(self.camera_frame)

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

    def write_qualities(self, qualities: list[float], frame: tk.Frame, editable=False):
        """write the quality of each cell on the frame showed to the user

        Args:
            bbs_position (list[ndarray]): postions of bounding boxes for each cell
            qualities (list[float]): qualities of each cell
        """
        self.proposed_qualities = qualities
        self.quals_editor = _QualitiesEditor(frame.canvas, bbs_position=self.chosen_locations, qualities=qualities, cell_m_q=self.cell_m_q, cell_h_q=self.cell_h_q, editable=editable)

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

    def reset_gui(self):
        self.proposed_models = []
        self.chosen_model = ""
        self.chosen_pack = ""
        self.proposed_packs = None
        self.proposed_locations = []
        self.chosen_locations = []
        self.proposed_qualities = []
        self.chosen_qualities = []
        self.outcomes = []
        self.confirm = False
        self.class_reject = False # !!!
        self.done = False
        self.frame.canvas.delete("all")
        self.frame.draw_image(self.camera_frame)
        self.show_frame()

    def after_update(self):
        # self.camera_frame = self.vision_module.get_current_frame()
        self.frame.draw_image(self.camera_frame)
        self.after(1, self.after_update)

class HomeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.canvas = tk.Canvas(self)
        self.canvas.pack(fill='both', expand=True)
        self.draw_image(self.controller.camera_frame)
    
    def draw_image(self, img):
        scale = min(self.canvas.winfo_width() / img.size[0], self.canvas.winfo_height() / img.size[1])
        if scale > .01:
            new_size = (int(scale * img.size[0]), int(scale * img.size[1]))
            resized_img = img.resize(new_size)
        else:
            resized_img = img
        self.tk_image = PIL.ImageTk.PhotoImage(resized_img)
        self.canvas.delete('image')
        self.canvas.create_image(self.canvas.winfo_width()//2, self.canvas.winfo_height()//2, anchor=tk.CENTER, image=self.tk_image, tags='image')
        self.canvas.lower('image')

if __name__ == "__main__":
    camera_frame = cv2.imread("./data/camera_frame.png")
    camera_frame = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
    camera_frame = PIL.Image.fromarray(camera_frame)
    app = MemGui(camera_frame=camera_frame)
    app.after(1, app.after_update)
    app.mainloop()