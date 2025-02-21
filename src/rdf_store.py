import time
import sys
import os
import numpy as np
import re

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
        self.user = None
        self.session = None
        self.battery_pack = None
        self.battery_cells = []

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
        self.battery_pack = RdfProxy.getObject("BatteryPack")
        self.session.hasConstituent.add(self.battery_pack)
        self.single_battery_cell = RdfProxy.getObject("BatteryCell")
        now = time.time()
        self.sorting_process.fromTime = round(now*1000)

    def end_sorting_process(self):
        """
        Records that a sorting process has ended. 
        A process is part of the session, which can include multiple processes.
        """
        now = time.time()
        self.sorting_process.toTime = round(now*1000)
    
    def get_model_instance(self, model: str):
        query = 'select ?inst where ?inst <rdf:type> <cim:BatteryCell> ?_' \
            ' & ?inst <soma:hasNameString> "{}"^^<xsd:string> ?_'.format(model)
        insts = RdfProxy.selectQuery(query)
        return None if not insts else insts[0]

    def get_dimensions_from_cell_type(self, model: str):
        """
        Records the cell model name following the classification step. 
        Returns the dimensions of the cell type in (height, diameter)
        """
        model_str = self.get_model_instance(model) # verify that cell model is in the ontology 
        self.single_battery_cell.hasPart.add(model_str) # add the verified model as a property of the single battery cell

        # Get the height of the battery cell "model" from the ontology
        query = 'select distinct ?height where ?cell <soma:hasHeight> ?height ?_ & ?cell <rdf:type> <cim:BatteryCell> ?_ '\
            ' & ?cell <soma:hasNameString> "{}"^^<xsd:string> ?_'.format(model)
        height = RdfProxy.selectQuery(query)[0]
        
        # Get the diameter of the battery cell from the ontology
        query = 'select distinct ?diam where ?cell <cim:hasDiameter> ?diam ?_ & ?cell <rdf:type> <cim:BatteryCell> ?_ '\
            ' & ?cell <soma:hasNameString> "{}"^^<xsd:string> ?_'.format(model)
        diameter = RdfProxy.selectQuery(query)[0]

        # Record cell size in RDF store
        self.single_battery_cell.hasDiameter = diameter
        self.single_battery_cell.hasHeight = height

        print(height, diameter)
        return (height,diameter)

    def update_number_of_cells(self, rows: int, cols:int, model: str):
        for row in range(rows):
            for col in range(cols):
                cell = RdfProxy.getObject("BatteryCell")
                cell.hasHeight = self.single_battery_cell.hasHeight
                cell.hasDiameter = self.single_battery_cell.hasDiameter
                cell.hasPositionData = str((row,col))
                model_str = self.get_model_instance(model)            
                cell.hasPart.add(model_str)
                self.battery_pack.hasPart.add(cell)
    
    def update_cell_sorted(self, row: int, col:int, sorted: bool):
        for cell in self.battery_pack.hasPart:
            if cell.hasPositionData == str((row,col)):
                cell.wasSorted = sorted

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
            # TODO: at least log a warning
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
    
    def object_classification(self):
        """record the robot has classified object (session constituent)"""
        return self.__session_part("ObjectClassification")
    
    def object_detection(self):
        """record the robot has detected object (session constituent)"""
        return self.__session_part("ObjectDetection")
    
    def quality_assessment(self):
        """record the robot has assessed quality of object (session constituent)"""
        return self.__session_part("QualityAssessment")
    
    def request_help(self):
        """ 
        TODO: specify what the robot is asking for help about (request.hasConstituent.add(?))
        """
        requesthelp = self.__session_part("RequestHelp")
        requesthelp.hasParticipant.add(self.robot)
        return requesthelp