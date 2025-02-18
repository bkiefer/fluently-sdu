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
        self.robot = RdfProxy.rdf2pyobj('<cim:robot1>')
        self.user = None
        self.session = None

    def get_user(self, node, first_name: str, last_name: str):
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

    def start_session(self, node):
        if self.session is not None:
            self.end_session(node)
        self.session = RdfProxy.getObject("UserSession")
        self.user.userSessions.add(self.session)
        self.session.user = self.user
        return self.session

    def end_session(self, node):
        self.session = None

    def __session_part(self, what: str):
        part = RdfProxy.getObject(what)
        self.session.hasConstituent.add(part)
        return part

    def __get_last_session_constituent(self, clazz):
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

    def dimensions_checked(self, node):
        """record system has checked dimension"""
        return self.__session_part("CheckedDimensions")
    
    def request_help(self, node):
        """ 
        TODO: specify what the system is asking for help about
        TODO: put class under RobotAction
        """
        requesthelp = self.__session_part("RequestHelp")
        return requesthelp