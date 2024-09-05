from hfc_thrift.rdfproxy import RdfProxy
import sys
import os
import numpy as np

DEFAULT_H_RESOLUTION = 3
DEFAULT_V_RESOLUTION = 3


class RdfStore:
    """
    This class provides all API functions to register the data from the
    behaviour tree execution and to retrieve neccessary information from there
    """

    def __init__(self, port=7070):
        RdfProxy.init_rdfproxy(port=port)
        self.robot = RdfProxy.rdf2pyobj('<cim:robot1>')

    def get_user(self, node, first_name: str, last_name: str):
        users = RdfProxy.selectQuery(
            'select ?uri where ?uri <rdf:type> <cim:User> ?_ '
            '& ?uri <soho:hasName> "John" ?_ '
            '& ?uri <soho:hasSurname> "Doe" ?_')
        if not users:
            self.user = RdfProxy.getObject("User")
            self.user.hasName = "John"
            self.user.hasSurname = "Doe"
        else:
            self.user = users[0]
        return self.user

    def start_session(self, node):
        if self.session:
            self.end_session(node)
        self.session = RdfProxy.getObject("UserSession")
        self.user.userSessions.add(self.session)
        return self.session

    def end_session(self, node):
        self.session = None

    def __session_part(self, what: str):
        part = RdfProxy.getObject(what)
        self.session.hasConstituent.add(part)
        return part

    def start_scan(self, node):
        """
        Start a new Scanningprocess in the current session, and return the
        created object.

        Modifying the horizontal or vertical resolution can be done directly on
        the object:
        scan.hasHorziontalResolution = h
        scan.hasVerticalResolution = v
        """
        self.scan = self.__session_part("ScanningProcess")
        # TODO: COMPUTE THE USER PREFERRED DEFAULT SETTINGS
        self.scan.hasHorziontalResolution = DEFAULT_H_RESOLUTION
        self.scan.hasVerticalResolution = DEFAULT_V_RESOLUTION
        return self.scan

    # For all the Offer situations, i think we should have a fixed Instance
    # which is a placeholder for what we offer, or should we create an Event
    # instance which then may never happen since it is rejected?
    def offer_instruction(self, node, which):
        """
        Robot offers to show instructions, which determines what the
        instructions are about, if applicable
        which is (i assume), an instance of VideoData (see below)
        """
        offer = self.__session_part("Offer")
        # We need to create (fixed) instances of SOMA:VideoData that represent
        # different (parts of) instruction video, that isParticipantIn this
        # Instruction (e.g., offer hasParticipant VideoData)
        offer.hasParticipant.add(which)
        return offer

    def __get_last_session_constituent(self, clazz):
        lastoffer = RdfProxy.selectQuery(
            'select ?off ?t where ?off <rdf:type> {} ?t'
            ' & {} <DUL:hasConstituent> ?off ?_'
            ' aggregate ?res = LGetLatest2 ?s ?t "1"^^<xsd:int>'.format(
                clazz, self.session.uri))
        if not lastoffer:
            # TODO: at least log a warning
            return None

    def reject_instruction(self, node):
        """
        Assumption: only the last offered instruction can be rejected/accepted
        """
        lastoffer = self.__get_last_session_constituent("<cim:Offer>")
        if not lastoffer:
            # TODO: at least log a warning
            return
        reject = self.__session_part("Reject")
        reject.hasConstituent.add(lastoffer)
        # TODO: check if our code handles this assignment correctly, e.g.,
        # clones the set of the lastoffer.hasPart
        reject.hasPart = lastoffer.hasPart

    def accept_instruction(self, node):
        """
        Assumption: only the last offered instruction can be rejected/accepted
        """
        lastoffer = self.__get_last_session_constituent("<cim:Offer>")
        if not lastoffer:
            # TODO: at least log a warning
            return
        accept = self.__session_part("Accept")
        accept.hasConstituent.add(lastoffer)
        accept.hasPart = lastoffer.hasPart

    def display_instruction(self, node):
        """
        Assumption: only the last offered instruction can be played?
        """
        lastoffer = self.__get_last_session_constituent("<cim:Offer>")
        instruction = self.__session_part("Instruction")
        # TODO: we could play instructions immediately without offer, maybe it
        # would be more convenient to pass the VideoData as argument?
        instruction.hasPart = lastoffer.hasPart

    def request_next_part(self, node, part):
        requestnext = self.__session_part("RequestNext")
        instruction = self.__get_last_session_constituent("<cim:Instruction>")
        requestnext.hasConstituent(instruction)
        # Again: We could get the last part from the DB and automatically
        # determine the next part, but i for now assume it's an argument
        instruction.hasPart.add(part)
        # As i designed this, there will be no new 'Instruction' for the parts

    def request_previous_part(self, node, part):
        requestback = self.__session_part("RequestBack")
        instruction = self.__get_last_session_constituent("<cim:Instruction>")
        requestback.hasConstituent(instruction)
        # Again: We could get the last part from the DB and automatically
        # determine the previous part, but i for now assume it's an argument
        instruction.hasPart.add(part)

    def dimensions_checked(self, node):
        self.__session_part("CheckedDimensions")

    def poses_generated(self, node):
        self.__session_part("PosesGenerated")
