import py_trees as pt
import time
import random
import spatialmath as sm
from gubokit import utilities

class BeginSession(pt.behaviour.Behaviour):
    """
    Sets up the user and session in the RDF store
    """
    def __init__(self, name, rdf, gui, vision):
        super(BeginSession, self).__init__(name)
        self.gui = gui
        self.rdf = rdf
        self.vision = vision

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(8)
        if self.gui.first_name != None:
            # register name and start session
            self.rdf.get_user(first_name = self.gui.first_name, last_name = self.gui.last_name)
            self.rdf.start_session()
            new_status = pt.common.Status.SUCCESS
            print(self.name, new_status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
class PackPlaced(pt.behaviour.Behaviour):
    """
    Await pack placed and fastened
    """
    def __init__(self, name, rdf, vision, gui):
        super(PackPlaced, self).__init__(name)
        self.gui = gui
        self.rdf = rdf
        self.vision = vision

    def update(self):
        # register battery placed from human confirmation
        if self.gui.confirm:
            self.gui.confirm = False
            self.rdf.human_place_battery()
            new_status = pt.common.Status.SUCCESS
            self.rdf.get_pack_models_in_ontology()
            print(self.name, new_status)
        else:
            frame = self.vision.get_current_frame()
            self.gui.update_image(frame)
            self.gui.show_frame(9)
            new_status = pt.common.Status.RUNNING
        return new_status
    
class AutoPackClass(pt.behaviour.Behaviour):
    """
    The vision module classifies the pack.
    SUCCESS if user accepts the classification. Pack state is updated.
    FAILURE if user rejects the classification or the robot does not recognize the pack. 
    """
    def __init__(self, name, rdf, pack_state, vision, gui):
        super(AutoPackClass, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state
        self.rdf = rdf
        self.tried = False
        self.result = None

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(16) 

        if not self.tried:
            self.tried = True
            # locate pack with vision module
            self.result = self.vision.locate_pack(frame)
            known_models = self.rdf.get_pack_models_in_ontology()
            if not self.result:
                self.gui.update_proposed_packs(["unknown"]+known_models)
            else:
                proposed_pack = self.result["shape"]
                if proposed_pack in known_models:
                    # put proposed pack in front of list
                    known_models.remove(proposed_pack)
                    self.gui.update_proposed_packs([proposed_pack]+known_models)
                else: 
                    self.gui.update_proposed_packs(["unknown"]+known_models)
            new_status = pt.common.Status.RUNNING

        elif self.gui.class_reject:
            self.gui.class_reject = False
            new_status = pt.common.Status.FAILURE
            print(self.name, new_status)

        elif self.gui.chosen_pack != "":
            # record classification is done, update pack state
            self.rdf.battery_classification()
            self.rdf.record_pack_type(self.result["shape"]) # TODO: change to actual label
            self.pack_state.model = self.result["shape"]
            self.pack_state.size = self.result["size"]
            self.pack_state.cover_on = self.result["cover_on"] # use vision function cell_detection()?
            self.pack_state.location = self.result["location"]
            print("location: ",self.pack_state.location)
            new_status = pt.common.Status.SUCCESS
            # TODO: RDF: record if classification was successful
            # TODO: RDF: update and upload disassembly plan
            print(self.name, new_status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            self.logger.info("Terminating: " + self.name + " with status: " + str(new_status))
            self.tried = False

class HelpedPackClass(pt.behaviour.Behaviour):
    """
    The user classifies the pack.
    SUCCESS when the user input is received. Pack state is updated.    
    """
    def __init__(self, name, rdf, pack_state, gui, vision):
        super(HelpedPackClass, self).__init__(name)
        self.gui = gui
        self.pack_state = pack_state
        self.rdf = rdf
        self.vision = vision

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(17) 

        if self.gui.chosen_pack != "":
            model = self.gui.chosen_pack
            self.rdf.record_pack_type(pack_name=model)
            self.pack_state.model = model
            cells = self.vision.cell_detection(frame)
            self.pack_state.cover_on = True if not cells else False
            self.rdf.check_cover(cells_visible=False if not cells else True)
            new_status = pt.common.Status.SUCCESS
            self.rdf.cell_classification()
            print(self.name, new_status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
class HelpedLocatePack(pt.behaviour.Behaviour):
    """
    The user locates the pack using the GUI.
    SUCCESS when the user input is received. Pack state is updated.    
    """
    def __init__(self, name, rdf, pack_state, gui, vision):
        super(HelpedLocatePack, self).__init__(name)
        self.gui = gui
        self.pack_state = pack_state
        self.rdf = rdf
        self.vision = vision
        self.tried = False

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(18) 
        if not self.tried:
            self.tried = True
            self.gui.update_bbs([], self.gui.frames[18])
            self.gui.bbs_editor.spawn_box()
        if self.gui.chosen_pack_location:
            location = self.gui.chosen_pack_location[0]
            frame_position = ((location[0]+location[2])//2, (location[1]+location[3])//2)
            self.pack_state.location = frame_position
            #self.pack_state.size = 
            new_status = pt.common.Status.SUCCESS
            # TODO: RDF update
            print(self.name, new_status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
    def terminate(self, new_status):
        self.logger.info("Terminating: " + self.name + " with status: " + str(new_status))
        self.tried = False

class CheckCoverOff(pt.behaviour.Behaviour):
    """
    The vision module determines if the pack is covered.
    SUCCESS if cover is off.
    FAILURE if cover is on.
    """
    def __init__(self, name, rdf, pack_state, vision, gui):
        super(CheckCoverOff, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state
        self.rdf = rdf
        self.tried = False

    def update(self):
        if not self.tried: # behavior is constantly ticked, only record once if cover is on ONCE
            self.tried = True
            if not self.pack_state.cover_on:
                #self.rdf.check_cover(cells_visible=True)
                new_status = pt.common.Status.SUCCESS
            else:
                new_status = pt.common.Status.FAILURE
        else:
            frame = self.vision.get_current_frame()
            cells = self.vision.cell_detection(frame)
            if len(cells) != 0:
                self.pack_state.cover_on = False
                self.rdf.check_cover(cells_visible=True)
                new_status = pt.common.Status.SUCCESS
            else:
                new_status = pt.common.Status.FAILURE
            # TODO: RDF: check if removal strategy was "human", if cover is off, record RemoveCover isA HumanAction!
        return new_status
    
    #def terminate(self, new_status):
    #    self.logger.info("Terminating: " + self.name + " with status: " + str(new_status))
    #    self.tried = False

class CheckHumanRemovesCover(pt.behaviour.Behaviour):
    """
    Checks the RDF store OR user input if the human should remove the cover
    SUCCESS if human should remove cover
    FAILURE otherwise
    """
    def __init__(self, name, rdf, pack_state, gui, vision):
        super(CheckHumanRemovesCover, self).__init__(name)
        self.gui = gui
        self.pack_state = pack_state
        self.rdf = rdf
        self.vision = vision

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(13) 
        # TODO: RDF: check if pack is known
        #       if yes, check disassembly plan
        # if no, await user input:
        
        if self.gui.removal_strategy != "":
            if self.gui.removal_strategy == "human":
                new_status = pt.common.Status.SUCCESS
                print(self.name, self.status)
            else:
                new_status = pt.common.Status.FAILURE 
                print(self.name, self.status)
            # TODO: RDF update
        else:
            new_status = pt.common.Status.RUNNING
        
        return new_status

class CheckColabRemoveCover(pt.behaviour.Behaviour):
    """
    Checks the RDF store OR user input if cover removal is collaborative
    SUCCESS if collaborative
    FAILURE otherwise
    """
    def __init__(self, name, rdf, pack_state, gui, vision):
        super(CheckColabRemoveCover, self).__init__(name)
        self.gui = gui
        self.pack_state = pack_state
        self.rdf = rdf
        self.vision = vision

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(13) 
        # TODO: RDF: check if pack is known
        #       if yes, check disassembly plan
        # if no, await user input:

        if self.gui.removal_strategy != "":
            # This should be extracted from RDF
            if self.gui.removal_strategy == "colab": 
                new_status = pt.common.Status.SUCCESS
                print(self.name, self.status)
            else:
                new_status = pt.common.Status.FAILURE 
                print(self.name, self.status)
            # TODO: RDF update
        else:
            new_status = pt.common.Status.RUNNING
        #print(self.gui.removal_strategy)

        return new_status

class ColabAwaitHuman(pt.behaviour.Behaviour):
    """
    Wait for human acknowledgement that they are ready for robot to remove cover
    SUCCESS when acknowledged
    """
    def __init__(self, name, rdf, pack_state, gui, vision):
        super(ColabAwaitHuman, self).__init__(name)
        self.gui = gui
        self.pack_state = pack_state
        self.rdf = rdf
        self.vision = vision

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(14)
        if self.gui.confirm:
            self.gui.confirm = False
            # TODO: RDF: update
            new_status = pt.common.Status.SUCCESS
            print(self.name, self.status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
class RemoveCover(pt.behaviour.Behaviour):
    """
    Robot removes cover
    SUCCESS when done
    """
    def __init__(self, name, rdf, pack_state, vision, gui, robot, bin_rotvec, pack_height):
        super(RemoveCover, self).__init__(name)
        self.robot = robot
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state
        self.rdf = rdf
        self.bin_rotvec = bin_rotvec
        self.pack_height = pack_height

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(14)
        #new_status = pt.common.Status.RUNNING
        
        # TODO: robot module: remove cover
        pack_location = self.pack_state.location
        try: 
            b_T_TCP = utilities.rotvec_to_T(self.robot.robot.getActualTCPPose())
            screw_T_b = self.vision.frame_pos_to_pose(pack_location, self.vision.camera, self.pack_height, b_T_TCP)
            self.robot.pick_and_place(screw_T_b,utilities.rotvec_to_T(self.bin_rotvec))
        except:
            pass

        # TODO: RDF: update
        self.rdf.robot_remove_cover()
        new_status = pt.common.Status.SUCCESS # TODO: change to running
        print(self.name, new_status)
        return new_status
    
class AwaitToolChange(pt.behaviour.Behaviour):
    """
    Checks user input if tool change is complete
    This step is used for any tool change
    SUCCESS tool change is complete 
    """
    def __init__(self, name, rdf, gui, vision, robot):
        super(AwaitToolChange, self).__init__(name)
        self.gui = gui
        self.rdf = rdf
        self.vision = vision
        self.robot = robot

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(11)

        if self.gui.confirm:
            self.gui.confirm = False
            self.rdf.switch_tool()
            new_status = pt.common.Status.SUCCESS
            tool = self.rdf.get_robot_tool()
            if tool == "large":
                self.robot.active_gripper = "big"
            elif tool == "small": 
                self.robot.active_gripper = "small"
            print(self.name, self.status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status

class BigGripper(pt.behaviour.Behaviour):
    """
    Checks if big gripper is equipped.
    SUCCESS if true.
    """
    def __init__(self, name, rdf, gui, vision, robot):
        super(BigGripper, self).__init__(name)
        self.gui = gui
        self.rdf = rdf
        self.vision = vision
        self.robot = robot
        self.tried = False

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(10)

        new_status = pt.common.Status.RUNNING

        if not self.tried:
            self.tried = True
            last_tool = self.rdf.get_robot_tool()
            if last_tool:
                self.tried = False
                if last_tool == "small":
                    self.robot.active_gripper = "small"
                    new_status = pt.common.Status.FAILURE
                elif last_tool == "large":
                    self.robot.active_gripper = "big"
                    new_status = pt.common.Status.SUCCESS
                print("last tool", self.rdf.get_robot_tool())

        elif self.gui.gripper != "":
            if self.gui.gripper == "large":
                new_status = pt.common.Status.SUCCESS
                self.rdf.record_robot_tool("large")
                self.robot.active_gripper = "big"
                print("last tool", self.rdf.get_robot_tool())
            else: 
                new_status = pt.common.Status.FAILURE
                self.rdf.record_robot_tool("small")
                self.robot.active_gripper = "small"
                print("last tool", self.rdf.get_robot_tool())
            self.gui.gripper = ""
             
        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            self.logger.info("Terminating: " + self.name + " with status: " + str(new_status))
            self.tried = False
    
class SmallGripper(pt.behaviour.Behaviour):
    """
    Checks if small gripper is equipped.
    SUCCESS if true.
    """
    def __init__(self, name, rdf, gui, vision, robot):
        super(SmallGripper, self).__init__(name)
        self.gui = gui
        self.rdf = rdf
        self.vision = vision
        self.robot = robot
        self.tried = False

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(10)

        new_status = pt.common.Status.RUNNING
        
        if not self.tried:
            self.tried = True
            last_tool = self.rdf.get_robot_tool()
            if last_tool:
                self.tried = False
                if last_tool == "small":
                    self.robot.active_gripper = "small"
                    new_status = pt.common.Status.SUCCESS
                elif last_tool == "large":
                    self.robot.active_gripper = "big"
                    new_status = pt.common.Status.FAILURE     
                print("last tool", self.rdf.get_robot_tool())
        
        elif self.gui.gripper != "":
            if self.gui.gripper == "small":
                new_status = pt.common.Status.SUCCESS
                self.rdf.record_robot_tool("small")
                self.robot.active_gripper = "small"
                print("last tool", self.rdf.get_robot_tool())
            else: 
                new_status = pt.common.Status.FAILURE
                self.rdf.record_robot_tool("large")
                self.robot.active_gripper = "big"
                print("last tool", self.rdf.get_robot_tool())
            self.gui.gripper = ""
        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            self.logger.info("Terminating: " + self.name + " with status: " + str(new_status))
            self.tried = False
        
class CheckPackKnown(pt.behaviour.Behaviour):
    """
    Checks the RDF store if pack is known
    SUCCESS if pack is known
    FAILURE otherwise
    """
    def __init__(self, name, rdf, pack_state, gui):#, vision):
        super(CheckPackKnown, self).__init__(name)
        self.gui = gui
        self.pack_state = pack_state
        self.rdf = rdf

    def update(self):
        if self.status == pt.common.Status.INVALID:
            print("First update for behavior", self.name)
            self.rdf.start_sorting_process()
        """
        #results = self.vision.cell_detection(self.gui.camera_frame) # center, radius
        print("Results: ",results)
        if len(results)!=0:
            results = sorted(results, key=lambda el: (el[1], el[0]))
            k = 0
            for i in range((self.pack_state.rows)):
                for j in range(self.pack_state.cols):
                    frame_position = (results[k][0], results[k][1])
                    # pose = self.vision.frame_to_3d(frame_position, self.vision.camera, flag=j)
                    # self.pack_state.update_cell(i, j, frame_position=frame_position, pose=pose, radius=results[k][2])
                    self.pack_state.update_cell(i, j, frame_position=frame_position, radius=results[k][2])
                    k += 1
        """

        # TODO: RDF: check if pack is known
        #       if yes, update cell information
        known_packs = self.rdf.get_pack_models_in_ontology()
        if self.pack_state.model in known_packs:
            pass
            # new_status = pt.common.Status.SUCCESS # TODO: skip cell classification and get cell model from RDF if pack is known
        new_status = pt.common.Status.FAILURE 
        print(self.name, self.status)
        return new_status

class AutoCellClass(pt.behaviour.Behaviour):
    """
    The vision module classifies the battery cells.
    SUCCESS if user accepts the classification. Pack state is updated.
    FAILURE if user rejects the classification. Pack state remains unchanged.
    """
    def __init__(self, name, rdf, pack_state, vision, gui):
        super(AutoCellClass, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state
        self.rdf = rdf
        self.status = pt.common.Status.INVALID
        self.tried = False

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(1)

        # TODO: get the probabilities from vision and the height registered in rdf
        if not self.tried:
            self.tried = True
            print("First update for behavior", self.name)
            cells_probs = self.vision.classify_cell(frame)
            self.gui.update_proposed_models(cells_probs)

        if self.gui.class_reject:
            self.gui.class_reject = False
            new_status = pt.common.Status.FAILURE
            print(self.name, new_status)

        elif self.gui.chosen_model != "":
            model = self.gui.chosen_model
            self.pack_state.cell_model = model
            print("chosen model: ", model)
            #k = 0
            #for i in range((self.pack_state.rows)):
            #    for j in range(self.pack_state.cols):
            #        self.pack_state.update_cell(i, j, model=model)
            #        k += 1
            #size = self.rdf.get_dimensions_from_cell_type(model)
            #size = (0, 0)
            # update cells information with model and size
            #for row in range(self.pack_state.rows):
            #    for col in range(self.pack_state.cols):
            #        self.pack_state.update_cell(row, col, model=model, size=(size))
            new_status = pt.common.Status.SUCCESS
            # record classification is done
            self.rdf.cell_classification()
            print(self.name, new_status)
            print(model)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            self.logger.info("Terminating: " + self.name + " with status: " + str(new_status))
            self.tried = False

class HelpedCellClass(pt.behaviour.Behaviour):
    """
    The user classifies the battery cells.
    SUCCESS when the user input is received. Pack state is updated.
    """
    # NOTE: The system may be able to classify the pack, or may determine that the pack is unseen (!). 
    # The user can override the decision either way.

    def __init__(self, name, rdf, pack_state, gui, vision):
        super(HelpedCellClass, self).__init__(name)
        self.gui = gui
        self.pack_state = pack_state
        self.rdf = rdf
        self.vision = vision
        self.status = pt.common.Status.INVALID

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(2)

        if self.gui.chosen_model != "":
            model = self.gui.chosen_model
            print("chosen model: ", model)
            self.pack_state.cell_model = model
            #radius, height = self.rdf.get_dimensions_from_cell_type(model) # !!!
            #radius, height = 85, 26
            # update cells information with model and size
            #k = 0
            #for i in range((self.pack_state.rows)):
            #    for j in range(self.pack_state.cols):
            #        self.pack_state.update_cell(i, j, model=model, radius=radius, height=height)
            #        k += 1
            # record classification is done
            # TODO: record class done by HUMAN
            self.rdf.cell_classification()
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
    def __init__(self, name, rdf, pack_state, vision, gui, robot):
        super(Detect, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state
        self.robot = robot
        self.rdf = rdf
        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(3)
        
        if not self.tried:
            self.tried = True
            print("First update for behavior", self.name)  
            # proposed_locations = []
            # update cell locations in GUI
            # for row in self.pack_state.cells:
            #    for cell in row:
            #        cx, cy = cell.frame_position
            #        r = cell.radius
            #        proposed_locations.append((cx-r, cy-r, cx+r, cy+r))
            proposed_locations = self.vision.cell_detection(frame) # center, radius
            print("proposed: ",proposed_locations)
            self.gui.update_bbs(proposed_locations, self.gui.frames[3])

        if self.gui.chosen_locations: # if chosen_locations not empty
            radius, height = self.rdf.get_dimensions_from_cell_type(self.pack_state.cell_model)
            k = 0
            # TODO: change dimensions into rows and columns rather than a single row
            self.pack_state.update_dim(1,len(self.gui.chosen_locations)) 
            for i in range(self.pack_state.rows):
                for j in range(self.pack_state.cols):
                    frame_position = self.gui.chosen_locations[k]
                    # get the center position
                    frame_position = [(frame_position[0]+frame_position[2])//2, (frame_position[1]+frame_position[3])//2]
                    self.pack_state.update_cell(i, j, model=self.pack_state.cell_model, 
                                                frame_position=frame_position,
                                                radius = radius,
                                                height = height)
                    k += 1
            # we add all of the cells and their properties to the RDF store as part of the battery pack object
            self.rdf.update_number_of_cells(rows=self.pack_state.rows, cols=self.pack_state.cols, model=self.pack_state.cell_model)
            new_status = pt.common.Status.SUCCESS
            self.rdf.object_detection()
            print(self.name, new_status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
    def terminate(self, new_status):
        self.logger.info("Terminating: " + self.name + " with status: " + str(new_status))
        self.tried = False

class Assess(pt.behaviour.Behaviour):
    """
    The vision module assesses the quality of each individual battery cell.
    SUCCESS if the user has no interventions. Pack state is updated.
    FAILURE if the user wishes to edit the assessment. Pack state remains unchanged.
    """
    def __init__(self, name, rdf, pack_state, vision, gui):
        super(Assess, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state
        self.rdf = rdf
        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(4)
        
        if not self.tried:
            self.tried = True
            print("First update for behavior", self.name)
            # current_frame = self.vision.get_current_frame() # keep old frame ???
            bbs_positions = self.gui.chosen_locations
            # get proposed qualities from vision module and update GUI
            #qualities = self.vision.assess_cells_qualities(frame=self.gui.camera_frame, bbs_positions=bbs_positions)
            qualities = []
            for i in range (len(bbs_positions)):
                qualities.append(random.randint(90,100)/100)
            self.gui.write_qualities(qualities, self.gui.frames[4], editable=True)
            self.gui.proposed_qualities = qualities
        
        if len(self.gui.chosen_qualities) != 0:
            # change to known dimensions
            i = 0
            # update cell information with the qualities
            for row in range(self.pack_state.rows):
                for col in range(self.pack_state.cols):
                    quality = self.gui.chosen_qualities[i]
                    self.pack_state.update_cell(row, col, quality=quality)
                    self.rdf.update_cell_quality(row,col,quality)
                    i += 1
            new_status = pt.common.Status.SUCCESS
            self.rdf.quality_assessment()
            print(self.name, new_status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
    def terminate(self, new_status):
        self.logger.info("Terminating: " + self.name + " with status: " + str(new_status))
        self.tried = False

class CheckCellsOK(pt.behaviour.Behaviour):
    """
    Checks the RDF store OR pack_state if cell quality is above some threshold
    SUCCESS cells above threshold
    FAILURE otherwise
    """
    def __init__(self, name, rdf, pack_state, gui):
        super(CheckCellsOK, self).__init__(name)
        self.gui = gui
        self.pack_state = pack_state
        self.rdf = rdf

    def update(self):
        if self.status == pt.common.Status.INVALID:
            print("First update for behavior", self.name)
        
        # TODO: RDF: check if cell quality above threshold, OR
        # TODO: pack_state: check if cell quality above threshold
        
        new_status = pt.common.Status.SUCCESS
        for row in self.pack_state.cells:
                for cell in row:
                    quality = cell.quality
                    if quality < 0.5:
                        new_status = pt.common.Status.FAILURE

        # TODO: RDF: update 
        print(self.name, self.status)
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
    def __init__(self, name, rdf, pack_state, vision, robot, gui, cell_m_q, cell_h_q, discard_T, keep_T, over_pack_T):
        super(AutoSort, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.robot = robot
        self.pack_state = pack_state
        self.rdf = rdf
        self.tried = False
        self.cell_m_q, self.cell_h_q = cell_m_q, cell_h_q
        self.status = pt.common.Status.INVALID
        self.discard_T, self.keep_T, self.over_pack_T = discard_T, keep_T, over_pack_T

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(5)
        new_status = pt.common.Status.RUNNING
        if not self.tried:
            self.tried = True
            print("First update for behavior", self.name)
            self.gui.write_qualities(self.gui.chosen_qualities, self.gui.frames[5])
            self.gui.write_qualities(self.gui.chosen_qualities, self.gui.frames[6])
        else:
            # get the pose of each cell + quality and perform pick and place
            new_status = pt.common.Status.SUCCESS
            for i, row in enumerate(self.pack_state.cells):
                for j, cell in enumerate(row):
                    if cell.sorted:
                        continue
                    frame_position = cell.frame_position
                    radius = cell.radius
                    print("cell height: ", cell.height)
                    print("cell type: ", cell.model)
                    print("cell position: ", cell.frame_position)
                    if cell.quality < self.cell_m_q:
                        place_pose = self.discard_T
                    else:
                        place_pose = self.keep_T   
                    try:
                        b_T_TCP = utilities.rotvec_to_T(self.robot.robot.getActualTCPPose())
                        cell.pose = self.vision.frame_pos_to_pose(frame_position, self.vision.camera, cell.height, b_T_TCP)
                        pick_pose = cell.pose
                        self.robot.pick_and_place(pick_pose, place_pose)
                        self.robot.move_to_cart_pos(self.over_pack_T)
                    except:
                        pass
                    sorted = self.vision.verify_pickup(frame_position, radius)
                    self.gui.write_outcome_picked_cell([frame_position[0], frame_position[1]], sorted, self.gui.frames[5])
                    self.gui.write_outcome_picked_cell([frame_position[0], frame_position[1]], sorted, self.gui.frames[6])
                    # update RDF
                    self.rdf.robot_pick_place()
                    self.rdf.update_cell_sorted(i, j, sorted=sorted)
                    self.rdf.pick_place_outcome(outcome=sorted)
                    if sorted:
                        self.pack_state.update_cell(i, j, sorted=sorted)
                    else:
                        should_try_again = self.rdf.should_try_again()
                        print("Should try again: ", should_try_again)
                        if not should_try_again:
                            new_status = pt.common.Status.FAILURE
                            return new_status
                        else:
                            new_status = pt.common.Status.RUNNING
                            
            if new_status == pt.common.Status.SUCCESS:
                self.rdf.end_sorting_process()
                self.rdf.end_session()
            print(self.name, new_status)
            
        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            self.logger.info("Terminating: " + self.name + " with status: " + str(new_status))
            self.tried = False

class HelpedSort(pt.behaviour.Behaviour):
    """
    GUI asks human for help.
    Human extracts the battery cells.
    SUCCESS when human input is received (task done).
    """
    def __init__(self, name, rdf, pack_state, gui, vision):
        super(HelpedSort, self).__init__(name)
        self.gui = gui
        self.vision = vision
        self.pack_state = pack_state
        self.rdf = rdf
        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(6)
        if not self.tried:
            self.tried = True
            print("First update for behavior", self.name) # TODO: put the class under RobotAction
            self.rdf.request_help()

        if self.gui.done:
            new_status = pt.common.Status.SUCCESS
            self.rdf.end_sorting_process()
            self.rdf.end_session()
            print(self.name, new_status)   
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
    def terminate(self, new_status):
        self.logger.info("Terminating: " + self.name + " with status: " + str(new_status))
        self.tried = False
    
class DiscardPack(pt.behaviour.Behaviour):
    def __init__(self, name, rdf, pack_state, gui, vision, bin_rotvec, pack_height):
        super(DiscardPack, self).__init__(name)
        self.gui = gui
        self.vision = vision
        self.pack_state = pack_state
        self.rdf = rdf
        self.bin_rotvec = bin_rotvec
        self.pack_height = pack_height
        self.status = pt.common.Status.INVALID

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(7)

        pack_location = self.pack_state.location
        try: 
            b_T_TCP = utilities.rotvec_to_T(self.robot.robot.getActualTCPPose())
            screw_T_b = self.vision.frame_pos_to_pose(pack_location, self.vision.camera, self.pack_height, b_T_TCP)
            self.robot.pick_and_place(screw_T_b,utilities.rotvec_to_T(self.bin_rotvec))
        except:
            pass

        if self.gui.done:
            new_status = pt.common.Status.SUCCESS
            print(self.name, new_status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
        
class AwaitCoverFastening(pt.behaviour.Behaviour):
    """
    Checks user input if cover fastening is complete
    SUCCESS when input received
    """
    def __init__(self, name, rdf, gui, vision):
        super(AwaitCoverFastening, self).__init__(name)
        self.gui = gui
        self.rdf = rdf
        self.vision = vision

    def update(self):
        frame = self.vision.get_current_frame()
        self.gui.update_image(frame)
        self.gui.show_frame(12)

        if self.gui.confirm:
            self.gui.confirm = False
            # TODO: RDF: update
            new_status = pt.common.Status.SUCCESS
            print(self.name, self.status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status