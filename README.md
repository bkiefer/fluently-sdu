# fluently_mem
MEM use case from fluently project

## GUI

The GUI remains the same, I added [X] buttons in the top-right corner of the bounding boxes so that users can also delete them in case there are too many. It no longer gets initial values from the GUI itself. Everything should now come from the vision module (via the Behavior Tree). Because of this, most GUI screens have a change_label() function to update labels that are not available during initialization.

## Vision module

The behavior tree is using the Vision module so once we actually receive camera frames they should be successfully passed to the GUI.
QUESTION: I didn't know whether we take the current camera frame at the beginning of the task (with vision.get_current_frame()) and reuse it or if we call the get_current_frame() function at each step. For now I have included it in all of the behaviors but it can of course be changed.

## Robot module

I am calling the functions robot_module.pick_and_place() and robot_module.frame_to_world() in the behavior tree but for now it makes no difference.

## Behaviour tree and GUI integration

I am ticking the tree and the GUI from the main() function in the behavior_tree.py file, I found this to be a bit easier when handling how to close everything at the end. The unicode tree prints at every tick in the terminal but this can just be removed.

## Setup

To run everything, now that the RDF server is running as well, you will need the following (or similar):

    ├── fluently_mem_ws                   
       ├── fluently_mem        
       ├── fluently_ontology   
       └── hfc-thrift          

All repos are the same as in the prima additive workspace:
https://gitlab.sdu.dk/gubo/fluently_mem
https://github.com/bkiefer/fluently_ontology
https://github.com/bkiefer/hfc-thrift

They have been updated so remember to pull again.

To install HFC Thrift and the ontology, follow these steps:

### HFC Thrift:

Make sure you have an internet connection and openjdk-11-jdk, maven, and git are installed 
	$ sudo apt install openjdk-11-jdk maven git 
Go the hfc-thrift directory and install
    $ cd fluently_mem_ws/hfc-thrift
NOTE: DO NOT RUN ./COMPILE.SH!
    $ mvn -U clean install
    $ mvn -f apps.xml install
Install the dependencies (make sure pip and setuptools are recent versions): 
	$ cd src/main/python 
	$ pip install . 

### The Fluently ontology:

Install raptor2 utilities: 
	$ cd fluently_ontology 
	$ sudo apt install raptor2-utils 
Run the following script in the root directory of the repository: 
	$ ./ntcreate.sh 

## How to run

You will need two terminals, one for the HFC server and one for everything else.

### HFC server:

Start the server (the new version of the Behavior Tree will only run if the RDF server is running): 
	$ hfc-thrift/bin/startServer.sh -p 7070 fluently_ontology/fluently.yml 

### Behavior tree:

First source .bashempi for the paths:
    $ cd fluently_mem_ws/fluently_mem
    $ source .bashempi
Run the behavior tree:
    $ python3 src/behavior_tree.py