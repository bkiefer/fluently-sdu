# Example code for using the HFC -- python bridge

# Installation

First create a conda or other virtual environment and activate it.

Install [hfc-thrift](https://github.com/bkiefer/hfc-thrift) from github:

    git clone git@github.com:bkiefer/hfc-thrift.git
    cd hfc-thrift
    ./compile.sh
    cd src/main/python
    pip install .

Clone the extended [Fluently ontology](https://github.com/bkiefer/fluently_ontology)

    git clone git@github.com:bkiefer/fluently_ontology.git

Start the HFC server:

    <hfc-thrift-dir>/bin/startServer -p 7070 <ontology-dir>/fluently.yml


Now the code should run, although it's not doing anything at the moment. If you want to check that it's really working, uncomment the line

    #persistenceFile: persistent.nt

in `fluently.yml` and re-run it. You can see that a user John Doe has been created, and in any new run, no new user will be created, but all sessions are added to the existing user.
