import py_trees as pt

class BeginSession(pt.behaviour.Behaviour):
    """
    Sets up the user and session in the RDF store
    """
    def __init__(self, name, blackboard, rdf, gui):
        super(BeginSession, self).__init__(name)
        self.gui = gui
        self.blackboard = blackboard
        self.rdf = rdf
        self.status = pt.common.Status.INVALID
        self.tried = False

    def update(self):
        if not self.tried:  
            self.rdf.get_user(first_name = "", last_name = "")
            self.rdf.start_session()
            self.tried = True
        new_status = pt.common.Status.SUCCESS
        
        return new_status

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
        self.tried = False

    def update(self):
        if not self.tried:
            self.rdf.start_sorting_process()
            self.tried = True

        if self.gui.active_frame != 1:
            self.gui.show_frame(1)
            print("First update for behavior", self.name)
            current_frame_list = [self.vision.get_current_frame()]
            # value will be updated in the GUI shortly
            self.gui.proposed_models = self.vision.classify_cell(frames=current_frame_list) 

        if self.gui.class_reject:
            new_status = pt.common.Status.FAILURE

        elif self.gui.chosen_model != "":
            # TODO: add to RDF store and extract dimensions of cell 
            model = self.gui.chosen_model
            print(model)
            size = self.rdf.get_dimensions_from_cell_type(model)
            print(size)
            # update cells information
            for row in range(self.pack_state.rows):
                for col in range(self.pack_state.cols):
                    self.pack_state.update_cell(row, col, model=model)
            new_status = pt.common.Status.SUCCESS
            self.rdf.object_classification()
            # TODO: add cell information to RDF store
        else:
            new_status = pt.common.Status.RUNNING

        return new_status

class HelpedClass(pt.behaviour.Behaviour):
    """
    The user classifies the battery pack.
    SUCCESS when the user input is received. Pack state is updated.
    """
    # NOTE: The system may be able to classify the pack, or may determine that the pack is unseen (!). 
    # The user can override the decision either way.

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
            # update cells information
            for row in range(self.pack_state.rows):
                for col in range(self.pack_state.cols):
                    self.pack_state.update_cell(row, col, model=model)
            new_status = pt.common.Status.SUCCESS
            # TODO: add cell information to RDF store
        else:
            new_status = pt.common.Status.RUNNING

        return new_status

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
            current_frame = self.vision.get_current_frame()
            # get detected cells from vision module
            proposed = self.vision.cell_detection(current_frame) # center, radius
            proposed_locations = []
            # update cell locations in GUI
            for circle in proposed:
                proposed_locations.append((circle[0]-circle[2], circle[1]-circle[2],circle[0]+circle[2], circle[1]+circle[2]))
            self.gui.proposed_locations = proposed_locations
            self.gui.show_frame(3)

        if self.gui.chosen_locations: # if not chosen_locations not empty
            # for now it is just one long row, but this info could come from the pack information / visual / user input
            self.pack_state.update_dim(rows=len(self.gui.chosen_locations),cols=1) # change to known dimensions
            i = 0
            # change to known dimensions
            for row in range(self.pack_state.rows):
                for col in range(self.pack_state.cols):
                    frame_position = self.gui.chosen_locations[i]
                     # get the center position
                    frame_position = [(frame_position[0]+frame_position[2])//2, (frame_position[1]+frame_position[3])//2]
                    pose = self.robot.frame_to_world(frame_position)
                    self.pack_state.update_cell(row, col, frame_position=frame_position, pose=pose)
                    i += 1
            new_status = pt.common.Status.SUCCESS
            self.rdf.object_detection()
        else:
            new_status = pt.common.Status.RUNNING
        
        return new_status

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
            current_frame = self.vision.get_current_frame() # keep old frame ???
            bbs_positions = self.gui.chosen_locations
            # get proposed qualities from vision module and update GUI
            qualities = self.vision.assess_cells_qualities(frame=current_frame,bbs_positions=bbs_positions)
            self.gui.proposed_qualities = qualities
            self.gui.show_frame(4)
        
        if len(self.gui.chosen_qualities) != 0:
            # change to known dimensions
            i = 0
            # update cell information with the qualities
            for row in range(self.pack_state.rows):
                for col in range(self.pack_state.cols):
                    quality = self.gui.chosen_qualities[i]
                    self.pack_state.update_cell(row, col, quality=quality)
                    i += 1
            new_status = pt.common.Status.SUCCESS
            self.rdf.quality_assessment()

        else:
            new_status = pt.common.Status.RUNNING

        return new_status

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
        
        else:
            current_frame = self.vision.get_current_frame() # keep old frame ???
            i = 0
            # get the pose of each cell + quality and perform pick and place
            for row in range(self.pack_state.rows):
                for col in range(self.pack_state.cols):
                    frame_position = self.pack_state.cells[i][0].frame_position
                    pose = self.pack_state.cells[i][0].pose
                    discard = (self.pack_state.cells[i][0].quality >= 0.5)
                    # TODO: perform pick and place based on pose and discard True/False
                    self.robot.pick_and_place(pose, pose)
                    sorted = self.vision.verify_pickup(current_frame, frame_position)
                    if sorted:
                        self.pack_state.update_cell(row, col, sorted=sorted)
                    else:
                        # Fails if a single pick and place fails, maybe change this
                        new_status = pt.common.Status.FAILURE 
                        return new_status
                    # TODO: update self.gui.outcomes
                    i += 1

            new_status = pt.common.Status.SUCCESS
            self.rdf.end_sorting_process()
            self.rdf.end_session()

        return new_status

class HelpedSort(pt.behaviour.Behaviour):
    """
    GUI asks human for help.
    Human extracts the battery cells.
    SUCCESS when human input is received (task done).
    """
    def __init__(self, name, blackboard, rdf, pack_state, gui, vision):
        super(HelpedSort, self).__init__(name)
        self.gui = gui
        self.vision = vision
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
            # record system asks for help, TODO: put the class under RobotAction
            self.rdf.request_help()

        if self.gui.done:
            # visual check that all cells are sorted
            current_frame = self.vision.get_current_frame() # keep old frame ???
            i = 0
            print("Final check...")
            # Verify that all cells have been picked up
            for row in range(self.pack_state.rows):
                for col in range(self.pack_state.cols):
                    frame_position = self.pack_state.cells[i][0].frame_position
                    sorted = self.vision.verify_pickup(current_frame, frame_position)
                    if sorted:
                        self.pack_state.update_cell(row, col, sorted=sorted)
                    else:
                        # TODO: warn user that not all batteries are sorted through GUI (?)
                        print("UserWarning: Battery cell not sorted")
                    i += 1
            new_status = pt.common.Status.SUCCESS
            self.rdf.end_sorting_process()
            self.rdf.end_session()
        else:
            new_status = pt.common.Status.RUNNING
            
        return new_status