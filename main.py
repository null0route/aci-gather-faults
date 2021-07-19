#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Main python file which uses the ACI REST API to gather faults 

"""


import argparse
import datetime
import json
import prettytable
import requests
import types
import getpass
from requests.models import HTTPError
import urllib3

__loginPath = "/api/aaaLogin.json"
__logoutPath = "/api/aaaLogout.json"
__classQuery = "/api/node/class/{0}.json"
__query_filter_string = '?query-target-filter={0}({1},"{2}")'
__moQuery = "/api/node/mo/{0}.json"
__schema = "https://"

__severityMap = {
    "critical":6,
    "major":5,
    "minor":4,
    "warning":3,
    "info":2,
    "cleared":1
}

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Get Faults from your ACI Fabrics',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-f","--fabric", help="Providate a fabric JSON file", default="fabrics.json",type=str)
    parser.add_argument("-d","--days", help="Filter events older than value provided", default=7, type=int)
    parser.add_argument("-l","--length", help="Truncate the description output to the value provided", default=200, type=int)
    parser.add_argument("-a","--ack",help="Show faults which have been ACKed in the APIC",action="store_true")
    parser.add_argument("--same-credentials",help="Allows a user to only provide credentials for all fabrics once",action='store_true')
    parser.add_argument("--faults",help="Filter fault severities not provided",default="critical,major,minor,warning,info,cleared", type=str)
    parser.add_argument("--ignore-warnings",help="Disable warning messages",action='store_true')
    parser.add_argument("--disable-certificate-check",help="Disables validation of server certificate",action='store_false')

    args = parser.parse_args()

    fabric_file = args.fabric
    max_event_age = args.days
    max_desc_length = args.length

    if args.ignore_warnings is not None:
        urllib3.disable_warnings()
    
    fabrics = json.load(open(fabric_file,'r'))


    faults_over_all_fabrics = []

    username = None
    password = None

    for fabric in fabrics["fabrics"]:
        session = requests.Session()

        if args.same_credentials:
            if username is None:
                username = input("Username for all fabrics: ")
                password = getpass.getpass("Password to all fabrics: ")
        else:
            username = input("Username to fabric {}: ".format(fabric))
            password = getpass.getpass("Password to fabric {}: ".format(fabric))

        session.verify = False if args.disable_certificate_check is not None else True
        session.headers = {"Content-Type":"application/json"}

        #Login
        response = session.post(
            url=__schema+fabric+__loginPath,
            json={
                "aaaUser":{
                    "attributes":{
                        "name":username,
                        "pwd":password
                    }
                }
            }
        )

        try:
            if not response.ok:
                response.raise_for_status()
        except HTTPError as error:
            print(error)
            continue
        

        #Get All Faults
        not_older_than = (datetime.datetime.utcnow()-datetime.timedelta(days=max_event_age)).strftime("%Y-%m-%dT%H:%M")
        
        response = session.get(
            url=__schema+fabric+__classQuery.format("faultInfo")+__query_filter_string.format("gt","faultInst.lastTransition",not_older_than)
        )

        try:
            if not response.ok:
                response.raise_for_status()
        except HTTPError as error:
            print(error)
            continue
        
                
        allFaults = response.json()

        #Get Fabric overall health
        response = session.get(
            url=__schema+fabric+__moQuery.format("topology/health")
        )

        try:
            if not response.ok:
                response.raise_for_status()
        except HTTPError as error:
            print(error)
            continue

        fabric_health = int(response.json()["imdata"][0]["fabricHealthTotal"]["attributes"]["cur"])


        #Convert Fault JSON output to Python object
        #https://stackoverflow.com/questions/6578986/how-to-convert-json-data-into-a-python-object
        pyAllFaults = json.loads(json.dumps(allFaults), object_hook=lambda d: types.SimpleNamespace(**d))

        #Logout from ACI cluster
        session.post(
            url=__schema+fabric+__logoutPath,
            json={
                "aaaUser":{
                    "attributes":{
                        "name":username
                    }
                }
            })

        #Collect Faults to print
        print_faults = []




        for fault in pyAllFaults.imdata:
            if hasattr(fault,"faultInst"):
                attr = fault.faultInst.attributes
            elif hasattr(fault,"faultDelegate"):
                attr = fault.faultDelegate.attributes
            else:
                print("Fault type has not been implemented")
                continue
            
            if attr.ack == "yes" and args.ack is not None:
                continue

            if attr.severity not in args.faults.split(","):
                continue
            
            attr.fabric = fabric
            attr.fabricHealth = fabric_health
            print_faults.append(attr)

        if len(print_faults) == 0:
            #Add a "simulated fault" when there are no new faults to report for a fabric"
            json.loads(json.dumps(allFaults), )
            print_faults = [
                json.loads(json.dumps({
                    "fabric":fabric,
                    "fabricHealth":fabric_health,
                    "ack":"no",
                    "cause":"faults-filtered",
                    "descr":"No new faults in {} days".format(str(max_event_age)),
                }),object_hook=lambda d: types.SimpleNamespace(**d))
            ]
                

        faults_over_all_fabrics = faults_over_all_fabrics + print_faults

    faults_over_all_fabrics = sorted(
        faults_over_all_fabrics, 
        key=lambda x: (
            100-x.fabricHealth,
            __severityMap[getattr(x,"severity","info")],
            getattr(x,"lastTransition",not_older_than)
            ),
        reverse=True
        )

    table = prettytable.PrettyTable()

    table.field_names = [
        "Fabric",
        "Fabric Health",
        "Date",
        "Domain",
        "Severity",
        "Fault Code",
        "Cause",
        "Description",
        "Occur"
    ]
    for fault in faults_over_all_fabrics:
            table.add_row([
                fault.fabric,
                fault.fabricHealth,
                getattr(fault,"lastTransition",""),
                getattr(fault,"domain",""),
                getattr(fault,"severity",""),
                getattr(fault,"code",""),
                getattr(fault,"cause",""),
                getattr(fault,"descr","")[:max_desc_length],
                getattr(fault,"occur","1")
            ])

    print(table)