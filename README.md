[![published](https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg)](https://developer.cisco.com/codeexchange/github/repo/null0route/aci-gather-faults)
# Gather faults from ACI fabrics

Sample code how to use the Cisco ACI REST API to gather faults and fabric healths over 1 or several ACI fabrics. The results are filtered and presented in an easy to consume format. 


## Use Case Description

This sample code illustrate how an administrator could use the API and adding simple business logic to filter out events which are older than X amount of days (Default 7).

## Requirements

Tested with Python3.9.2

## Installation

pip install -r requirements.txt

## Usage

The script will prompt the user for username and password for each fabric which is being iterated. It is up to the user to securely handle their credentials.

### Run with Default parameters:

    python3 main.py

### Run with custom fabric JSON file

    python3 main.py -f customfabric.json

### Get faults 14 days before current time

    python3 main.py -d 14

### Truncate description text to only 1000 characters

    python3 main.py -l 1000

### Get faults for 3 days with less than 20 characters and with a custom fabric JSON file

    python3 main.py -d 3 -l 20 -f customfabric.json
    
### Run the help command to get further help with available flags
    
    python3 main.py -h
    
### DevNet Sandbox

A great way to try this sample code is by using it against [ACI Simulator v4](https://developer.cisco.com/docs/sandbox/#!data-center/overview). DNS name and credentials for the sandbox could be found inside the detailed description of the sandbox.

## How to test the software

The APIs and the code was tested 15th of July 2021

## Known issues


## Getting involved

This section should detail why people should get involved and describe key areas you are currently focusing on; e.g., trying to get feedback on features, fixing certain bugs, building important pieces, etc. Include information on how to setup a development environment if different from general installation instructions.

General instructions on _how_ to contribute can be found in the [CONTRIBUTING](./CONTRIBUTING.md) file.
