from hfc_thrift.rdfproxy import RdfProxy

RdfProxy.init_rdfproxy(port=7070)

robot = RdfProxy.rdf2pyobj('<cim:robot1>')

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

def execute(robot, action):
    """stub that should do the appropriate action on the robot and return success"""
    return True

scanSuccess = True
while not scanSuccess:
    scan = RdfProxy.getObject("ScanningProcess")
    session.has_constituent.add(scan)
    scan.hasVerticalResolution = 3
    scan.hasHorizontalResolution = 3
    # robot.speak(user, 'Question(SetupOK)')
    # response = waitForResponse()
    # if response <= 'Confirm()'
    scanSuccess = execute(robot, scan)
    scan.wasSuccessful = scanSuccess


