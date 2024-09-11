import os
import unittest
import subprocess
import time
import numpy as np

from hfc_thrift.rdfproxy import RdfProxy
from numpy.ma.testutils import assert_equal

from rdf_store import RdfStore


class MyTestCase(unittest.TestCase):
    HFC_JAR=os.environ["HOME"]+'/src/java/hfc-thrift/target/hfc-server.jar'
    @classmethod
    def setUpClass(cls):
        """ Start external hfc instance """
        cls.proc = subprocess.Popen(
            ["java", '-jar', cls.HFC_JAR, '-p', '7070',
            "../src/main/resources/ontology/fluently.yml"],
             shell=False, stdout=subprocess.PIPE, encoding='utf-8')
        for line in iter(cls.proc.stdout.readline, ''):
            #print(line)
            if 'Starting the simple server' in line:
                print("HFC server started successfully")
                break

    @classmethod
    def tearDownClass(cls):
        """ stop external hfc instance"""
        RdfProxy.shutdown_server()
        cls.proc.wait()

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
        the_scan = RdfProxy.rdf2pyobj(scan.uri)
        self.assertEqual(the_scan.hasHorizontalResolution, 7)
        self.assertEqual(the_scan.hasVerticalResolution, 5)

    def test_instructions(self):
        rdf_store = RdfStore()
        johndoe = rdf_store.get_user(None, "John", "Doe")
        session = rdf_store.start_session(None)
        offer = rdf_store.offer_instruction(None, "intro")
        self.assertIsNotNone(offer)
        decline = rdf_store.decline_instruction(None)
        self.assertIsNotNone(decline)
        self.assertTrue(offer in decline.hasConstituent)
        accept = rdf_store.accept_instruction(None)
        self.assertIsNotNone(accept)
        self.assertTrue(offer in accept.hasConstituent)

    def test_add_pose_offers(self):
        rdf_store = RdfStore()
        johndoe = rdf_store.get_user(None, "John", "Doe")
        session = rdf_store.start_session(None)
        request = rdf_store.addpose_requested(None)
        self.assertIsNotNone(request)
        accept = rdf_store.addpose_accepted(None)
        self.assertIsNotNone(accept)
        decline = rdf_store.addpose_declined(None)
        self.assertIsNotNone(decline)

    def test_add_pose(self):
        rdf_store = RdfStore()
        johndoe = rdf_store.get_user(None, "John", "Doe")
        session = rdf_store.start_session(None)
        scan = rdf_store.start_scan(None)
        # TODO: get rid of the warning when creating the matrix
        pose1 = np.matrix([[1,2,3,4],[1,2,3,4],[1,2,3,4],[1,2,3,4]]
                         , dtype=float)
        quat1 = rdf_store.add_pose(None, pose1)
        pose_2 = np.matrix('-0.56333682 0 0.82622734 -0.22; 0 1 0 0; '
                           '-0.82622734 0 -0.56333682 0.15; 0 0 0 1')
        quat2 = rdf_store.add_pose(None, pose_2)
        assert_equal(len(scan.hasManualPoses), 2)
        assert(quat1 in scan.hasManualPoses)
        assert(quat2 in scan.hasManualPoses)

    def test_start_end_scan(self):
        rdf_store = RdfStore()
        johndoe = rdf_store.get_user(None, "John", "Doe")
        session = rdf_store.start_session(None)
        scan = rdf_store.start_scan(None)
        rdf_store.robot_starts_scanning(None)
        time.sleep(0.5)
        rdf_store.robot_ends_scanning(None)
        assert(scan.toTime - scan.fromTime > 500 and
               scan.toTime - scan.fromTime < 1000)

    def test_record_scan_result(self):
        rdf_store = RdfStore()
        johndoe = rdf_store.get_user(None, "John", "Doe")
        session = rdf_store.start_session(None)
        scan = rdf_store.start_scan(None)
        rdf_store.record_scan_test_quality(None, 0.95)
        assert_equal(scan.scanQuality, 0.95)
        rdf_store.record_scan_test_result(None,"accepted")
        assert_equal(scan.wasSuccessful, "accepted")

if __name__ == '__main__':
    unittest.main()
