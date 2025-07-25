"""
This module implemements a lightweight reasoner/planner.

It evaluates the conditions of actions, both of which are stored in a RDF
representation in an external RDF/OWL DB/reasoner.
"""

from hfc_thrift.rdfproxy import RdfProxy


AtomicCondition = None

BasicCondition = None
AskQueryCondition = None
AllQueryCondition = None
SomeQueryCondition = None

NegationCondition = None
ConjunctionCondition = None
DisjunctionCondition = None

Action = None


# RdfProxy must have been initialized prior to everything else
def init_proxy(port=7070, ns='cim:',
               classmapping={"<plan:Action>": "Action"}):
    """Initialize the link to the external RDF/OWL reasoner.

    This method must be called prior to creating the first reasoner object
    """
    RdfProxy.init_rdfproxy(port=port, ns=ns, classmapping=classmapping)


def init_classes():
    """
    Initialize global classes for actions and conditions.

    The values of these global variables are proxies of RDF classes.
    Common functionality is added for easy evaluation and use in the code.
    """
    global AtomicCondition, BasicCondition, AskQueryCondition, AllQueryCondition
    global SomeQueryCondition, NegationCondition, ConjunctionCondition, DisjunctionCondition
    global Action

    AtomicCondition = RdfProxy.getClass('<plan:AtomicCondition>')

    BasicCondition = RdfProxy.getClass('<plan:BasicCondition>')
    AskQueryCondition = RdfProxy.getClass('<plan:AskQueryCondition>')
    AllQueryCondition = RdfProxy.getClass('<plan:AllQueryCondition>')
    SomeQueryCondition = RdfProxy.getClass('<plan:SomeQueryCondition>')

    NegationCondition = RdfProxy.getClass('<plan:Negation>')
    ConjunctionCondition = RdfProxy.getClass('<plan:Conjunction>')
    DisjunctionCondition = RdfProxy.getClass('<plan:Disjunction>')

    Action = RdfProxy.getClass('<plan:Action>')

    def basic_eval(self, globals):
        """Evaluate a basic (python code) condition."""
        # print(self.basicCondition)
        val = False
        try:
            val = eval(self.basicCondition, globals)
        except Exception as ex:
            print(f"ERROR: {ex}")
            return False
        return val
    BasicCondition.eval = basic_eval

    def askq_eval(self):
        """Evaluate a ask query condition."""
        res = RdfProxy.selectQuery(self.rdlQuery)
        return len(res) > 0
    AskQueryCondition.eval = askq_eval

    def allq_eval(self):
        """
        Evaluate if all results of a query must fullfil a predicate.

        Use this if you want to check one conforming or zero.
        """
        res = RdfProxy.selectQuery(self.rdlQuery)
        predicate = eval(self.predicate)  # TODO: CAN THIS BE A "CONDITION" ??
        return all(predicate(x) for x in res)
    AllQueryCondition.eval = allq_eval

    def someq_eval(self):
        """
        Evaluate if at least result of a query fullfils a predicate.

        At least one must fulfill the condition.
        """
        res = RdfProxy.selectQuery(self.rdlQuery)
        predicate = eval(self.predicate)  # TODO: CAN THIS BE A "CONDITION" ??
        return any(predicate(x) for x in res)
    SomeQueryCondition.eval = someq_eval


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
        if AtomicCondition is None:
            init_classes()
        self.actions = RdfProxy.selectQuery(
            'select ?a where ?a <rdf:type> <plan:Action> ?_ ')
            # & ?a <plan:name> "confirm_pack_fastened" ?_') #debugging
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
        if ConjunctionCondition.superclass_of(cond) or \
           DisjunctionCondition.superclass_of(cond):
            for sub in cond.conditions:
                self._collect_atomics(sub, action)
        elif NegationCondition.superclass_of(cond):
            self._collect_atomics(cond.condition, action)
        elif AtomicCondition.superclass_of(cond):
            if cond in self._atomic2action:
                self._atomic2action[cond].append(action)
            else:
                self._atomic2action[cond] = [action]

    def _eval_condition(self, cond, violated, bindings, neg=False):
        val = False
        if ConjunctionCondition.superclass_of(cond):
            val = True
            for sub in cond.conditions:
                sval = self._eval_condition(sub, violated, bindings)
                val = val and sval
        elif DisjunctionCondition.superclass_of(cond):
            for sub in cond.conditions:
                sval = self._eval_condition(sub, violated, bindings)
                val = val or sval
        elif NegationCondition.superclass_of(cond):
            # cond.condition is always an atomic condition, the converter
            # guarantees that
            sval = self._eval_condition(cond.condition, violated, bindings, neg=True)
            if sval:
                violated.append(cond)
            val = not sval
        elif AtomicCondition.superclass_of(cond):
            # avoid re-evaluation
            val = self._atomic_results[cond]
            if not val and not neg:
                violated.append(cond)
        return val

    def _create_explanation(self, violated):
        reason = ''
        # TODO: FIX THE OUTPUT FOR ATOMICS (NEGATION)
        for cond in violated:
            basereason = ''
            neg = ''
            if AtomicCondition.superclass_of(cond):
                basereason = cond.description
                neg = 'not '
            else:
                basereason = cond.condition.description
            basereason = basereason.format(neg=neg)
            if reason:
                reason += ' and ' + basereason
            else:
                reason = basereason
        return reason

    def _evaluate_condition(self, condition, bindings):
        violated = []
        val = self._eval_condition(condition, violated, bindings)
        reason = "" if val else self._create_explanation(violated)
        return val, violated, reason

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
                    val = (new_value, violated, reason) = \
                        self._evaluate_condition(action.condition, bindings)
                    changed_actions[action] = val
                    self._action_results[action] = val

        self._last_atomic_results = self._atomic_results
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

    def check_postcondition(self, action, bindings):
        """Check the postcondition of an action, if any."""
        if action.postCondition == RdfProxy.UNBOUND:
            return True, None, None
        return self._evaluate_condition(action.postCondition, bindings)


if __name__ == "__main__":
    init_proxy()
