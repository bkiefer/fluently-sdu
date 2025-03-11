import py_trees as pt
import time
import spatialmath as sm

class BeginSession(pt.behaviour.Behaviour):
    """
    Sets up the user and session in the RDF store
    """
    def __init__(self, name, blackboard, rdf, pack_state, vision, gui, robot):
        super(BeginSession, self).__init__(name)
        self.gui = gui
        self.blackboard = blackboard
        self.rdf = rdf
        self.vision = vision
        self.pack_state = pack_state
        self.robot = robot
        # self.status = pt.common.Status.INVALID
        # self.tried = False

    def update(self):
        if self.status == pt.common.Status.INVALID:
            print("First update for behavior", self.name)
            self.rdf.get_user(first_name = "", last_name = "")
            self.rdf.start_session()
            results = self.vision.cell_detection(self.gui.camera_frame) # center, radius
            results = sorted(results, key=lambda el: (el[1], el[0]))
            k = 0
            for i in range((self.pack_state.rows)):
                for j in range(self.pack_state.cols):
                    frame_position = (results[k][0], results[k][1])
                    # pose = self.vision.frame_to_3d(frame_position, self.vision.camera, flag=j)
                    # self.pack_state.update_cell(i, j, frame_position=frame_position, pose=pose, radius=results[k][2])
                    self.pack_state.update_cell(i, j, frame_position=frame_position, radius=results[k][2])
                    k += 1
            new_status = pt.common.Status.SUCCESS   
            print(self.name, self.status)
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
        # self.tried = False

    def update(self):
        if self.status == pt.common.Status.INVALID:
            self.rdf.start_sorting_process()
            # self.tried = True

        if self.gui.active_frame != 1:
            print("First update for behavior", self.name)
            # TODO: get the probability from the rdf and the height registered in the battery pack state
            cells_probs = [{'model': "AA", 'prob': 0.51}, {'model': "C", 'prob': 0.49},  {'model': "XXX", 'prob': 0.23}, {'model': "XYZ", 'prob': 0.12}] 
            self.gui.update_proposed_models(cells_probs)
            self.gui.show_frame(1)

        if self.gui.class_reject:
            new_status = pt.common.Status.FAILURE
            print(self.name, new_status)

        elif self.gui.chosen_model != "":
            model = self.gui.chosen_model
            k = 0
            for i in range((self.pack_state.rows)):
                for j in range(self.pack_state.cols):
                    self.pack_state.update_cell(i, j, model=model)
                    k += 1
            new_status = pt.common.Status.SUCCESS
            # record classification is done
            self.rdf.object_classification()
            print(self.name, new_status)
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
            # radius, height = self.rdf.get_dimensions_from_cell_type(model)
            radius, height = 85, 26
            # update cells information with model and size
            k = 0
            for i in range((self.pack_state.rows)):
                for j in range(self.pack_state.cols):
                    self.pack_state.update_cell(i, j, model=model, radius=radius, height=height)
                    k += 1
            # record classification is done
            self.rdf.object_classification()
            new_status = pt.common.Status.SUCCESS
            print(self.name, new_status)
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
        # self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        if self.gui.active_frame != 3:
            print("First update for behavior", self.name)
            # current_frame = self.vision.get_current_frame()
            # proposed = self.vision.cell_detection(self.gui.camera_frame) # center, radius
            proposed_locations = []
            # # update cell locations in GUI
            for row in self.pack_state.cells:
                for cell in row:
                    cx, cy = cell.frame_position
                    r = cell.radius
                    proposed_locations.append((cx-r, cy-r, cx+r, cy+r))
                    # TODO: it is not drawing check if they are correctly initialized
            self.gui.update_bbs(proposed_locations, self.gui.frames[3])
            self.gui.show_frame(3)

        if self.gui.chosen_locations: # if not chosen_locations not empty
            # for now it is just one long row, but this info could come from the pack information / visual / user input
            k = 0
            for i in range(self.pack_state.rows):
                for j in range(self.pack_state.cols):
                    frame_position = self.gui.chosen_locations[k]
                     # get the center position
                    frame_position = [(frame_position[0]+frame_position[2])//2, (frame_position[1]+frame_position[3])//2]
                    # pose = self.vision.frame_to_3d(frame_position, self.vision.camera, flag=j)
                    # self.pack_state.update_cell(i, j, frame_position=frame_position, pose=pose, radius=results[k][2])
                    self.pack_state.update_cell(i, j, frame_position=frame_position)
                    k += 1
            # we add all of the cells and their properties to the RDF store as part of the battery pack object
            # self.rdf.update_number_of_cells(rows=self.pack_state.rows, cols=self.pack_state.cols, model=self.gui.chosen_model)
            new_status = pt.common.Status.SUCCESS
            # self.rdf.object_detection()
            print(self.name, new_status)
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
        # self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        if self.gui.active_frame != 4:
            print("First update for behavior", self.name)
            # current_frame = self.vision.get_current_frame() # keep old frame ???
            bbs_positions = self.gui.chosen_locations
            # get proposed qualities from vision module and update GUI
            qualities = self.vision.assess_cells_qualities(frame=self.gui.camera_frame, bbs_positions=bbs_positions)
            self.gui.write_qualities(qualities, self.gui.frames[4], editable=True)
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
            print(self.name, new_status)

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
    def __init__(self, name, blackboard, rdf, pack_state, vision, robot, gui, cell_m_q, cell_h_q, discard_T, keep_T, over_pack_T):
        super(AutoSort, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.robot = robot
        self.pack_state = pack_state
        self.blackboard = blackboard
        self.rdf = rdf
        # self.tried = False
        self.cell_m_q, self.cell_h_q = cell_m_q, cell_h_q
        self.status = pt.common.Status.INVALID
        self.discard_T, self.keep_T, self.over_pack_T = discard_T, keep_T, over_pack_T

    def update(self):
        if self.gui.active_frame != 5:
            print("First update for behavior", self.name)
            # self.gui.proposed_locations = self.vision.cell_detection(current_frame)
            self.gui.write_qualities(self.gui.chosen_qualities, self.gui.frames[5])
            self.gui.write_qualities(self.gui.chosen_qualities, self.gui.frames[6])
            self.gui.show_frame(5)
            new_status = pt.common.Status.RUNNING
        else:
            # current_frame = self.vision.get_current_frame() # keep old frame ???
            # get the pose of each cell + quality and perform pick and place
            new_status = pt.common.Status.SUCCESS
            for i, row in enumerate(self.pack_state.cells):
                for j, cell in enumerate(row):
                    frame_position = cell.frame_position
                    radius = cell.radius
                    pick_pose = cell.pose
                    if cell.quality < self.cell_m_q:
                        place_pose = self.discard_T
                    else:
                        place_pose = self.keep_T    
                    self.robot.pick_and_place(pick_pose, place_pose)
                    self.robot.move_to_cart_pos(self.over_pack_T)
                    sorted = self.vision.verify_pickup(frame_position, radius)
                    self.gui.write_outcome_picked_cell([frame_position[0], frame_position[1]], sorted, self.gui.frames[5])
                    self.gui.write_outcome_picked_cell([frame_position[0], frame_position[1]], sorted, self.gui.frames[6])
                    # update RDF
                    self.rdf.update_cell_sorted(i, j, sorted=sorted)
                    if sorted:
                        self.pack_state.update_cell(i, j, sorted=sorted)
                    else:
                        # Fails if a single pick and place fails, maybe change this
                        new_status = pt.common.Status.FAILURE 
                        # return new_status # removed otherwise does not tries them all
                    # TODO: update self.gui.outcomes
            self.rdf.end_sorting_process()
            self.rdf.end_session()
            print(self.name, new_status)
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
        # self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        if self.gui.active_frame != 6:
            print("First update for behavior", self.name)
            #current_frame = self.vision.get_current_frame()
            #self.gui.proposed_locations = self.vision.cell_detection(current_frame)
            self.gui.show_frame(6)
            # record system asks for help, TODO: put the class under RobotAction
            # self.rdf.request_help()

        if self.gui.done:
            # visual check that all cells are sorted
            current_frame = self.vision.get_current_frame() # keep old frame ???
            print("Final check...")
            # Verify that all cells have been picked up
            for row in range(self.pack_state.rows):
                for col in range(self.pack_state.cols):
                    frame_position = self.pack_state.cells[row][col].frame_position
                    sorted = self.vision.verify_pickup(frame_position,  self.pack_state.cells[row][col].radius)
                    if sorted:
                        self.pack_state.update_cell(row, col, sorted=sorted)
                    else:
                        # TODO: warn user that not all batteries are sorted through GUI (?)
                        print("UserWarning: Battery cell not sorted")
            new_status = pt.common.Status.SUCCESS
            self.rdf.end_sorting_process()
            self.rdf.end_session()
            print(self.name, new_status)   
        else:
            new_status = pt.common.Status.RUNNING
        return new_status