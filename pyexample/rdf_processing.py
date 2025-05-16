import time
import sys
import os
import numpy as np
import re
import csv
import pandas as pd

sys.path.append(os.path.expanduser("~") + "/hfc-thrift/src/main/python/src")
from hfc_thrift.rdfproxy import RdfProxy

def main(args=None):
    port=7070
    mapclass = { "<cim:Offer>": "Offer",
                    "<cim:Decline>" : "Decline",
                    "<cim:Accept>" : "Accept",
                    "<cim:Question>" : "Question",
                    "<cim:YNQuestion>" : "YNQuestion"}
    RdfProxy.init_rdfproxy(port=port, classmapping=mapclass)

    filename = "test_data.csv"
    fields = ['user_name', 'session_id', 'session_start', 'session_end', 'accept_intro', 'intro_start', 'intro_end', 'accept_reso', 'reso_start', 'reso_end', 'accept_manual', 'manual_start', 'manual_end', 'accept_quality', 'quality_start', 'quality_end', 'scan_id', 'scan_hres', 'scan_vres', 'scan_start', 'scan_end', 'change_res_yn', 'num_of_added_poses', 'num_of_back_requests', 'scan_quality', 'scan_decision'] 
    with open(filename, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)

    # --- Select all distinct user / session pairs --- #
    user_session_pairs = RdfProxy.selectQuery('select distinct ?user ?sess where ?user <rdf:type> <cim:User> ?_ & ?user <cim:userSessions> ?sess ?_')
    i = 1
    j = 1
    for a, b in user_session_pairs:
        k = 1
        user_name = f'{a.hasName} {a.hasSurname}'
        print(user_name)
        session_id = i

        # --- Get start/end time for session --- #
        session_rdf = RdfProxy.python2rdf(b)
        session_start = RdfProxy.selectQuery('select ?t where ?user <cim:userSessions> {} ?t aggregate ?res = LMin ?t'.format(session_rdf))[0] # inside list
        session_end = RdfProxy.selectQuery('select ?t where {} ?_ ?_ ?t  aggregate ?res = LMax ?t'.format(session_rdf))[0] 

        # --- Get all scanning processes within session --- #
        scanning_processes = RdfProxy.selectQuery('select ?c ?t where {} <dul:hasConstituent> ?c ?t & ?c <rdf:type> <cim:ScanningProcess> ?_  aggregate ?res = LGetLatest2 ?c ?t "1"^^<xsd:int>'.format(session_rdf))
        for scan in scanning_processes:
            scan_id = j
            scan_rdf = RdfProxy.python2rdf(scan)

            # --- Change resolution --- #
            hres = RdfProxy.selectQuery('select ?hres where {} <cim:hasHorizontalResolution> ?hres ?t'.format(scan_rdf))
            vres = RdfProxy.selectQuery('select ?vres where {} <cim:hasVerticalResolution> ?vres ?t'.format(scan_rdf))
            scan_hres = hres[-1] # get the latest one
            scan_vres = vres[-1]
            change_resolution = 0
            if len(hres) > 1:
                 change_resolution = 1
            
            # --- Introduction slides --- #
            introduction_offers = RdfProxy.selectQuery('select ?off ?accept where {} <dul:hasConstituent> ?off ?_ '
                                                '& ?off <rdf:type> <cim:Offer> ?_ & ?off <dul:hasParticipant> <cim:Introduction> ?_ '
                                                '& ?accept <rdf:type> <cim:Accept> ?_ & ?accept <dul:hasConstituent> ?off ?_'.format(session_rdf))
            intro_accept = 0
            intro_start = ""
            intro_end = ""
            if len(introduction_offers) > 0:
                 intro_accept = 1
                 
                 intro_start = RdfProxy.selectQuery('select ?t where {} <dul:hasConstituent> ?inst ?t & ?inst <dul:hasParticipant> <cim:Introduction> ?_ '
                                               '& ?inst <rdf:type> <cim:Instruction> ?_ aggregate ?res = LMin ?t'.format(session_rdf))[0]
                 
                # intro_end = RdfProxy.selectQuery('select ?t where {} <dul:hasConstituent> ?checkdim ?t & ?checkdim <rdf:type> <cim:CheckedDimensions> ?_ aggregate ?res = LMin ?t'.format(session_rdf))[0]
                # 
                 intro_end = RdfProxy.selectQuery('select ?t where ?inst <dul:hasPart> ?_ ?t & {} <dul:hasConstituent> ?inst ?_ & ?inst <dul:hasParticipant> <cim:Introduction> ?_ '
                                               '& ?inst <rdf:type> <cim:Instruction> ?_ aggregate ?res = LMax ?t'.format(session_rdf))
                
                 if intro_end:
                    intro_end = intro_end[0]
                 else:
                    intro_end = str(int(intro_start)+10000)
                 
            # --- Resolution slides --- #

            resolution_offers = RdfProxy.selectQuery('select ?off ?accept where {} <dul:hasConstituent> ?off ?_ '
                                                '& ?off <rdf:type> <cim:Offer> ?_ & ?off <dul:hasParticipant> <cim:Resolution> ?_ '
                                                '& ?accept <rdf:type> <cim:Accept> ?_ & ?accept <dul:hasConstituent> ?off ?_'.format(session_rdf))

            reso_accept = 0
            reso_start = ""
            reso_end = ""

            if len(resolution_offers) > 0:
                 reso_accept = 1
                 
                 reso_start = RdfProxy.selectQuery('select ?t where {} <dul:hasConstituent> ?inst ?t & ?inst <dul:hasParticipant> <cim:Resolution> ?_ '
                                               '& ?inst <rdf:type> <cim:Instruction> ?_ aggregate ?res = LMin ?t'.format(session_rdf))[0]
                 
                 reso_end = RdfProxy.selectQuery('select ?t where ?inst <dul:hasPart> ?_ ?t & {} <dul:hasConstituent> ?inst ?_ & ?inst <dul:hasParticipant> <cim:Resolution> ?_ '
                                               '& ?inst <rdf:type> <cim:Instruction> ?_ aggregate ?res = LMax ?t'.format(session_rdf))
                
                 if reso_end:
                    reso_end = reso_end[0]
                 else:
                    reso_end = str(int(reso_start)+10000)

            # --- Manual poses slides --- #

            manual_offers = RdfProxy.selectQuery('select ?off ?accept where {} <dul:hasConstituent> ?off ?_ '
                                                '& ?off <rdf:type> <cim:Offer> ?_ & ?off <dul:hasParticipant> <cim:Manual> ?_ '
                                                '& ?accept <rdf:type> <cim:Accept> ?_ & ?accept <dul:hasConstituent> ?off ?_'.format(session_rdf))
            manual_accept = 0
            manual_start = ""
            manual_end = ""

            if len(manual_offers) > 0:
                 manual_accept = 1

                 manual_start = RdfProxy.selectQuery('select ?t where {} <dul:hasConstituent> ?inst ?t & ?inst <dul:hasParticipant> <cim:Manual> ?_ '
                                               '& ?inst <rdf:type> <cim:Instruction> ?_ aggregate ?res = LMin ?t'.format(session_rdf))[0]
                 
                 manual_end = RdfProxy.selectQuery('select ?t where ?inst <dul:hasPart> ?_ ?t & {} <dul:hasConstituent> ?inst ?_ & ?inst <dul:hasParticipant> <cim:Manual> ?_ '
                                               '& ?inst <rdf:type> <cim:Instruction> ?_ aggregate ?res = LMax ?t'.format(session_rdf))
                 
                 #manual_end = RdfProxy.selectQuery('select ?t where {} <dul:hasConstituent> ?yn ?t & ?yn <rdf:type> <cim:YNQuestionAddPose> ?_ aggregate ?res = LMin ?t'.format(session_rdf))[0]
                 if manual_end:
                    manual_end = manual_end[0]
                 else:
                    manual_end = str(int(manual_start)+10000)

            # --- Quality slides --- #
            
            quality_offers = RdfProxy.selectQuery('select ?off ?accept where {} <dul:hasConstituent> ?off ?_ '
                                                '& ?off <rdf:type> <cim:Offer> ?_ & ?off <dul:hasParticipant> <cim:Quality> ?_ '
                                                '& ?accept <rdf:type> <cim:Accept> ?_ & ?accept <dul:hasConstituent> ?off ?_'.format(session_rdf))
            quality_accept = 0
            quality_start = ""
            quality_end = ""

            if len(quality_offers) > 0:
                 quality_accept = 1
                 quality_start = RdfProxy.selectQuery('select ?t where {} <dul:hasConstituent> ?inst ?t & ?inst <dul:hasParticipant> <cim:Quality> ?_ '
                                               '& ?inst <rdf:type> <cim:Instruction> ?_ aggregate ?res = LMin ?t'.format(session_rdf))[0]
                 
                 quality_end = RdfProxy.selectQuery('select ?t where ?inst <dul:hasPart> ?_ ?t & {} <dul:hasConstituent> ?inst ?_ & ?inst <dul:hasParticipant> <cim:Quality> ?_ '
                                               '& ?inst <rdf:type> <cim:Instruction> ?_ aggregate ?res = LMax ?t'.format(session_rdf))
                 
                 if quality_end:
                    quality_end = quality_end[0]
                 else:
                    quality_end = str(int(quality_start)+10000)
                 
                 
                 #quality_end = RdfProxy.selectQuery('select ?t where {} <dul:hasConstituent> ?next ?t & ?next <rdf:type> <cim:RequestNext> ?_ '
                  #                                  '& ?next <dul:hasConstituent> ?inst ?_ & ?inst <dul:hasParticipant> <cim:Quality> ?_ aggregate ?res = LMin ?t'.format(session_rdf))[0]

            # --- Manual poses --- #
            poses = RdfProxy.selectQuery('select ?pose where {} <cim:hasManualPoses> ?quat ?_ '
                                         '& ?quat <rdf:type> <cim:Quaternion> ?_ & ?quat <cim:representation> ?pose ?_ '.format(scan_rdf))
            added_poses = len(poses)
            
            # --- Scan start/end --- #
            scan_time = RdfProxy.selectQuery('select distinct ?start ?end ?s ?t where {} <cim:fromTime> ?start ?s '    
                                '& {} <cim:toTime> ?end ?t'.format(scan_rdf,scan_rdf)) # inside list
            if not scan_time:
                 continue
            else:
                scan_time = scan_time[0]
                scan_start = scan_time[0]
                scan_end = scan_time[1]

                # --- Scan quality --- #
                scan_quality = RdfProxy.selectQuery('select ?qual where {} <cim:scanQuality> ?qual ?t'.format(scan_rdf))[0] # inside list
                scan_quality = "%.4f"%float(scan_quality)

                # --- Scan decision --- #
                scan_decision = RdfProxy.selectQuery('select ?decision where {} <cim:wasSuccessful> ?decision ?t'.format(scan_rdf))[0] # inside list

                # --- Request back --- #
                no_of_back_requests = len(RdfProxy.selectQuery('select ?req where {} <dul:hasConstituent> ?req ?_ '
                                                            '& ?req <rdf:type> <cim:RequestBack> ?_ & ?req <dul:hasConstituent> ?_ ?_ '.format(session_rdf))) #replace one ?_ with specific type of instruction if needed
                
                with open(filename, 'a', newline="") as csvfile:
                        csvwriter = csv.writer(csvfile)
                        # NOTE: accepting instructions and back requests are for the whole session, not the particular scan
                        csvwriter.writerow([user_name, session_id, session_start, session_end, intro_accept, intro_start, intro_end, reso_accept, reso_start, reso_end, manual_accept, manual_start, manual_end, quality_accept, quality_start, quality_end, scan_id, scan_hres, scan_vres, scan_start, scan_end, change_resolution, added_poses, no_of_back_requests, scan_quality, scan_decision])
            j += 1
        i += 1

    csvData = pd.read_csv(filename)
    csvData.sort_values(csvData.columns[19],axis=0,inplace=True)
    csvData['scan_id'] = [i for i in range(1,len(csvData['scan_id'])+1)]
    session_ids = [1]
    for i in range(len(csvData['session_id'])-1):
        if csvData['session_id'].iloc[i] == csvData['session_id'].iloc[i+1]:
            session_ids.append(session_ids[-1])
        else:
            session_ids.append(session_ids[-1]+1)
    csvData['session_id'] = session_ids
    
    num_sessions = [1]
    for i in range(len(csvData['user_name'])-1):
        if csvData['session_id'].iloc[i] == csvData['session_id'].iloc[i+1]:
            num_sessions.append(num_sessions[-1])
        elif csvData['user_name'].iloc[i] == csvData['user_name'].iloc[i+1]:
            num_sessions.append(num_sessions[-1]+1)
        else:
            num_sessions.append(1) 
    csvData = csvData.assign(num_sessions=num_sessions)
    with open(filename, 'w') as csvfile:
        csvData.to_csv(filename)

if __name__ == "__main__":
    main()