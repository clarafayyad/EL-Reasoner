import sys
from py4j.java_gateway import JavaGateway
from el_reasoner import ELReasoner


def main():
    # if len(sys.argv) != 3:
        # print("Usage: python main.py ONTOLOGY_FILE CLASS_NAME")
        # sys.exit(1)

    # ontology_file = sys.argv[1]
    # class_name = sys.argv[2]

    ontology_file = "person.owl"
    class_name = "Child"

    try:
        gateway = JavaGateway()
        parser = gateway.getOWLParser()
        ontology = parser.parseFile(ontology_file)
        gateway.convertToBinaryConjunctions(ontology)
        formatter = gateway.getSimpleDLFormatter()
        reasoner = ELReasoner(ontology, formatter)
        subsumers = reasoner.get_all_subsumers(class_name)
        print("Subsumers of " + class_name + " are: ")
        for subsumer in subsumers:
            print(subsumer)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
