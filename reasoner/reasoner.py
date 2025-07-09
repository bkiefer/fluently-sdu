from hfc_thrift.rdfproxy import RdfProxy

# RdfProxy must have been initialized in the main module

AtomicClass = RdfProxy.getClass('<plan:AtomicCondition>')

BasicClass = RdfProxy.getClass('<plan:BasicCondition>')
AskQueryClass = RdfProxy.getClass('<plan:AskQueryCondition>')
AllQueryClass = RdfProxy.getClass('<plan:AllQueryCondition>')
SomeQueryClass = RdfProxy.getClass('<plan:SomeQueryCondition>')

NegationClass = RdfProxy.getClass('<plan:Negation>')
ConjunctionClass = RdfProxy.getClass('<plan:Conjunction>')
DisjunctionClass  = RdfProxy.getClass('<plan:Disjunction>')

ActionClass = RdfProxy.getClass('<plan:Action>')


def basic_eval(self, globals):
    print(self.basicCondition)
    return eval(self.basicCondition, globals)
BasicClass.eval = basic_eval

def askq_eval(self):
    res = RdfProxy.selectQuery(self.rdlQuery)
    return len(res) > 0
AskQueryClass.eval = askq_eval

#
def allq_eval(self):
    """Use this if you want to check one conforming or zero"""
    res = RdfProxy.selectQuery(self.rdlQuery)
    predicate = eval(self.predicate) # TODO: CAN THIS BE A "CONDITION" ??
    return all(predicate(x) for x in res)
AllQueryClass.eval = allq_eval

#
def someq_eval(self):
    """at least one must fulfill the condition"""
    res = RdfProxy.selectQuery(self.rdlQuery)
    predicate = eval(self.predicate) # TODO: CAN THIS BE A "CONDITION" ??
    return any(predicate(x) for x in res)
SomeQueryClass.eval = someq_eval

def eval_condition(cond, violated, globals):
    val = False
    if ConjunctionClass.superclass_of(cond):
        val = True
        for sub in cond.conditions:
            sval = eval_condition(sub, violated, globals)
            val = val and sval
    elif DisjunctionClass.superclass_of(cond):
        for sub in cond.conditions:
            sval = eval_condition(sub, violated, globals)
            val = val or sval
    elif AtomicClass.superclass_of(cond):
        val = cond.eval(globals)
        if not val:
            print(cond.description)
            violated.append(cond)
    return val

def actionExecutable(self, globals):
    cond = self.condition
    print(cond.uri)
    violated = []
    val = eval_condition(cond, violated, globals)
    return val, violated
ActionClass.executable = actionExecutable
