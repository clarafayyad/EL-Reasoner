import sys
import os
from py4j.java_gateway import JavaGateway
from el_reasoner import ELReasoner

test_cases = {
    "1": {
        "file": "ontologies/animal.owl",
        "class": "Dog",
        "expected_subsumers": ["Dog", "Mammal", "Animal", "⊤"],
    },
    "2": {
        "file": "ontologies/transport.owl",
        "class": "Bus",
        "expected_subsumers": ["Bus", "PublicTransport", "Vehicle", "⊤", "∃hasFuelType.Diesel"],
    },
    "3": {
        "file": "ontologies/person.owl",
        "class": "Child",
        "expected_subsumers": ["Child", "Person", "∃hasParent.Person"],
    }
}

for number, test in test_cases.items():
    file = test["file"]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, file)

    gateway = JavaGateway()
    parser = gateway.getOWLParser()
    ontology = parser.parseFile(file_path)
    gateway.convertToBinaryConjunctions(ontology)
    formatter = gateway.getSimpleDLFormatter()

    reasoner = ELReasoner(ontology, formatter)
    subsumers = reasoner.get_all_subsumers(test["class"])

    for expected_subsumer in test["expected_subsumers"]:
        if not expected_subsumer in subsumers:
            print("Expected subsumer " + expected_subsumer + " not found")
            print("Subsumers: " + str(subsumers))
            sys.exit(1)

print("Tests passed!")