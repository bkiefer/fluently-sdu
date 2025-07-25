import os
import subprocess
import sys
import time
import unittest
from typing import cast
import logging
from hfc_thrift import rdfproxy
from hfc_thrift.rdfproxy import RdfProxy
from reasoner import Reasoner, init_proxy
from pathlib import Path

logging.basicConfig(
    format="%(asctime)s: %(levelname)s: %(message)s",
    level=logging.INFO,
    force=True)
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

# self.assertTrue(isinstance(clazz, type))
# self.assertIs(clazz1, clazz2)
# with self.assertRaisesRegex(ValueError,
#                             "unsupported type <class 'NoneType'> of None"):
#     RdfProxy.python2rdf(None)
# self.assertFalse(sub.superclass_of(sup))
# self.assertRaises(ValueError, xsdutils.splitOwlUri, 'no-uri')

# fake data
from battery_pack_module import PackState
from robot_module import RobotModule
class App:
    pack_state = None

app = App()
app.pack_state = PackState()
app.robot_module = RobotModule('foo', None, None,
                               active_gripper="small", verbose=True)

NR_ATOMICS = 16
NR_ACTIONS = 21

class RdfProxyTestCase(unittest.TestCase):
    proc: subprocess.Popen
    hfc_dir = Path('~/src/java/hfc-thrift/').expanduser()
    onto_dir = Path('~/src/java/fluently-sdu/src/main/resources/ontology/').expanduser()

    @classmethod
    def setUpClass(cls) -> None:
        port = 7979
        if sys.platform.startswith('linux'):
            # Linux specific procedures

            # start hfc server process
            cls.proc = subprocess.Popen(
                ["/usr/bin/java",
                 "-Dlogback.configurationFile=./logback.xml",
                 "-jar", str(cls.hfc_dir.joinpath("target/hfc-server.jar")),
                 "-p", str(port), str(cls.onto_dir.joinpath("fluently.yml"))],
                encoding="UTF-8",
                stdout=subprocess.PIPE)
            for line in (cls.proc.stdout or []):
                if "Starting" in line:
                    logger.info(f"HFC Server started successfully on port {port}")
                    time.sleep(0.5)
                    break

        else:
            logger.warning('Make sure HFC server is running on port 7979 using'
                           ' fluently.yml configuration')

        try:
            # don't use default port: PAL hfc service uses it.
            init_proxy(port=port)
        except Exception as ex:
            logger.error(f"Could not initialize rdfproxy: {ex}")
            if sys.platform.startswith('linux'):
                # stop hfc server process, if running
                cls.proc.terminate()

    @classmethod
    def tearDownClass(cls) -> None:
        if sys.platform.startswith('linux'):
            try:
                RdfProxy.shutdown_server()
            finally:
                # wait for hfc server process to end
                cls.proc.wait()

    def setUp(self):
        if not sys.platform.startswith('linux'):
            rdfproxy.hfc.init("src/FluentlyOntology/fluently.yml")


    def test_reasoner_basics(self):
        # init_rdfproxy is called in test class setup, verify its effects here
        r = Reasoner()
        self.assertEqual(len(r.actions), NR_ACTIONS)
        self.assertEqual(len(r._atomic2action), NR_ATOMICS)
        name = "confirm_quals"
        action = r.get_action(name)
        self.assertEqual(name, action.name)

    def test_evaluate_actions(self):
        # init_rdfproxy is called in test class setup, verify its effects here
        r = Reasoner()
        changed = r.evaluate_actions(globals())
        # first run, all changed
        self.assertEqual(len(changed), NR_ACTIONS)
        name = "choose_diff_pack_model"
        act = r.get_action(name)
        self.assertTrue(act in changed)
        self.assertEqual(changed[act][2], "Pack is not fastened")

        # second run with first change
        name = "confirm_pack_fastened"
        act = r.get_action(name)
        self.assertTrue(act in changed)
        vals = changed[act]
        self.assertTrue(vals[0], "")
        self.assertEqual(vals[2], "")

        app.pack_state.fastened = True
        changed = r.evaluate_actions(globals())
        self.assertEqual(len(changed), 6)
        self.assertTrue(act in changed)
        self.assertEqual(changed[act][2], "Pack is fastened")
        self.assertTrue(r.check_postcondition(act, globals())[0])

        # third run with second change
        app.pack_state.model_confirmed = True
        changed = r.evaluate_actions(globals())
        self.assertEqual(len(changed), 2)
        name = "choose_diff_pack_model"
        act = r.get_action(name)
        self.assertTrue(act in changed)
        self.assertEqual(changed[act][2], "Pack model is confirmed")

    def test_negated_precondition(self):
        r = Reasoner()
        changed = r.evaluate_actions(globals())
        self.assertEqual(app.robot_module.active_gripper, 'small')
        name = 'equip_small_tool'
        act = r.get_action(name)
        self.assertFalse(r.action_is_executable(act)[0])

    def test_unbound_postcondition(self):
        r = Reasoner()
        changed = r.evaluate_actions(globals())
        name = 'classify_pack'
        act = r.get_action(name)
        self.assertTrue(r.check_postcondition(act, globals())[0])
        self.assertIsNone(r.check_postcondition(act, globals())[2])


if __name__ == '__main__':
    unittest.main()
