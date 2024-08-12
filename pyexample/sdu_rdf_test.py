import sys
import os
import numpy as np

sys.path.append(os.path.expanduser("~") + "/hfc-thrift/src/main/python/src")
try:
    from hfc_thrift.rdfproxy import RdfProxy
    RdfProxy.init_rdfproxy(port=7070)
    
except Exception as e:
    print(f"Connection error: {e}")
    sys.exit()

robot = RdfProxy.getObject("Cobot")

impeller = RdfProxy.getObject("ProductionObject")

users = RdfProxy.selectQuery('select ?uri where ?uri <rdf:type> <cim:User> ?_ '
                             '& ?uri <soho:hasName> "John" ?_ '
                             '& ?uri <soho:hasSurname> "Doe" ?_')

if not users:
    user = RdfProxy.getObject("User")
    user.hasName = "John"
    user.hasSurname ="Doe"
else:
    user = users[0]

session = RdfProxy.getObject("UserSession")
user.userSessions.add(session)
scan = RdfProxy.getObject("ScanningProcess") 

def skip_instruction_test(instruction_type):
    """
    System offers the user instructions
    
    Args:
        instruction_type (str): the type of instruction (introduction, resolution, manual, or quality)
    Returns:
        bool: True if user wants to skip instructions, False otherwise 
    """
    # record system offers instructions
    # record user accepts instructions
    
    return False # behavior tree node

def instruction_test(instruction_type):
    """
    System generates and displays instructions to user

    Args:
        instruction_type (str): the type of instruction (introduction, resolution, manual, or quality)

    Returns:
        bool: True when instructions have been read
    """

    # record system displays instruction
    # record user clicks "next"
    # record user clicks "back"
    # record user clicks "next" again
    # record user clicks "next" again (that was the final slide)
    
    return True 

def action_trigger_test(action):
    """
    Simple action trigger. Orders the system to complete an action. Returns the status of the action.
    
    Args:
        action (str): the name of the action node

    Returns:
        bool: True if action succeeds, False if it fails.
    """
    if action == "check_dimension":
        # record system has checked dimension
        return True

    elif action == "generate_poses":
        # record system has generated poses
        return True

    elif action == "resolution_ok":
        # record system "offers" user to change resolution
        # record user accepts to change resolution
        return False
    
    elif action == "scan_plan_ok":
        # record system "offers" user to add manual pose
        # record user accepts to add manual pose
        return False
    
    elif action == "change_resolution":
        # record we are in "change resolution" mode

        # record new horizontal resolution
        scan.hasVerticalResolution = 3

        # record new vertical resolution
        scan.hasHorizontalResolution = 3  

        return True
    
    elif action == "add_pose":
        # record we are in "add manual pose" mode

        # record 1st 6D pose (4x4 homogeneous transformation matrix)
        poseA = RdfProxy.getObject("6DPose")
        #poseA.hasPositionData(np.matrix([[-1, 0, 0, 0],[0, 1, 0, 0],[0, 0, -1, 0.37],[0, 0, 0, 1]]))
        #scan.hasManualPoses.add(poseA)
        
        # record 2nd pose
        poseB = RdfProxy.getObject("6DPose")
        #poseB.hasPositionData(np.matrix([[-0.56, 0, 0.83, -0.22 ],[0, 1, 0, 0],[-0.83, 0, -0.56, 0.15],[0, 0, 0, 1]]))
        #scan.hasManualPoses.add(poseB)
        
        return True 
    
    elif action == "start_scan":
        # record robot scans object

        # add new scan as an instance to the session
        session.hasPart.add(scan)

        return True

    else:
        return False
    
def scan_ok_test():
    """
    Returns:
        bool: True if the user accepts the scan
    """
    # record robot offers/asks about scan quality
    # record user rejects scan

    scan.wasSuccessful = False
    
    return False

def scan_failed_test():
    """
    Returns:
        bool: True if the user rejects the scan
    """

    # no nothing (user choice already recorded)
    return True

def scan_incomplete_test():
    """
    Returns:
        bool: True if the user wants to modify the scan
    """

    # no nothing (user choice already recorded)
    return False


# Fake behavior tree (we just call the functions in a sequence)
skip_instruction_test(instruction_type="introduction")
instruction_test(instruction_type="introduction")
actions = ["check_dimension","generate_poses","resolution_ok","scan_plan_ok","change_resolution","add_pose","start_scan"]
for action in actions:
    action_trigger_test(action=action)
scan_ok_test()
scan_failed_test()
scan_incomplete_test()