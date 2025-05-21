import py_trees as pt
import time
import random
import spatialmath as sm
from gubokit import utilities
import statistics

class GeneralBehavior(pt.behaviour.Behaviour):
    def __init__(self, name, rdf, gui, vision, frame_id=None, pack_state=None, robot=None, bin_rotvec=None, pack_height=None, 
                 over_pack_T=None, cell_m_q=None, cell_h_q=None, discard_T=None, keep_T=None):
        super(GeneralBehavior, self).__init__(name)
        self.rdf = rdf
        self.gui = gui
        self.vision = vision
        self.frame_id = frame_id
        self.pack_state = pack_state
        self.robot = robot
        self.bin_rotvec = bin_rotvec
        self.pack_height = pack_height
        self.over_pack_T = over_pack_T
        self.cell_m_q, self.cell_h_q = cell_m_q, cell_h_q
        self.discard_T, self.keep_T, self.over_pack_T = discard_T, keep_T, over_pack_T
        self.frame = None

    def update(self):
        self.frame = self.vision.get_current_frame(format="pil")
        self.gui.update_image(self.frame)
        #if self.frame_id and self.frame_id != self.gui.active_frame:
        #    self.gui.show_frame(self.frame_id)
        if self.frame_id:
            self.gui.show_frame(self.frame_id)
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            self.logger.info("Terminating: " + self.name + " with status: " + str(new_status))

class Idle(GeneralBehavior):
    """
    Awaits human
    """
    def update(self):
        super().update()
        new_status = pt.common.Status.RUNNING
        return new_status

class BeginSession(GeneralBehavior):
    """
    Sets up the user and session in the RDF store
    """
    def update(self):
        super().update()
        if self.gui.first_name != None:
            # register name and start session
            self.rdf.get_user(first_name = self.gui.first_name, last_name = self.gui.last_name)
            self.rdf.start_session()
            new_status = pt.common.Status.SUCCESS
            print(self.name, new_status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
class PackPlaced(GeneralBehavior):
    """
    Await pack placed and fastened
    """
    def update(self):
        super().update()
        # register battery placed from human confirmation
        if self.gui.confirm:
            self.gui.confirm = False
            self.rdf.human_place_battery()
            new_status = pt.common.Status.SUCCESS
            print(self.name, new_status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
class AutoPackClass(GeneralBehavior):
    """
    The vision module classifies the pack.
    SUCCESS if user accepts the classification. Pack state is updated.
    FAILURE if user rejects the classification or the robot does not recognize the pack. 
    """
    def __init__(self, name, rdf, gui, vision, frame_id, pack_state, robot, pack_height):
        super().__init__(name=name, rdf=rdf, gui=gui, vision=vision, frame_id=frame_id, pack_state=pack_state, robot=robot, pack_height=pack_height)
        self.proposed_pack = None
        self.result = None

    def update(self):
        super().update()
        intent = self.gui.mqtt.get_intent()
    
        if not self.result:
            # locate pack with vision module
            self.result = self.vision.locate_pack(self.frame)
            known_models = self.rdf.get_known_packs()
            if not self.result:
                self.proposed_pack = "unknown"
                self.gui.update_proposed_packs([self.proposed_pack]+known_models)
            else:
                self.proposed_pack = self.result["shape"]
                if self.proposed_pack in known_models:
                    # put proposed pack in front of list
                    known_models.remove(self.proposed_pack)
                    self.gui.update_proposed_packs([self.proposed_pack]+known_models)
                else: 
                    self.gui.update_proposed_packs(["unknown"]+known_models)
            new_status = pt.common.Status.RUNNING

        elif self.gui.class_reject:
            self.gui.class_reject = False
            new_status = pt.common.Status.FAILURE
            print(self.name, new_status)

        elif self.gui.chosen_pack != "":
            if self.proposed_pack == "unknown":
                new_status = pt.common.Status.FAILURE
            else:
                # record in rdf and update pack state
                self.rdf.battery_classification() # should specify no help from human
                self.rdf.record_pack_type(self.result["shape"]) # change to actual label
                self.pack_state.model = self.result["shape"]
                self.pack_state.size = self.result["size"]
                self.pack_state.cover_on = self.result["cover_on"] # use vision function cell_detection()?
                self.pack_state.location = self.result["location"]
                try:   
                    b_T_TCP = utilities.rotvec_to_T(self.robot.robot.getActualTCPPose())
                    pack_T_b = self.vision.frame_pos_to_pose(self.pack_state.location, self.vision.camera, self.pack_height, b_T_TCP)
                    self.pack_state.pose = pack_T_b
                except:
                    pass
                # TODO: RDF: record if classification was successful
                # TODO: RDF: update and upload disassembly plan
                new_status = pt.common.Status.SUCCESS
            print(self.name, new_status)
        else:
            if intent == "yes":
                self.gui.frames[15].confirm()
            elif intent == "no":
                self.gui.frames[15].deny()

            new_status = pt.common.Status.RUNNING
        self.gui.mqtt.clear_intents()
        return new_status
    
class HelpedPackClass(GeneralBehavior):
    """
    The user classifies the pack.
    SUCCESS when the user input is received. Pack state is updated.    
    """
    def update(self):
        super().update()
        if self.gui.chosen_pack != "":
            # record in rdf and update pack state
            model = self.gui.chosen_pack
            self.rdf.record_pack_type(pack_name=model)
            self.pack_state.model = model
            
            self.gui.update_bbs([], self.gui.frames[17])
            
            #frame = self.vision.get_current_frame(format="pil")
            #cells = self.vision.cell_detection(frame)
            #self.pack_state.cover_on = True if not cells else False
            #self.rdf.check_cover(cells_visible=False if not cells else True)
            #self.rdf.battery_classification() # should specify help from human
            new_status = pt.common.Status.SUCCESS
            print(self.name, new_status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
class HelpedLocatePack(GeneralBehavior):
    """
    The user locates the pack using the GUI.
    SUCCESS when the user input is received. Pack state is updated.    
    """
    def update(self):
        super().update()
        new_status = pt.common.Status.RUNNING
        if not self.gui.bbs_editor.box_items:
            self.gui.bbs_editor.spawn_box()

        elif self.gui.chosen_pack_location:
            location = self.gui.chosen_pack_location[0]
            frame_position = ((location[0]+location[2])//2, (location[1]+location[3])//2)
            self.pack_state.location = frame_position
            b_T_TCP = utilities.rotvec_to_T(self.robot.robot.getActualTCPPose())
            pack_T_b = self.vision.frame_pos_to_pose(self.pack_state.location, self.vision.camera, self.pack_height, b_T_TCP)
            self.pack_state.pose = pack_T_b
            new_status = pt.common.Status.SUCCESS
            # record in RDF
            print(self.name, new_status)
        return new_status

class CheckCoverOff(GeneralBehavior):
    """
    The vision module determines if the pack is covered.
    SUCCESS if cover is off.
    FAILURE if cover is on.
    """
    def update(self):
        super().update()
        #cells = self.vision.cell_detection(self.frame) # Needs to be changed
        #if len(cells) > 3: # Needs to be changed
        #        self.pack_state.cover_on = False
        #        self.rdf.check_cover(cells_visible=True)
        #        new_status = pt.common.Status.SUCCESS
        #else:
        new_status = pt.common.Status.FAILURE
        return new_status
    
    def terminate(self, new_status):
        if new_status == pt.common.Status.SUCCESS:
            self.logger.info("Terminating: " + self.name + " with status: " + str(new_status))

class CheckHumanRemovesCover(GeneralBehavior):
    """
    Checks the RDF store OR user input if the human should remove the cover
    SUCCESS if human should remove cover
    FAILURE otherwise
    """
    def update(self):
        super().update()
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

class CheckColabRemoveCover(GeneralBehavior):
    """
    Checks the RDF store OR user input if cover removal is collaborative
    SUCCESS if collaborative
    FAILURE otherwise
    """
    def update(self):
        super().update()
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
        return new_status

class ColabAwaitHuman(GeneralBehavior):
    """
    Wait for human acknowledgement that they are ready for robot to remove cover
    SUCCESS when acknowledged
    """
    def update(self):
        super().update()
        if self.gui.confirm:
            self.gui.confirm = False
            # TODO: RDF: update
            new_status = pt.common.Status.SUCCESS
            print(self.name, self.status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
class RemoveCover(GeneralBehavior):
    """
    Robot removes cover
    SUCCESS when done
    """
    def update(self):
        super().update()

        self.robot.pick_and_place(self.pack_state.pose,utilities.rotvec_to_T(self.bin_rotvec))
        self.robot.robot.moveL(self.over_pack_T)
        self.rdf.robot_remove_cover()
        new_status = pt.common.Status.SUCCESS
        print(self.name, new_status)
        return new_status
    
class AwaitToolChange(GeneralBehavior):
    """
    Checks user input if tool change is complete
    This step is used for any tool change
    SUCCESS tool change is complete 
    """
    def update(self):
        super().update()
        if self.gui.confirm:
            self.gui.confirm = False
            self.rdf.switch_tool()
            new_status = pt.common.Status.SUCCESS
            tool = self.rdf.get_robot_tool()
            try:
                if tool == "large":
                    self.robot.change_gripper("big")
                elif tool == "small": 
                    self.robot.change_gripper("small")
            except:
                pass
            print(self.name, self.status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status

class BigGripper(GeneralBehavior):
    """
    Checks if big gripper is equipped.
    SUCCESS if true.
    """
    def update(self):
        super().update()
        new_status = pt.common.Status.RUNNING
        last_tool = self.rdf.get_robot_tool()
        if last_tool == "small":
            #self.robot.change_gripper("small") # UNCOMMENT
            new_status = pt.common.Status.FAILURE
        elif last_tool == "large":
            #self.robot.change_gripper("big") # UNCOMMENT
            new_status = pt.common.Status.SUCCESS

        elif self.gui.gripper != "":
            if self.gui.gripper == "large":
                new_status = pt.common.Status.SUCCESS
                self.rdf.record_robot_tool("large")
                #self.robot.change_gripper("big") # UNCOMMENT
            else: 
                new_status = pt.common.Status.FAILURE
                self.rdf.record_robot_tool("small")
                #self.robot.change_gripper("small") # UNCOMMENT
            self.gui.gripper = ""
        return new_status

class SmallGripper(GeneralBehavior):
    """
    Checks if small gripper is equipped.
    SUCCESS if true.
    """
    def update(self):
        super().update()
        
        new_status = pt.common.Status.RUNNING
        last_tool = self.rdf.get_robot_tool()
        
        if last_tool == "small":
            # self.robot.change_gripper("small") # UNCOMMENT
            new_status = pt.common.Status.SUCCESS
        elif last_tool == "large": 
            # self.robot.change_gripper("big") # UNCOMMENT
            new_status = pt.common.Status.FAILURE     
        
        elif self.gui.gripper != "":
            if self.gui.gripper == "small":
                new_status = pt.common.Status.SUCCESS # UNCOMMENT
                self.rdf.record_robot_tool("small")
                # self.robot.change_gripper("small")
            else: 
                new_status = pt.common.Status.FAILURE # UNCOMMENT
                self.rdf.record_robot_tool("large")
                # self.robot.change_gripper("big")
            self.gui.gripper = ""
        return new_status
        
class CheckPackKnown(GeneralBehavior):
    """
    Checks the RDF store if pack is known
    SUCCESS if pack is known
    FAILURE otherwise
    """
    def update(self):
        super().update()
        if self.status == pt.common.Status.INVALID:
            print("First update for behavior", self.name) 
        # TODO: RDF: check if pack is known
        #       if yes, update cell information
        known_packs = self.rdf.get_known_packs() # change this
        if self.pack_state.model in known_packs:
            pass
            # new_status = pt.common.Status.SUCCESS # TODO: skip cell classification and get cell model from RDF if pack is known
        new_status = pt.common.Status.FAILURE 
        print(self.name, self.status)
        return new_status

class AutoCellClass(GeneralBehavior):
    """
    The vision module classifies the battery cells.
    SUCCESS if user accepts the classification. Pack state is updated.
    FAILURE if user rejects the classification. Pack state remains unchanged.
    """
    def __init__(self, name, rdf, gui, vision, frame_id, pack_state, robot, pack_height):
        super().__init__(name=name, rdf=rdf, gui=gui, vision=vision, frame_id=frame_id, pack_state=pack_state, robot=robot, pack_height=pack_height)
        self.cell_class_dict = {}

    def update(self):
        super().update()
        intent = self.gui.mqtt.get_intent()
        if not self.cell_class_dict:                
            self.robot.move_to_cart_pos(self.pack_state.pose*sm.SE3([-0.05, 0.03,-0.05]))
            self.cell_class_dict = self.vision.classify_cell(self.frame)
            model = str(self.cell_class_dict["model"])
            known_cells = self.rdf.get_known_cells()
            known_cells.insert(0, known_cells.pop(known_cells.index(model)))
            self.gui.update_proposed_models(known_cells) 

            bbs = self.cell_class_dict['bbs']
            print("bbs: ",bbs)
            zs = self.cell_class_dict['zs']
            print("zs: ",zs)
            z = statistics.median(zs)

            self.pack_state.update_dim(1,len(bbs)) 
            k = 0
            for i in range(self.pack_state.rows):
                for j in range(self.pack_state.cols):
                    frame_position = [bbs[k][0], bbs[k][1]]
                    print("frame position: ",frame_position)
                    width = bbs[k][2]
                    print("width: ",width)
                    z = z
                    self.pack_state.update_cell(i, j, frame_position=frame_position,
                                                width = width,
                                                z = z)
                    k += 1

        if self.gui.class_reject:
            self.gui.class_reject = False
            new_status = pt.common.Status.FAILURE
            print(self.name, new_status)

        elif self.gui.chosen_model != "":
            model = self.gui.chosen_model
            self.pack_state.cell_model = model # add rest of variables
            for i in range(self.pack_state.rows):
                for j in range(self.pack_state.cols):
                    self.pack_state.update_cell(i, j, model=self.pack_state.cell_model)
            self.rdf.cell_classification() # should specify done by robot
            new_status = pt.common.Status.SUCCESS
            print(self.name, new_status)
        else:
            if intent == "yes":
                self.gui.frames[1].confirm()
            elif intent == "no":
                self.gui.frames[1].deny()

            new_status = pt.common.Status.RUNNING
        self.gui.mqtt.clear_intents()

        return new_status

class HelpedCellClass(GeneralBehavior):
    """
    The user classifies the battery cells.
    SUCCESS when the user input is received. Pack state is updated.
    """
    # NOTE: The system may be able to classify the pack, or may determine that the pack is unseen (!). 
    # The user can override the decision either way.
    def update(self):
        super().update()
        if self.gui.chosen_model != "":
            model = self.gui.chosen_model
            print("chosen model: ", model)
            self.pack_state.cell_model = model # add rest of variables
            for i in range(self.pack_state.rows):
                for j in range(self.pack_state.cols):
                    self.pack_state.update_cell(i, j, model=self.pack_state.cell_model)
            self.rdf.cell_classification() # should specify done by human
            new_status = pt.common.Status.SUCCESS
            print(self.name, new_status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status

class Detect(GeneralBehavior):
    """
    The vision module detects the individual battery cells.
    SUCCESS when the detection is accepted. Pack state is updated.
    """
    def __init__(self, name, rdf, gui, vision, frame_id, pack_state, robot):
        super().__init__(name, rdf, gui, vision, frame_id, pack_state, robot)
        self.proposed_bbs = []
        self.z = 0
    def update(self):
        super().update()
        if not self.proposed_bbs:
            print("First update for behavior", self.name)  
            for i in range(self.pack_state.rows):
                for j in range(self.pack_state.cols):
                    cx = self.pack_state.cells[i][j].frame_position[0]
                    cy = self.pack_state.cells[i][j].frame_position[1]
                    r = self.pack_state.cells[i][j].width/2
                    self.z = self.pack_state.cells[i][j].z
                    self.proposed_bbs.append((cx-r, cy-r, cx+r, cy+r))
                self.gui.update_bbs(self.proposed_bbs, self.gui.frames[3])

        if self.gui.chosen_locations: # if chosen_locations not empty
            print(self.gui.chosen_locations)
            bbs = []
            
            for i in self.gui.chosen_locations:
                print("location: ",i)
                width = i[3]-i[1]
                cx = i[0]+(width/2)
                cy = i[1]+(width/2)
                bbs.append([cx,cy,width])
            
            #bbs = [[self.gui.chosen_locations[i][0], self.gui.chosen_locations[i][1]] for i in self.gui.chosen_locations]
            #print("bbs: ",bbs)
            #zs = [self.gui.chosen_locations[i][2] for i in self.gui.chosen_locations]
            #print("zs: ",zs)

            #self.pack_state.update_dim(1,len(bbs)) 
            k = 0
            for i in range(self.pack_state.rows):
                for j in range(self.pack_state.cols):
                    frame_position = [bbs[k][0], bbs[k][1]]
                    print("frame position: ",frame_position)
                    width = bbs[k][2]
                    print("width: ",width)
                    z = self.z
                    self.pack_state.update_cell(i, j, model=self.pack_state.model, 
                                                frame_position=frame_position,
                                                width = width,
                                                z = z)
                    k += 1

            #radius, height = self.rdf.get_dimensions_from_cell_type(self.pack_state.cell_model)
            #k = 0
            ## TODO: change dimensions into rows and columns rather than a single row
            #self.pack_state.update_dim(1,len(self.gui.chosen_locations)) 
            #for i in range(self.pack_state.rows):
            #    for j in range(self.pack_state.cols):
            #        frame_position = self.gui.chosen_locations[k]
            #        # get the center position
            #        frame_position = [(frame_position[0]+frame_position[2])//2, (frame_position[1]+frame_position[3])//2]
            #        self.pack_state.update_cell(i, j, model=self.pack_state.cell_model, 
            #                                    frame_position=frame_position,
            #                                    radius = radius,
            #                                    height = height)
            #        k += 1
            # we add all of the cells and their properties to the RDF store as part of the battery pack object
            #self.rdf.update_number_of_cells(rows=self.pack_state.rows, cols=self.pack_state.cols, model=self.pack_state.cell_model)
            
            new_status = pt.common.Status.SUCCESS
            self.rdf.object_detection()
            print(self.name, new_status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status

class Assess(GeneralBehavior):
    """
    The vision module assesses the quality of each individual battery cell.
    SUCCESS if the user has no interventions. Pack state is updated.
    FAILURE if the user wishes to edit the assessment. Pack state remains unchanged.
    """
    def __init__(self, name, rdf, gui, vision, frame_id, pack_state):
        super().__init__(name, rdf, gui, vision, frame_id, pack_state)
        self.bbs_positions = []

    def update(self):
        super().update()
        if not self.bbs_positions:
            print("First update for behavior", self.name)
            # current_frame = self.vision.get_current_frame(format="pil") # keep old frame ???
            self.bbs_positions = self.gui.chosen_locations
            # get proposed qualities from vision module and update GUI
            #qualities = self.vision.assess_cells_qualities(frame=self.gui.camera_frame, bbs_positions=bbs_positions)
            qualities = []
            for i in range (len(self.bbs_positions)):
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

class CheckCellsOK(GeneralBehavior):
    """
    Checks the RDF store OR pack_state if cell quality is above some threshold
    SUCCESS cells above threshold
    FAILURE otherwise
    """
    def update(self):
        super().update()
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

class AutoSort(GeneralBehavior):
    """
    The robot performs pick and place for each battery cell.
    The vision module determines if grasping and pick up is successful for each cell.
    """
    
    def __init__(self, name, rdf, gui, vision, frame_id, pack_state, robot, over_pack_T, cell_m_q, cell_h_q, discard_T, keep_T):
        super().__init__(name=name, rdf=rdf, gui=gui, vision=vision, frame_id=frame_id, pack_state=pack_state, robot=robot, over_pack_T=over_pack_T, cell_m_q=cell_m_q, cell_h_q=cell_h_q, discard_T=discard_T, keep_T=keep_T)

    def update(self):
        super().update()
        new_status = pt.common.Status.RUNNING
        if self.rdf.sorting_process != None:
            self.rdf.start_sorting_process()
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
                    radius = cell.width/2
                    z = cell.z
                    if cell.quality < self.cell_m_q:
                        place_pose = self.discard_T
                    else:
                        place_pose = self.keep_T
                    
                    base_T_TCP = utilities.rotvec_to_T(self.robot.robot.getActualTCPPose())
                    cell_T = self.vision.frame_pos_to_pose(frame_pos=frame_position, camera=self.vision.camera, Z=z, base_T_TCP=base_T_TCP)
                    self.robot.pick_and_place(cell_T, place_pose)


                    #b_T_TCP = utilities.rotvec_to_T(self.robot.robot.getActualTCPPose())
                    #cell.pose = self.vision.frame_pos_to_pose(frame_position, self.vision.camera, cell.height, b_T_TCP)
                    #pick_pose = cell.pose
                    #self.robot.pick_and_place(pick_pose, place_pose)
                    #self.robot.move_to_cart_pos(self.over_pack_T)
                    
                    sorted = self.vision.verify_pickup(frame_position, radius)
                    self.gui.write_outcome_picked_cell([frame_position[0], frame_position[1]], sorted, self.gui.frames[5])
                    self.gui.write_outcome_picked_cell([frame_position[0], frame_position[1]], sorted, self.gui.frames[6])
                    
                    # update RDF
                    self.rdf.robot_pick_place()
                    self.rdf.update_cell_sorted(i, j, sorted=sorted)
                    self.rdf.pick_place_outcome(outcome=sorted)
                    if sorted:
                        self.pack_state.update_cell(i, j, sorted=sorted)
                    #else:
                    #    should_try_again = self.rdf.should_try_again()
                    #    print("Should try again: ", should_try_again)
                    #    if not should_try_again:
                    #        new_status = pt.common.Status.FAILURE
                    #        return new_status
                    #    else:
                    #        new_status = pt.common.Status.RUNNING
                            
            if new_status == pt.common.Status.SUCCESS:
                self.rdf.end_sorting_process()
                self.rdf.end_session()
            print(self.name, new_status)

        return new_status

class HelpedSort(GeneralBehavior):
    """
    GUI asks human for help.
    Human extracts the battery cells.
    SUCCESS when human input is received (task done).
    """
    def update(self):
        super().update()
        if self.gui.done:
            self.rdf.request_help()
            new_status = pt.common.Status.SUCCESS
            self.rdf.end_sorting_process()
            self.rdf.end_session()
            print(self.name, new_status)   
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
    
class DiscardPack(GeneralBehavior):
    def update(self):
        super().update()
        pack_location = self.pack_state.location

        b_T_TCP = utilities.rotvec_to_T(self.robot.robot.getActualTCPPose())
        screw_T_b = self.vision.frame_pos_to_pose(pack_location, self.vision.camera, self.pack_height, b_T_TCP)
        self.robot.pick_and_place(screw_T_b,utilities.rotvec_to_T(self.bin_rotvec))

        if self.gui.done:
            new_status = pt.common.Status.SUCCESS
            print(self.name, new_status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status
        
class AwaitCoverFastening(GeneralBehavior):
    """
    Checks user input if cover fastening is complete
    SUCCESS when input received
    """
    def update(self):
        super().update()
        if self.gui.confirm:
            self.gui.confirm = False
            # TODO: RDF: update
            new_status = pt.common.Status.SUCCESS
            print(self.name, self.status)
        else:
            new_status = pt.common.Status.RUNNING
        return new_status