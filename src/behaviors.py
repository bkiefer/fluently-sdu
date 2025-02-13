import py_trees as pt
from gui_module import MemGui
from robot_module import RobotModule
from battery_pack_module import PackState
from vision_module import VisionModule
#from rdf_store import RdfStore

class AutoClass(pt.behaviour.Behaviour):
    """
    The vision module classifies the battery pack.
    SUCCESS if user accepts the classification. Pack state is updated.
    FAILURE if user rejects the classification. Pack state remains unchanged.
    """
    def __init__(self, name, blackboard, rdf, pack_state, vision, gui):
        super(AutoClass, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state
        self.blackboard = blackboard
        self.rdf = rdf
        self.status = pt.common.Status.INVALID

    def update(self):
        if self.gui.active_frame != 1:
            self.gui.show_frame(1)
            print("First update for behavior", self.name)
            current_frame_list = [self.vision.get_current_frame()]
            # value will be updated in the GUI shortly
            self.gui.proposed_models = self.vision.classify_cell(frames=current_frame_list) 

        if self.gui.class_reject:
            new_status = pt.common.Status.FAILURE

        elif self.gui.chosen_model != "":
            model = self.gui.chosen_model
            # update cell models
            # TODO: get the rest of cell information from ontology?
            for row in range(self.pack_state.rows):
                for col in range(self.pack_state.cols):
                    self.pack_state.update_cell(row, col, model=model)
            #for cell in self.pack_state.cells[0]:
            #    cell.model = self.gui.chosen_model
            new_status = pt.common.Status.SUCCESS
        else:
            new_status = pt.common.Status.RUNNING
        return new_status

class HelpedClass(pt.behaviour.Behaviour):
    """
    The user classifies the battery pack.
    SUCCESS when the user input is received. Pack state is updated.
    """
    # NOTE: The system may be able to classify the pack, or may determine that the pack is unseen (!). The user can override the decision either way.

    def __init__(self, name, blackboard, rdf, pack_state, gui):
        super(HelpedClass, self).__init__(name)
        self.gui = gui
        self.pack_state = pack_state
        self.blackboard = blackboard
        self.rdf = rdf
        self.status = pt.common.Status.INVALID

    def update(self):
        if self.gui.active_frame != 2:
            print("First update for behavior", self.name)
            self.gui.show_frame(2)

        if self.gui.chosen_model != "":
            model = self.gui.chosen_model
            # update cell models
            # TODO: get the rest of cell information from ontology?
            for row in range(self.pack_state.rows):
                for col in range(self.pack_state.cols):
                    self.pack_state.update_cell(row, col, model=model)
            #for cell in self.pack_state.cells[0]:
            #    cell.model = self.gui.chosen_model
            new_status = pt.common.Status.SUCCESS
        else:
            new_status = pt.common.Status.RUNNING

        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            pass
            #self.blackboard.set(self.name, new_status)        
            #self.rdf.update_rdf(node = self.name)

class Detect(pt.behaviour.Behaviour):
    """
    The vision module detects the individual battery cells.
    SUCCESS when the detection is accepted. Pack state is updated.
    """
    def __init__(self, name, blackboard, rdf, pack_state, vision, gui, robot):
        super(Detect, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state
        self.robot = robot
        self.blackboard = blackboard
        self.rdf = rdf
        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        if self.gui.active_frame != 3:
            print("First update for behavior", self.name)
            #current_frame = self.vision.get_current_frame()
            #self.gui.proposed_locations = self.vision.cell_detection(current_frame)
            self.gui.show_frame(3)

        if self.gui.chosen_locations: # if not chosen_locations not empty
            self.pack_state.update_dim(rows=len(self.gui.chosen_locations),cols=1) # change to known dimensions
            i = 0
            for row in range(self.pack_state.rows):
                for col in range(self.pack_state.cols):
                    frame_position = self.gui.chosen_locations[i]
                    pose = self.robot.frame_to_world(frame_position)
                    self.pack_state.update_cell(row, col, frame_position=frame_position, pose=pose)
                    i += 1
            new_status = pt.common.Status.SUCCESS
        else:
            new_status = pt.common.Status.RUNNING
        
        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            pass
            #self.blackboard.set(self.name, new_status)        
            #self.rdf.update_rdf(node = self.name)

class Assess(pt.behaviour.Behaviour):
    """
    The vision module assesses the quality of each individual battery cell.
    SUCCESS if the user has no interventions. Pack state is updated.
    FAILURE if the user wishes to edit the assessment. Pack state remains unchanged.
    """
    def __init__(self, name, blackboard, rdf, pack_state, vision, gui):
        super(Assess, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state
        self.blackboard = blackboard
        self.rdf = rdf
        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        if self.gui.active_frame != 4:
            print("First update for behavior", self.name)
            #current_frame = self.vision.get_current_frame()
            #self.gui.proposed_locations = self.vision.cell_detection(current_frame)
            self.gui.show_frame(4)
        
        if len(self.gui.chosen_qualities) != 0:
            new_status = pt.common.Status.SUCCESS
        else:
            new_status = pt.common.Status.RUNNING

        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            pass
            #self.blackboard.set(self.name, new_status)        
            #self.rdf.update_rdf(node = self.name)

class AutoSort(pt.behaviour.Behaviour):
    """
    The pick up area is determined by the vision module.
    The place area is determined by the pack state.
    The robot performs pick and place for each battery cell.
    The vision module determines if grasping and pick up is successful for each cell.
    The pack state is updated.
    If necessary there is a nozzle swap / ask for human help.

    NOTE: SUCCESS if all pick and place actions succeed or some other criterion? 
    """
    def __init__(self, name, blackboard, rdf, pack_state, vision, robot, gui):
        super(AutoSort, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.robot = robot
        self.pack_state = pack_state
        self.blackboard = blackboard
        self.rdf = rdf
        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        if self.gui.active_frame != 5:
            print("First update for behavior", self.name)
            #current_frame = self.vision.get_current_frame()
            #self.gui.proposed_locations = self.vision.cell_detection(current_frame)
            self.gui.show_frame(5)
            new_status = pt.common.Status.RUNNING

        #if all(cell.sorted for cell in self.pack_state.cells):      
            #new_status = pt.common.Status.SUCCESS  
        else:
            new_status = pt.common.Status.FAILURE

        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            pass
            #self.blackboard.set(self.name, new_status)        
            #self.rdf.update_rdf(node = self.name)

class HelpedSort(pt.behaviour.Behaviour):
    """
    GUI asks human for help.
    Human extracts the battery cells.
    SUCCESS when human input is received (task done).
    """

    def __init__(self, name, blackboard, rdf, pack_state, gui):
        super(HelpedSort, self).__init__(name)
        self.gui = gui
        self.pack_state = pack_state
        self.blackboard = blackboard
        self.rdf = rdf
        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        if self.gui.active_frame != 6:
            print("First update for behavior", self.name)
            #current_frame = self.vision.get_current_frame()
            #self.gui.proposed_locations = self.vision.cell_detection(current_frame)
            self.gui.show_frame(6)

        #if all(cell.sorted for cell in self.pack_state.cells):      
            #new_status = pt.common.Status.SUCCESS  
        if self.gui.done:
            new_status = pt.common.Status.SUCCESS

        else: 
            new_status = pt.common.Status.RUNNING
            
        return new_status
        
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            pass
            #self.blackboard.set(self.name, new_status)        
            #self.rdf.update_rdf(node = self.name)