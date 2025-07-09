from hfc_thrift.rdfproxy import RdfProxy

RdfProxy.init_rdfproxy(port=7070, ns='cim:', classmapping={"<plan:Action>":"Action"})
RdfProxy.UNDEFINED_SLOTS_ARE_ERRORS = False

from reasoner import ActionClass

actions = RdfProxy.selectQuery("select ?a where ?a <rdf:type> <plan:Action> ?_")

class Battery:
    def __getattr__(self, slot):
        return None

battery = RdfProxy.getProxy("<cim:Square>")
cover = RdfProxy.getObject("Entity")
tool = RdfProxy.getObject("Entity")

for action in actions:
    val, violated = action.executable(globals())
    print(action.uri + " is " + str(val), end='')
    for v in violated:
        print(" " + v.description, end='')
    print()
