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
class App:
    pack_state = None

app = App()
app.pack_state = PackState()

NR_ATOMICS = 14
NR_ACTIONS = 20

class RdfProxyTestCase(unittest.TestCase):
    proc: subprocess.Popen
    #hfc_dir = Path('~/src/java/hfc-thrift/').expanduser()
    #onto_dir = Path('~/src/java/fluently-sdu/src/main/resources/ontology/').expanduser()
    hfc_dir = Path('~/fluently_ws/hfc-thrift/').expanduser()
    onto_dir = Path('~/fluently_ws/fluently-sdu/src/main/resources/ontology/').expanduser()

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
        self.assertEqual(len(changed), NR_ACTIONS)
        app.pack_state.fastened = True
        changed = r.evaluate_actions(globals())
        self.assertEqual(len(changed), 6)


if __name__ == '__main__':
    unittest.main()
