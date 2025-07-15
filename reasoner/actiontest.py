from hfc_thrift.rdfproxy import RdfProxy

RdfProxy.init_rdfproxy(port=7070, ns='cim:', classmapping={"<plan:Action>":"Action"})
RdfProxy.UNDEFINED_SLOTS_ARE_ERRORS = False

from reasoner import Reasoner

actions = RdfProxy.selectQuery("select ?a where ?a <rdf:type> <plan:Action> ?_")

class Battery:
    def __getattr__(self, slot):
        return None

battery = RdfProxy.getProxy("<cim:Square>")
cover = RdfProxy.getObject("Entity")
tool = RdfProxy.getObject("Entity")

r = Reasoner()
changed_actions = r.evaluate_actions(globals())
