"""
This module implemements a lightweight reasoner/planner.

It evaluates the conditions of actions, both of which are stored in a RDF
representation in an external RDF/OWL DB/reasoner.
"""

from hfc_thrift.rdfproxy import RdfProxy


AtomicClass = None

BasicClass = None
AskQueryClass = None
AllQueryClass = None
SomeQueryClass = None

NegationClass = None
ConjunctionClass = None
DisjunctionClass = None

ActionClass = None

# RdfProxy must have been initialized
def init_proxy(port=7070, ns='cim:',
               classmapping={"<plan:Action>": "Action"}):
    """Initialize the link to the external RDF/OWL reasoner."""
    RdfProxy.init_rdfproxy(port=port, ns=ns, classmapping=classmapping)


def init_classes():
    """
    Initialize global classes for actions and conditions.

    The values of these global variables are proxies of RDF classes.
    Common functionality is added for easy evaluation and use in the code.
    """
    global AtomicClass, BasicClass, AskQueryClass, AllQueryClass
    global SomeQueryClass, NegationClass, ConjunctionClass, DisjunctionClass
    global ActionClass

    AtomicClass = RdfProxy.getClass('<plan:AtomicCondition>')

    BasicClass = RdfProxy.getClass('<plan:BasicCondition>')
    AskQueryClass = RdfProxy.getClass('<plan:AskQueryCondition>')
    AllQueryClass = RdfProxy.getClass('<plan:AllQueryCondition>')
    SomeQueryClass = RdfProxy.getClass('<plan:SomeQueryCondition>')

    NegationClass = RdfProxy.getClass('<plan:Negation>')
    ConjunctionClass = RdfProxy.getClass('<plan:Conjunction>')
    DisjunctionClass = RdfProxy.getClass('<plan:Disjunction>')

    ActionClass = RdfProxy.getClass('<plan:Action>')

    def basic_eval(self, globals):
        # print(self.basicCondition)
        val = False
        try:
            val = eval(self.basicCondition, globals)
        except Exception as ex:
            print(f"ERROR: {ex}")
            return False
        return val
    BasicClass.eval = basic_eval

    def askq_eval(self):
        res = RdfProxy.selectQuery(self.rdlQuery)
        return len(res) > 0
    AskQueryClass.eval = askq_eval

    #
    def allq_eval(self):
        """Use this if you want to check one conforming or zero."""
        res = RdfProxy.selectQuery(self.rdlQuery)
        predicate = eval(self.predicate)  # TODO: CAN THIS BE A "CONDITION" ??
        return all(predicate(x) for x in res)
    AllQueryClass.eval = allq_eval

    #
    def someq_eval(self):
        """At least one must fulfill the condition."""
        res = RdfProxy.selectQuery(self.rdlQuery)
        predicate = eval(self.predicate)  # TODO: CAN THIS BE A "CONDITION" ??
        return any(predicate(x) for x in res)
    SomeQueryClass.eval = someq_eval


class Reasoner(object):
    """A lightweight reasoner, able to give explanations of failing conditions.

    It pulls all actions from an RDF database and offers evaluation of their
    preconditions. If the precondition for an action is not fulfilled, the list
    of literals responsible for this is computed, and an "explanation", based
    on this, is generated.
    """

    def __init__(self):
        """Create a new Reasoner object.

        Before creating a reasoner, it's important that the connection to
        the database has been established calling init_proxy() first.
        If necessary, the global class variables will be initialized.
        """
        if AtomicClass is None:
            init_classes()
        self.actions = RdfProxy.selectQuery(
            "select ?a where ?a <rdf:type> <plan:Action> ?_")
        # a mapping from action names to action objects
        self._name2action = {}
        # This maps atomic conditions to actions, to reduce evaluation cost
        self._atomic2action = {}
        for action in self.actions:
            self._name2action[action.name] = action
            self._collect_atomics(action.condition, action)
        # This caches the values of the evaluation of action conditions
        # the value is a tuple (bool, list(violations))
        self._action_results = {}
        # This caches the values of the last run of atomic conditions
        self._last_atomic_results = {}
        # current values of evaluation of atomic conditions
        self._atomic_results = {}

    def _collect_atomics(self, cond, action):
        """
        Create a mapping from atomic conditions to dependant actions.

        That an action is depending on a condition is determined
        by recursively going through the complex conditions in the action,
        if any
        """
        #print(cond)
        if ConjunctionClass.superclass_of(cond) or \
           DisjunctionClass.superclass_of(cond):
            for sub in cond.conditions:
                self._collect_atomics(sub, action)
        elif NegationClass.superclass_of(cond):
            self._collect_atomics(cond.condition, action)
        elif AtomicClass.superclass_of(cond):
            if cond in self._atomic2action:
                self._atomic2action[cond].append(action)
            else:
                self._atomic2action[cond] = [action]

    def _eval_condition(self, cond, violated, bindings):
        val = False
        if ConjunctionClass.superclass_of(cond):
            val = True
            for sub in cond.conditions:
                sval = self._eval_condition(sub, violated, bindings)
                val = val and sval
        elif DisjunctionClass.superclass_of(cond):
            for sub in cond.conditions:
                sval = self._eval_condition(sub, violated, bindings)
                val = val or sval
        elif NegationClass.superclass_of(cond):
            sval = self._eval_condition(cond.condition, violated, bindings)
            val = not sval
        elif AtomicClass.superclass_of(cond):
            # avoid re-evaluation
            val = self._atomic_results[cond]
            if not val:
                # print(cond.description)
                violated.append(cond)
        return val

    def _evaluate_action(self, action, bindings):
        violated = []
        val = self._eval_condition(action.condition, violated, bindings)
        return val, violated

    def evaluate_actions(self, bindings, delta=True):
        """
        Evaluate the executability of actions.

        This will return a dict of actions and their evaluations which have
        changed from the last evaluation to the current one, if delta is True,
        all actions with evaluations otherwise.

        An evaluation consists of a boolean value and a list of violated
        atomic conditions.
        """
        # first evaluate all atomic conditions
        self._atomic_results = {}
        for atomic in self._atomic2action.keys():
            self._atomic_results[atomic] = atomic.eval(bindings)

        # compare the values to the last run (if available)
        last_atomic_values = self._last_atomic_results if delta else {}
        changed_actions = {}
        # all atomics
        for atomic in self._atomic2action.keys():
            if atomic not in last_atomic_values or \
                    last_atomic_values[atomic] != self._atomic_results[atomic]:
                for action in self._atomic2action[atomic]:
                    new_value = self._evaluate_action(action, bindings)
                    changed_actions[action] = new_value
                    self._action_results[action] = new_value

        self._last_atomic_results = self._atomic_results
        #print(self._action_results)
        return changed_actions

    def get_action(self, action_name):
        """Return the action with that name."""
        return self._name2action[action_name]

    def action_is_executable(self, action):
        """
        Return the executability of an action.

        Given the action name, get its executability and the violated
        atomic conditions for that action
        """
        return self._action_results[action]

if __name__ == "__main__":
    init_proxy()
