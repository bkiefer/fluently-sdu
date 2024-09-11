import time

from hfc_thrift.rdfproxy import RdfProxy
import sys
import os
import numpy as np

sys.path.append(os.path.expanduser("~") + "/hfc-thrift/src/main/python/src")

DEFAULT_H_RESOLUTION = 3
DEFAULT_V_RESOLUTION = 3


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
        self.scan = None

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

    def getFileInstance(self, which: str):
        query = 'select ?inst where ?inst <rdf:type> <cim:InstructionSlide> ?_' \
            ' & ?inst <soma:hasNameString> "{}"^^<xsd:string> ?_'.format(which)
        insts = RdfProxy.selectQuery(query)
        return None if not insts else insts[0]


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
        fi = self.getFileInstance(which)
        offer.hasParticipant.add(fi)
        return offer

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
        decline.hasParticipant.union(lastoffer.hasParticipant)
        return decline

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
        accept.hasParticipant.union(lastoffer.hasParticipant)
        return accept

    def display_instruction(self, node):
        """
        Assumption: only the last offered instruction can be played?
        """
        lastoffer = self.__get_last_session_constituent("<cim:Offer>")
        instruction = self.__session_part("Instruction")
        # TODO: we could play instructions immediately without offer, maybe it
        # would be more convenient to pass the VideoData as argument?
        instruction.hasParticipant.union(lastoffer.hasParticipant)
        return instruction

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
        return self.__session_part("CheckedDimensions")

    def poses_generated(self, node):
        """record system has generated poses"""
        return self.__session_part("PosesGenerated")

    def resolution_accept_requested(self, node):
        """record system "offers" user to change resolution"""
        return self.__session_part("YNQuestionResolution")

    def resolution_accepted(self, node):
        """record system "offers" user to change resolution"""
        return self.__session_part("AcceptResolution")

    def resolution_declined(self, node):
        """record system "offers" user to change resolution"""
        return self.__session_part("DeclineResolution")

    def change_resolution(self, node, h_res, v_res):
        self.scan.hasHorizontalResolution = h_res
        self.scan.hasVerticalResolution = v_res
        return self.scan

    def addpose_requested(self, node):
        """record system "offers" user to change addpose"""
        return self.__session_part("YNQuestionAddpose")

    def addpose_accepted(self, node):
        """record system "offers" user to change addpose"""
        return self.__session_part("AcceptAddpose")

    def addpose_declined(self, node):
        """record system "offers" user to change addpose"""
        return self.__session_part("DeclineAddpose")

    def add_pose(self, node, quaternion: np.matrix):
        """a pose is a quaternion, represented by a 4x4 numpy matrix"""
        pose = RdfProxy.getObject("Quaternion")
        # TODO: create an invertible string representation here, and write
        # a get_pose(s) method
        pose.representation = str(quaternion).replace(os.linesep, ' ')
        # we assume he have an active scan object, which is the last one in the
        # session
        self.scan.hasManualPoses.add(pose)
        return self.scan

    def record_scan_test_result(self, node, result: float):
        """
        indicates if the scan succeeded (result >0.8?), was 'incomplete'
        (0.5 < result < 0.8) or failed  (result < 0.5)

        Maybe we can use an enum, or strings instead and change the range
        of wasSuccessful
        """
        self.scan.wasSuccessful = result


    def robot_starts_scanning(self, node):
        now = time.time()
        self.scan.fromTime = round(now * 1000)

    def robot_ends_scanning(self, node):
        now = time.time()
        self.scan.toTime = round(now * 1000)

def update_rdf(node, blackboard, rdf_store: RdfStore):
    if node == "log_in":
        if blackboard.get(node) == "not_requested":
            user = rdf_store.get_user(node=node,first_name=blackboard.get("first_name"),last_name=blackboard.get("last_name"))
            session = rdf_store.start_session(node=node)
            scan = rdf_store.start_scan(node=node)
            print("User: ",user,"\nSession: ",session,"\nScan: ",scan)
            print("h_res: ",scan.hasHorizontalResolution)
            print("v_res", scan.hasVerticalResolution)
            print("Number of user sessions: ",len(user.userSessions))

    elif node in ["skip_intro","skip_reso","skip_manual","skip_quality"]:
        if blackboard.get(node) == "not_requested":
            offer = rdf_store.offer_instruction(node,which=node[4:])
            print("Offer: ", offer)

        elif blackboard.get(node) == "completed":
            accept = rdf_store.accept_instruction(node=node)
            print("Accept: ",accept)

        elif blackboard.get(node) == "failed":
            decline = rdf_store.decline_instruction(node=node)
            print("Decline: ",decline)

    elif node == ["introduction","resolution","manual","quality"]:
        if blackboard.get(node) == "not_requested":
            instruction = rdf_store.display_instruction(node=node)
            print("Instruction: ",instruction)

            # testing clicking "next" and "back", this info will come from sim
            rdf_store.request_next_part
            rdf_store.request_previous_part

    elif node == "check_dimension":
        if blackboard.get(node) == "completed":
            rdf_store.dimensions_checked(node=node)
            pass

    elif node == "generate_poses":
        if blackboard.get(node) == "completed":
            rdf_store.poses_generated(node=node)
            pass

    elif node == "change_resolution":
        if blackboard.get(node) == "completed":
            #h_res = blackboard.get("h_res") # Get this info from sim
            #v_res = blackboard.get("v_res") # Get this info from sim
            h_res = 5
            v_res = 5
            scan = rdf_store.change_resolution(node=node, h_res=h_res, v_res=v_res)
            print("Scan after changing resolution: ", scan)
            print("h_res: ",scan.hasHorizontalResolution)
            print("v_res", scan.hasVerticalResolution)

    elif node == "resolution_ok":
        if blackboard.get(node) == "not_requested":
            rdf_store.resolution_accept_requested(node=node)
            pass

        elif blackboard.get(node) =="completed":
            rdf_store.resolution_accepted(node=node)

        # elif failure
        elif blackboard.get(node) == "failed":
            pass

    elif node == "scan_plan_ok":
        if blackboard.get(node) == "not_requested":
            rdf_store.addpose_requested(node=node)

        elif blackboard.get(node) =="completed":
            rdf_store.addpose_accepted(node=node)

        # elif failure
        elif blackboard.get(node) == "failed":
            # BK: SOMETHING IS MISSING HERE?
            pass

    elif node == "add_pose":
        # GET INFO ABOUT ALL POSES FROM SIM
        q1 = np.matrix('1 0 0 0')
        q2 = np.matrix('1 2 3 4')
        poses = [q1,q2]
        # a pose is a quaternion, represented by a 4x4 numpy matrix
        # BK: are you adding all poses at once? or one by one?
        #for pose in poses:
        #    rdf_store.add_pose(node=node,quaternion=pose)

    elif node == "start_scan":
        # add an RdfStore function for when the robot performs the scanning action
        rdf_store.start_scan(node)
        # BK: is there also a signal when the scan ends?

    elif node == "scan_ok":
        """ This is the judgement of the user """
        if blackboard.get(node) =="completed":
            rdf_store.end_session(node=node)

    elif node == "scan_failed":
        if blackboard.get(node) =="completed":
            rdf_store.end_session(node=node)

    elif node == "scan_incomplete":
        if blackboard.get(node) =="completed":
            rdf_store.end_session(node=node)

    print(node)
