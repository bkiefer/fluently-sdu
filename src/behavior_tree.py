import py_trees as pt
import time
#import rclpy
#import sys
#import os
from gui_module import MemGui
from robot_module import RobotModule
from battery_pack_module import PackState
#from rdf_store import RdfStore
from vision_module import VisionModule
from behaviors import AutoClass, HelpedClass, Detect, Assess, AutoSort, HelpedSort

class BehaviourTree(pt.trees.BehaviourTree):
    def __init__(self):        
        # Blackboard and registering keys 
        self.blackboard = pt.blackboard.Client(name="Blackboard_client")   
        #self.rdf = RdfStore()
        self.rdf = None
        self.vision = VisionModule()
        self.gui = MemGui(self.vision.get_current_frame(format='pil'))
        self.robot = RobotModule([0,0,0,0,0,0])
        self.pack_state = PackState()
        self.done = False

        # Leaf nodes
        self.auto_class = AutoClass(name="auto_class", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui)
        self.helped_class = HelpedClass(name="helped_class", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, gui=self.gui)
        self.detect = Detect(name="detect", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui, robot=self.robot)
        self.assess = Assess(name="assess", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui)
        self.auto_sort = AutoSort(name="auto_sort", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, robot=self.robot, gui=self.gui)
        self.helped_sort = HelpedSort(name="helped_sort", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, gui=self.gui)

        # Selectors
        self.class_selector = pt.composites.Selector(name="class_selector", memory=True, children=[self.auto_class, self.helped_class]) # memory=True to avoid GUI state switch
        self.sort_selector = pt.composites.Selector(name="sort_selector", memory=True, children=[self.auto_sort, self.helped_sort])

        # Main sequence 
        self.main_sequence = pt.composites.Sequence(name="main_sequence",memory=True)
        self.main_sequence.add_children([self.class_selector,
                                         self.detect,
                                         self.assess,
                                         self.sort_selector])

        tree = self.main_sequence

        super(BehaviourTree, self).__init__(tree)

        #self.gui.after(1000, self.tick_tree_in_gui)
        #self.gui.mainloop()

    def tick_tree_in_gui(self):
        if self.root.status != (pt.common.Status.SUCCESS or pt.common.Status.FAILURE):
            self.tick()
            self.gui.after(1000, self.tick_tree_in_gui)
            print("\n"+pt.display.unicode_tree(root=self.root,show_status=True))
        else: 
            self.done = True
            self.gui.quit()
        
def main(args=None):
    tree = BehaviourTree()

    while not tree.done:
        tree.gui.after(1000, tree.tick_tree_in_gui)
        tree.gui.mainloop()

    if tree.root.status == pt.common.Status.SUCCESS:
        print("Behavior tree succeeded")

    elif tree.root.status == pt.common.Status.FAILURE:
        print("Behavior tree failed") 

if __name__ == "__main__":
    main()