import time
import sys
import os
import numpy as np
import re
import logging

from hfc_thrift.rdfproxy import RdfProxy

class RdfStore:
    """
    This class provides all API functions to register the data from the
    behaviour tree execution and to retrieve neccessary information from there
    """

    def __init__(self, port=7070):
        mapclass = { "<cim:Offer>": "Offer",
                     "<cim:Decline>" : "Decline",
                     "<cim:Accept>" : "Accept",
                     "<cim:Question>" : "Question",
                     "<cim:YNQuestion>" : "YNQuestion"}
        RdfProxy.init_rdfproxy(port=port, classmapping=mapclass)
        self.robot = RdfProxy.getObject('Cobot')
        self.robot.hasTool = "unknown"
        self.user = None
        self.session = None
        self.battery_pack = None
        self.battery_cells = []
        self.sorting_process = None
        

    def get_user(self, first_name: str, last_name: str):
        """
        If the user already exists in the RDF store we return this user object.
        Else create a new user object with the input names.
        """
        users = RdfProxy.selectQuery(
            'select ?uri where ?uri <rdf:type> <cim:User> ?_ '
            '& ?uri <soho:hasName> "{first_name}" ?_ '
            '& ?uri <soho:hasSurname> "{last_name}" ?_'.format(first_name=first_name,last_name=last_name))
        if not users:
            self.user = RdfProxy.getObject("User")
            self.user.hasName = first_name
            self.user.hasSurname = last_name
        else:
            self.user = users[0]
        return self.user

    def start_session(self):
        """
        Records that a user session has started. 
        A user session can comprise several processes (e.g., scans, disassembly task, sorting task).
        Thus the user session describes an entire interaction from beginning to end.
        """
        if self.session is not None:
            self.end_session()
        self.session = RdfProxy.getObject("UserSession")
        self.user.userSessions.add(self.session)
        self.session.user = self.user
        self.session.hasParticipant.add(self.robot)
        
        return self.session
    
    def end_session(self):
        """
        Records that a user session has ended. 
        A user session describes an entire interaction from beginning to end.
        """
        self.session = None
    
    def start_sorting_process(self):
        """
        Records that a sorting process has started. 
        A process is part of the session, which can include multiple processes.
        """
        self.sorting_process = self.__session_part("SortingProcess")
        now = time.time()
        self.sorting_process.fromTime = round(now*1000)
    
    def end_sorting_process(self):
        """
        Records that a sorting process has ended. 
        A process is part of the session, which can include multiple processes.
        """
        now = time.time()
        self.sorting_process.toTime = round(now*1000)
    
    def get_cell_model_instance(self, model: str):
        query = 'select ?cell where ?cell <rdf:type> <cim:BatteryCell> ?_' \
            ' & ?cell <soma:hasNameString> "{}"^^<xsd:string> ?_'.format(model)
        cells = RdfProxy.selectQuery(query)
        return None if not cells else cells[0]

    def get_known_cells(self): 
        query = 'select distinct ?str where ?pack <soho:hasLabel> ?str ?_ ' \
                ' & ?pack <rdf:type> <cim:BatteryCell> ?_'
        models = RdfProxy.selectQuery(query)
        print("Models: ",models)
        return models

    def get_known_packs(self): # change this
        query = 'select distinct ?str where ?pack <soho:hasLabel> ?str ?_ ' \
                ' & ?pack <rdf:type> <cim:BatteryPack> ?_'
        models = RdfProxy.selectQuery(query)
        return models
    
    def get_dimensions_from_cell_type(self, model: str):
        """
        Records the cell model name following the classification step. 
        Returns the dimensions of the cell type in (height, diameter)
        """
        print("model: ",model)
        model_str = self.get_cell_model_instance(model) # verify that cell model is in the ontology 
        print("model_str: ",model_str)
        if model_str:
            self.single_battery_cell.isClassifiedBy.add(model_str) # add the verified model as a property of the single battery cell

            # Get the height of the battery cell "model" from the ontology
            query = 'select distinct ?height where ?cell <soma:hasHeight> ?height ?_ & ?cell <rdf:type> <cim:BatteryCell> ?_ '\
                ' & ?cell <soma:hasNameString> "{}"^^<xsd:string> ?_'.format(model)
            height = RdfProxy.selectQuery(query)[0]
            
            # Get the diameter of the battery cell from the ontology
            query = 'select distinct ?diam where ?cell <cim:hasDiameter> ?diam ?_ & ?cell <rdf:type> <cim:BatteryCell> ?_ '\
                ' & ?cell <soma:hasNameString> "{}"^^<xsd:string> ?_'.format(model)
            diameter = RdfProxy.selectQuery(query)[0]
        else:
            height = 0.0
            diameter = 0.0

        # Record cell size in RDF store
        self.single_battery_cell.hasDiameter = diameter
        self.single_battery_cell.hasHeight = height

        print(diameter/2, height)
        return (diameter/2,height)
     
    def update_number_of_cells(self, rows: int, cols:int, model: str):
        for row in range(rows):
            for col in range(cols):
                cell = RdfProxy.getObject("BatteryCell")
                cell.hasHeight = self.single_battery_cell.hasHeight
                cell.hasDiameter = self.single_battery_cell.hasDiameter
                cell.hasPositionData = str((row,col))
                model_str = self.get_cell_model_instance(model) 
                if model_str:           
                    cell.isClassifiedBy.add(model_str)
                self.battery_pack.hasPart.add(cell)
    
    def update_cell_sorted(self, row: int, col:int, sorted: bool):
        for cell in self.battery_pack.hasPart:
            if cell.hasPositionData == str((row,col)):
                cell.wasSorted = str(sorted)
    
    def update_cell_quality(self, row:int, col:int, quality: float):
        for cell in self.battery_pack.hasPart:
            if cell.hasPositionData == str((row,col)):
                cell.hasQuality = quality
    
    def __session_part(self, object: str):
        """
        Links the session (subject) with another part (object) as a constituent (the predicate).
        Takes the object as input.
        """
        part = RdfProxy.getObject(object)
        self.session.hasConstituent.add(part)
        return part

    def __get_last_session_constituent(self, clazz):
        """
        Returns the last constituent (object) that has been linked to the session.
        """
        lastoffer = RdfProxy.selectQuery(
            'select ?off ?t where ?off <rdf:type> {} ?t'
            ' & {} <dul:hasConstituent> ?off ?_'
            ' aggregate ?res = LGetLatest2 ?off ?t "1"^^<xsd:int>'.format(
                clazz, self.session.uri))
        if not lastoffer:
            logging.warning(" No last session constituent found for class: %s",clazz)
            return None
        return lastoffer[0]

    def display_instruction(self, node):
        """
        Assumption: only the last offered instruction can be played?
        """
        lastoffer = self.__get_last_session_constituent("<cim:Offer>")
        instruction = self.__session_part("Instruction")
        instruction.hasParticipant.union(lastoffer.hasParticipant)
        return instruction
    
    def human_place_battery(self):
        """record the human has placed and fastened the battery pack on the worktable"""
        self.battery_pack = RdfProxy.getObject("BatteryPack")
        self.session.hasConstituent.add(self.battery_pack)
        self.single_battery_cell = RdfProxy.getObject("BatteryCell")
        place_battery = self.__session_part("PlaceBattery")
        return place_battery
        
    def battery_classification(self):
        """record the robot has classified the battery pack type"""
        # TODO: add information about success/failure of classification, was the pack in the DB, etc...
        # BatteryClassification data properties: hasNameString, wasSuccessful, isKnown
        # e.g., hasNameString = "unknown", wasSuccessful = "False", isKnown = "False"
        # hasNameString = ""
        return self.__session_part("BatteryClassification")
    
    def get_pack_model_instance(self, pack_name: str):
        query = 'select ?pack where ?pack <rdf:type> <cim:BatteryPack> ?_' \
            ' & ?pack <soma:hasNameString> "{}"^^<xsd:string> ?_'.format(pack_name)
        insts = RdfProxy.selectQuery(query)
        return None if not insts else insts[0]

    def record_pack_type(self, pack_name: str):
        model_str = self.get_pack_model_instance(pack_name) # verify that cell model is in the ontology 
        if model_str:
            self.battery_pack.isClassifiedBy.add(model_str) # add the verified model as a property of the single battery cell
        self.battery_pack.hasNameString = pack_name

    def identify_battery_type(self):
        """record the human has identified the battery pack type"""
        return self.__session_part("IdentifyBatteryType")
    
    def cell_classification(self):
        """record the robot has classified object (session constituent)"""
        return self.__session_part("CellClassification")
    
    def object_detection(self):
        """record the robot has detected object (session constituent)"""
        return self.__session_part("CellDetection")
    
    def quality_assessment(self):
        """record the robot has assessed quality of object (session constituent)"""
        return self.__session_part("QualityAssessment")

    def check_cover(self, cells_visible):
        """record that the robot has assessed whether or not the cover is on and the result (cellsVisible True/False)"""
        check_cover = self.__session_part("CheckCover")  
        check_cover.cellsVisible = str(cells_visible) 
        return check_cover

    def robot_pick_place(self):
        # TODO: change to a split into pickobjectaction and placeobjectaction?
        pick_place = self.__session_part("PickPlace")
        pick_place.hasParticipant.add(self.robot)
        return pick_place
    
    def pick_place_outcome(self, outcome):
        # get last pick place
        lastpickplace = self.__get_last_session_constituent("<soho:PickPlace>")
        lastpickplace.wasSuccessful = str(outcome)
        return lastpickplace
    
    def robot_remove_cover(self):
        return self.__session_part("RobotRemoveCover")
    
    def record_robot_tool(self, tool: str):
        if tool == "small":
            self.robot.hasTool = "small"
        elif tool == "large":
            self.robot.hasTool = "large"
        return
    
    def get_robot_tool(self):
        if self.robot.hasTool == "unknown":
            return None
        return self.robot.hasTool
    
    def switch_tool(self):
        if self.robot.hasTool == "small":
            self.robot.hasTool = "large"
        elif self.robot.hasTool == "large":
            self.robot.hasTool = "small"
        return 

    def request_help(self):
        """ 
        TODO: specify what the robot is asking for help about (request.hasConstituent.add(?))
        """
        requesthelp = self.__session_part("RequestHelp")
        requesthelp.hasParticipant.add(self.robot)
        return requesthelp
    
    def get_same_pack_sessions(self):        
        pack_name = self.battery_pack.hasNameString
        query = 'select distinct ?sess where ?sess <rdf:type> <cim:UserSession> ?_ ' \
                ' & ?sess <dul:hasConstituent> ?pack ?_ & ?pack <rdf:type> <cim:BatteryPack> ?_ ' \
                ' & ?pack <soma:hasNameString> "{}"^^<xsd:string> ?_'.format(pack_name)
        same_pack_sessions = RdfProxy.selectQuery(query)
        return same_pack_sessions

    def should_try_again(self):
        same_pack_sessions = self.get_same_pack_sessions()
        no_pick_place = 0
        no_failures = 0
        for sess in same_pack_sessions:
            rdf_sess = RdfProxy.python2rdf(sess)
            no_pick_place += len(RdfProxy.selectQuery('select ?p where {} <dul:hasConstituent> ?p ?_ ' \
                                                      '& ?p <rdf:type> <soho:PickPlace> ?_ ' \
                                                      '& ?p <dul:hasParticipant> ?c ?_ ' \
                                                      '& ?c <rdf:type> <soho:Cobot> ?_ '.format(rdf_sess)))
            no_failures += len(RdfProxy.selectQuery('select ?p where {} <dul:hasConstituent> ?p ?_ ' \
                                                      '& ?p <rdf:type> <soho:PickPlace> ?_ ' \
                                                      '& ?p <dul:hasParticipant> ?c ?_ ' \
                                                      '& ?p <cim:wasSuccessful> "False"^^<xsd:string> ?_ ' \
                                                      '& ?c <rdf:type> <soho:Cobot> ?_ '.format(rdf_sess)))
        failure_rate = no_failures/no_pick_place
        print("Failure rate: ", int(failure_rate*100), "%")
        if failure_rate < 0.2:
            return True
        else:
            return False