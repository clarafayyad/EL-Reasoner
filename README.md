# EL-Reasoner
This project consists of an EL Reasoner used to infer subsumers of a certain class given an ontology in .owl format. 

## Running the Reasoner
1. Open one terminal window and run `java -jar dl4python-0.1-jar-with-dependencies.jar`.
2. Open another and run `python main.py ONTOLOGY_FILE CLASS_NAME`, for example: `python main.py smoothie.owl Vegan_Delight`
3. _Option_: For debugging purposes, set `debug=True` in [the main file](main.py).
4. After running the program, the subsumers are going to be printed in the console, each on a line. 
