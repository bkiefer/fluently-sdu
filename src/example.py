import py_trees as pt
import sys
import os
import time

from gui_module import MemGui
from robot_module import RobotModule
from battery_pack_module import PackState
from vision_module import VisionModule

class Test01(pt.behaviour.Behaviour):
    """
    The vision module classifies the battery pack.
    SUCCESS if user accepts the classification. Pack state is updated.
    FAILURE if user rejects the classification. Pack state remains unchanged.
    """

    def __init__(self, name, pack_state, vision, gui):
        super().__init__(name)
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state

        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        if self.gui.active_frame != 1:
            print("First update for behavior", self.name)
            self.gui.show_frame(1) 
        if self.gui.chosen_model != "":
            new_status = pt.common.Status.SUCCESS
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
class Test02(pt.behaviour.Behaviour):
    """
    The vision module classifies the battery pack.
    SUCCESS if user accepts the classification. Pack state is updated.
    FAILURE if user rejects the classification. Pack state remains unchanged.
    """

    def __init__(self, name, pack_state, vision, gui):
        super().__init__(name)
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state

        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        if self.gui.active_frame != 2:
            print("First update for behavior", self.name)
            self.gui.show_frame(2) 
        if self.gui.active_frame > 43:
            new_status = pt.common.Status.SUCCESS
        else:
            new_status = pt.common.Status.RUNNING
        return new_status

class BehaviourTree(pt.trees.BehaviourTree):
    def __init__(self):        
        # Blackboard and registering keys 
        self.vision = VisionModule()
        self.gui = MemGui(self.vision.get_current_frame(format='pil'))
        self.robot = RobotModule([0,0,0,0,0,0])
        self.pack_state = PackState()

        # Leaf nodes
        self.auto_class = Test01(name="01", pack_state=self.pack_state, vision=self.vision, gui=self.gui)
        self.helped_class = Test02(name="02", pack_state=self.pack_state, vision=self.vision, gui=self.gui)

        # Main sequence 
        self.main_sequence = pt.composites.Sequence(name="main_sequence",memory=True)
        self.main_sequence.add_children([self.auto_class,
                                         self.helped_class])

        tree = self.main_sequence

        super(BehaviourTree, self).__init__(tree)
        
        self.gui.after(1, self.tick_tree_in_gui)
        self.gui.mainloop()

    def tick_tree_in_gui(self):
        self.tick()
        self.gui.after(1, self.tick_tree_in_gui)


if __name__ == "__main__":
    BehaviourTree()
