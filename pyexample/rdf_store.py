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
        self.user = None
        self.session = None
        self.scan = None

    def get_user(self, node, first_name: str, last_name: str):
        users = RdfProxy.selectQuery(
            'select ?uri where ?uri <rdf:type> <cim:User> ?_ '
            '& ?uri <soho:hasName> "{}" ?_ '
            '& ?uri <soho:hasSurname> "{}" ?_'.format(first_name, last_name))
        if not users:
            self.user = RdfProxy.getObject("User")
            self.user.hasName = first_name
            self.user.hasSurname = last_name
        else:
            self.user = users[0]
        return self.user

    def start_session(self, node):
        if self.session:
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
        self.scan.hasHorizontalResolution = DEFAULT_H_RESOLUTION
        self.scan.hasVerticalResolution = DEFAULT_V_RESOLUTION
        return self.scan

    # For all the Offer situations, i think we should have a fixed Instance
    # which is a placeholder for what we offer, or should we create an Event
    # instance which then may never happen since it is declined?
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

    def decline_instruction(self, node):
        """
        Assumption: only the last offered instruction can be declined/accepted
        """
        lastoffer = self.__get_last_session_constituent("<cim:Offer>")
        if not lastoffer:
            # TODO: at least log a warning
            return
        decline = self.__session_part("Decline")
        decline.hasConstituent.add(lastoffer)
        # TODO: check if our code handles this assignment correctly, e.g.,
        # clones the set of the lastoffer.hasPart
        decline.hasPart = lastoffer.hasPart

    def accept_instruction(self, node):
        """
        Assumption: only the last offered instruction can be declined/accepted
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
        """record system has checked dimension"""
        self.__session_part("CheckedDimensions")

    def poses_generated(self, node):
        """record system has generated poses"""
        self.__session_part("PosesGenerated")

    def resolution_accept_requested(self, node):
        """record system "offers" user to change resolution"""
        self.__session_part("YNQuestionResolution")

    def resolution_accepted(self, node):
        """record system "offers" user to change resolution"""
        self.__session_part("AcceptResolution")

    def addpose_requested(self, node):
        """record system "offers" user to change addpose"""
        self.__session_part("YNQuestionAddpose")

    def addpose_accepted(self, node):
        """record system "offers" user to change addpose"""
        self.__session_part("AcceptAddpose")

    def add_pose(self, node, quaternion: np.matrix):
        pose = RdfProxy.getObject("Quaternion")
        # i would propose to have an invertible string representation here
        pose.representation = str(quaternion)
        # we assume he have an active scan object, which is the last one in the
        # session
        scan = self.__get_last_session_constituent("<cim:ScanningProcess>")
        scan.hasManualPoses.add(pose)

    def record_scan_test_result(self, node, result: float):
        """
        indicates if the scan succeeded (result >0.8?), was 'incomplete'
        (0.5 < result < 0.8) or failed  (result < 0.5)

        Maybe we can use an enum, or strings instead and change the range
        of wasSuccessful
        """
        scan = self.__get_last_session_constituent("<cim:ScanningProcess>")
        scan.wasSuccessful = result
