import py_trees as pt
import rclpy
import sys
import os
import time

# from .vision import
from gui_module import MemGui
from robot_module import RobotModule
from battery_pack_module import PackState
# from rdf_store import RdfStore
from vision_module import VisionModule
from behaviors import AutoClass, HelpedClass, AutoDetect, HelpedDetect, AutoAssess, HelpedAssess, AutoSort, HelpedSort

class BehaviourTree(pt.trees.BehaviourTree):
    def __init__(self):        
        # Blackboard and registering keys 
        self.blackboard = pt.blackboard.Client(name="Blackboard_client")   
        self.rdf = RdfStore()
        self.vision = VisionModule()
        self.gui = MemGui(self.vision.get_current_frame(format='pil'))
        self.robot = RobotModule([0,0,0,0,0,0])
        self.pack_state = PackState()

        # Leaf nodes
        self.auto_class = AutoClass(name="auto_class", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui)
        self.helped_class = HelpedClass(name="helped_class", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, gui=self.gui)
        self.auto_detect = AutoDetect(name="auto_detect", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui)
        self.helped_detect = HelpedDetect(name="helped_detect", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui)
        self.auto_assess = AutoAssess(name="auto_assess", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui)
        self.helped_assess = HelpedAssess(name="helped_assess", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui)
        self.auto_sort = AutoSort(name="auto_sort", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, robot=self.robot)
        self.helped_sort = HelpedSort(name="helped_sort", blackboard=self.blackboard, rdf=self.rdf, pack_state=self.pack_state, vision=self.vision, gui=self.gui)

        # Selectors
        self.class_selector = pt.composites.Selector(name="class_selector", memory=False, children=[self.auto_class, self.helped_class])
        self.detect_selector = pt.composites.Selector(name="detect_selector", memory=False, children=[self.auto_detect, self.helped_detect])
        self.assess_selector = pt.composites.Selector(name="assess_selector", memory=False, children=[self.auto_assess, self.helped_assess])
        self.sort_selector = pt.composites.Selector(name="sort_selector", memory=False, children=[self.auto_sort, self.helped_sort])

        # Main sequence 
        self.main_sequence = pt.composites.Sequence(name="main_sequence",memory=False)
        self.main_sequence.add_children([self.class_selector,
                                         self.detect_selector,
                                         self.assess_selector,
                                         self.sort_selector])

        tree = self.main_sequence

        super(BehaviourTree, self).__init__(tree)

def main(args=None):
    tree = BehaviourTree()

    # execute the BT
    print("\n"+pt.display.unicode_tree(root=tree.root,show_status=True))
    
    done = False    
    tree.setup(timeout=15.0)
    
    while not done:
        tree.tick()
        time.sleep(0.5)

        if tree.root.status == pt.common.Status.SUCCESS:
            print("Behavior tree succeeded")
            done = True 
            
        elif tree.root.status == pt.common.Status.FAILURE:
            print("Behavior tree failed") 
            done = True 
    
    rclpy.shutdown()

if __name__ == "__main__":
    main()