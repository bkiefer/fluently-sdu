import py_trees as pt

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
        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        new_status = pt.common.Status.SUCCESS
        # User input
        
        # new_status = pt.common.Status.SUCCESS
        # new_status = pt.common.Status.FAILURE

        return new_status
    
    def terminate(self, new_status):
        self.blackboard.set(self.name, new_status)
        self.rdf.update_rdf(node = self.name)


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
        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        new_status = pt.common.Status.SUCCESS

        # User input
        
        # battery_pack_class = gui.receive_input()
        # pack_state.update_pack_state() 
        # new_status = pt.common.Status.SUCCESS

        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            self.blackboard.set(self.name, new_status)        
            self.rdf.update_rdf(node = self.name)

class AutoDetect(pt.behaviour.Behaviour):
    """
    The vision module detects the individual battery cells.
    SUCCESS if the user has no interventions. Pack state is updated.
    FAILURE if the user wishes to edit the detection. Pack state remains unchanged.
    """
    def __init__(self, name, blackboard, rdf, pack_state, vision, gui):
        super(AutoDetect, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state
        self.blackboard = blackboard
        self.rdf = rdf
        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        new_status = pt.common.Status.SUCCESS

        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            self.blackboard.set(self.name, new_status)        
            self.rdf.update_rdf(node = self.name)

class HelpedDetect(pt.behaviour.Behaviour):
    """
    The user adds bounding boxes via the GUI to complete the battery cell detection.
    Pack state is updated.
    SUCCESS when the user input is received.
    """

    def __init__(self, name, blackboard, rdf, pack_state, vision, gui):
        super(HelpedDetect, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state
        self.blackboard = blackboard
        self.rdf = rdf
        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        new_status = pt.common.Status.SUCCESS

        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            self.blackboard.set(self.name, new_status)        
            self.rdf.update_rdf(node = self.name)

class AutoAssess(pt.behaviour.Behaviour):
    """
    The vision module assesses the quality of each individual battery cell.
    SUCCESS if the user has no interventions. Pack state is updated.
    FAILURE if the user wishes to edit the assessment. Pack state remains unchanged.
    """
    def __init__(self, name, blackboard, rdf, pack_state, vision, gui):
        super(AutoAssess, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state
        self.blackboard = blackboard
        self.rdf = rdf
        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        new_status = pt.common.Status.SUCCESS

        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            self.blackboard.set(self.name, new_status)        
            self.rdf.update_rdf(node = self.name)

class HelpedAssess(pt.behaviour.Behaviour):
    """
    The user corrects the assessments.
    Pack state is updated.
    SUCCESS when the user input is received.
    """

    def __init__(self, name, blackboard, rdf, pack_state, vision, gui):
        super(HelpedAssess, self).__init__(name)
        self.vision = vision
        self.gui = gui
        self.pack_state = pack_state
        self.blackboard = blackboard
        self.rdf = rdf
        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        new_status = pt.common.Status.SUCCESS

        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            self.blackboard.set(self.name, new_status)        
            self.rdf.update_rdf(node = self.name)


class AutoSort(pt.behaviour.Behaviour):
    """
    The pick up area is determined by the vision module.
    The place area is determined by the pack state.
    The robot performs pick and place for each battery cell.
    The vision module determines if grasping and pick up is successful for each cell.
    The pack state is updated.
    If necessary there is a nozze swap / ask for human help.

    NOTE: SUCCESS if all pick and place actions succeed or some other criterion? 
    """
    def __init__(self, name, blackboard, rdf, pack_state, vision, robot):
        super(AutoSort, self).__init__(name)
        self.vision = vision
        self.robot = robot
        self.pack_state = pack_state
        self.blackboard = blackboard
        self.rdf = rdf
        self.tried = False
        self.status = pt.common.Status.INVALID

    def update(self):
        new_status = pt.common.Status.SUCCESS

        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            self.blackboard.set(self.name, new_status)        
            self.rdf.update_rdf(node = self.name)

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
        new_status = pt.common.Status.SUCCESS

        return new_status
    
    def terminate(self, new_status):
        if new_status != pt.common.Status.INVALID:
            self.blackboard.set(self.name, new_status)        
            self.rdf.update_rdf(node = self.name)