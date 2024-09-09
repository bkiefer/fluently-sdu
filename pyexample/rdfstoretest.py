import os
import unittest
import subprocess
import time

from hfc_thrift.rdfproxy import RdfProxy
from rdf_store import RdfStore


class MyTestCase(unittest.TestCase):
    HFC_JAR=os.environ["HOME"]+'/src/java/hfc-thrift/target/hfc-server.jar'
    @classmethod
    def setUpClass(cls):

        """ Start external hfc instance """
        cls.proc = subprocess.Popen(
            ["java", '-jar', cls.HFC_JAR, '-p7070',
            "../src/main/resources/ontology/fluently.yml"],
             shell=False)
        time.sleep(1)
        #cls.proc = subprocess.Popen(["pwd"], shell=True)
        #cls.proc.communicate()

    @classmethod
    def tearDownClass(cls):
        """ stop external hfc instance"""
        cls.proc.kill()

    def test_getuser(self):
        rdf_store = RdfStore()
        johndoe = rdf_store.get_user(None, "John", "Doe")
        self.assertIsNotNone(johndoe)
        johndoe2 = rdf_store.get_user(None, "John", "Doe")
        self.assertEqual(johndoe, johndoe2)

    def test_session(self):
        rdf_store = RdfStore()
        johndoe = rdf_store.get_user(None, "John", "Doe")
        session = rdf_store.start_session(None)
        self.assertIsNotNone(session)
        self.assertEqual(johndoe, session.user)
        self.assertEqual(rdf_store.session, session)
        rdf_store.end_session(None)
        self.assertIsNone(rdf_store.session)

    def test_start_scan(self):
        rdf_store = RdfStore()
        johndoe = rdf_store.get_user(None, "John", "Doe")
        session = rdf_store.start_session(None)
        scan = rdf_store.start_scan(None)
        self.assertIsNotNone(scan)
        scan.hasHorizontalResolution = 7
        scan.hasVerticalResolution = 5
        theScan = RdfProxy.rdf2pyobj(scan.uri)
        self.assertEqual(theScan.hasHorizontalResolution, 7)
        self.assertEqual(theScan.hasVerticalResolution, 5)

    def test_instructions(self):
        rdf_store = RdfStore()
        johndoe = rdf_store.get_user(None, "John", "Doe")
        session = rdf_store.start_session(None)
        offer = rdf_store.offer_instruction(None, "intro")
        self.assertIsNotNone(offer)
        decline = rdf_store.decline_instruction(None)
        self.assertIsNotNone(decline)
        self.assertTrue(offer in decline.hasConstituent)


if __name__ == '__main__':
    unittest.main()
