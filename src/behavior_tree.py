import py_trees as pt
import time
#import rclpy
#import sys
#import os
from gui_module import MemGui
from robot_module import RobotModule
from battery_pack_module import PackState
from rdf_store import RdfStore
from vision_module import VisionModule
from behaviors import AutoClass, HelpedClass, Detect, Assess, AutoSort, HelpedSort, BeginSession
from viewer import BtViewer
import spatialmath as sm
import numpy as np

class BehaviourTree(pt.trees.BehaviourTree):
    def __init__(self):        
        # Blackboard and registering keys 
        self.blackboard = pt.blackboard.Client(name="Blackboard_client")   
        self.rdf = RdfStore()
        #self.rdf = None
        cell_m_q, cell_h_q = 0.6, 0.8                       # this defines them everywhere
        discard_T = sm.SE3([0, 0, 0]) * sm.SE3.Rx(np.pi)    # needs to be defined from the real setup
        keep_T = sm.SE3([0, 0, 0]) * sm.SE3.Rx(np.pi)       # needs to be defined from the real setup
        self.vision = VisionModule()
        self.gui = MemGui(camera_frame=self.vision.get_current_frame(format='pil'), cell_m_q=cell_m_q, cell_h_q=cell_h_q)
        self.robot = RobotModule(ip="192.168.1.100", home_position=[0, 0, 0, 0, 0, 0])
        self.pack_state = PackState()
        self.done = False

        # Leaf nodes
        self.begin_session = BeginSession(name="begin_session", blackboard=self.blackboard, rdf=self.rdf, gui=self.gui)        
        self.auto_class = AutoClass(name="auto_class", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui)
        self.helped_class = HelpedClass(name="helped_class", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, gui=self.gui)
        self.detect = Detect(name="detect", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui, robot=self.robot)
        self.assess = Assess(name="assess", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui)
        self.auto_sort = AutoSort(name="auto_sort", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, robot=self.robot, gui=self.gui, 
                                  cell_h_q=cell_h_q, cell_m_q=cell_m_q, discard_T=discard_T, keep_T=keep_T)
        self.helped_sort = HelpedSort(name="helped_sort", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, gui=self.gui, vision=self.vision)

        # Selectors
        self.class_selector = pt.composites.Selector(name="class_selector", memory=True, children=[self.auto_class, self.helped_class]) # memory=True to avoid GUI state switch
        self.sort_selector = pt.composites.Selector(name="sort_selector", memory=True, children=[self.auto_sort, self.helped_sort])

        # Main sequence 
        self.main_sequence = pt.composites.Sequence(name="main_sequence",memory=True)
        self.main_sequence.add_children([self.begin_session,
                                         self.class_selector,
                                         self.detect,
                                         self.assess,
                                         self.sort_selector])

        tree = self.main_sequence

        super(BehaviourTree, self).__init__(tree)
        # self.viewer = BtViewer(self)

        #self.gui.after(1000, self.tick_tree_in_gui)
        #self.gui.mainloop()

    def on_gui_closure(self):
        self.root.status = pt.common.Status.FAILURE
        print("GUI closed")
        self.gui.destroy()

    def tick_tree_in_gui(self):
        if self.root.status == pt.common.Status.SUCCESS:
            print("Behavior tree succeeded")
            self.gui.reset_gui()
            self.main_sequence.stop(pt.common.Status.INVALID) # reset the tree
            self.gui.after(1, self.tick_tree_in_gui)
        elif self.root.status == pt.common.Status.FAILURE:
            # self.done = True # are we using this?
            print("Behavior tree failed") 
            self.gui.quit()
        else:
            self.tick()
            self.gui.after(1, self.tick_tree_in_gui)
            #self.viewer.update()
            # print("\n"+pt.display.unicode_tree(root=self.root,show_status=True))
        
def main(args=None):
    tree = BehaviourTree()
    tree.gui.protocol("WM_DELETE_WINDOW", tree.on_gui_closure)

    tree.gui.after(1, tree.tick_tree_in_gui)
    tree.gui.mainloop()

if __name__ == "__main__":
    main()