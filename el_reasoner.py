class ELReasoner:
    def __init__(self, ontology, formatter):
        self.ontology = ontology
        self.formatter = formatter
        self.individuals = {}  # Dictionary mapping individuals to their concepts and roles.
        self.relevant_concepts = self.extract_relevant_concepts()

    def initialize_individual(self, d0, C0):
        self.individuals[d0] = {"concepts": {C0}, "roles": {}}

    def extract_relevant_concepts(self):
        relevant_concepts = set()

        # Gather all concepts from the TBox axioms (both LHS and RHS)
        for axiom in self.ontology.tbox().getAxioms():
            try:
                lhs = self.formatter.format(axiom.lhs())
                rhs = self.formatter.format(axiom.rhs())
                relevant_concepts.add(lhs)
                relevant_concepts.add(rhs)
            except Exception:
                continue

        # Include nested concepts by recursively collecting from the LHS and RHS
        def extract_nested_concepts(concept):
            if isinstance(concept, tuple):  # For conjunctions or other nested structures
                for sub_concept in concept[1]:
                    relevant_concepts.add(sub_concept)
                    extract_nested_concepts(sub_concept)  # Recursively add nested concepts

        # Check for nested concepts in the TBox
        for axiom in self.ontology.tbox().getAxioms():
            try:
                lhs = self.formatter.format(axiom.lhs())
                rhs = self.formatter.format(axiom.rhs())
                # Add nested concepts
                extract_nested_concepts(lhs)
                extract_nested_concepts(rhs)
            except Exception:
                continue

        return relevant_concepts

    def is_relevant(self, concept):
        return concept in self.relevant_concepts

    def run_completion(self):
        changes = True
        while changes:
            changes = False
            for d in self.individuals:
                if self.top_rule(d): changes = True
                if self.u_rule_1(d): changes = True
                if self.u_rule_2(d): changes = True
                if self.existential_rule_1(d): changes = True
                if self.existential_rule_2(d): changes = True
                if self.disjunction_rule(d): changes = True

    def is_entailment(self, d0, D0):
        return D0 in self.individuals[d0]["concepts"]

    def top_rule(self, d):
        if "⊤" not in self.individuals[d]["concepts"]:
            self.individuals[d]["concepts"].add("⊤")
            return True
        return False

    def u_rule_1(self, d):
        new_concepts = set()
        for concept in self.individuals[d]["concepts"]:
            if isinstance(concept, tuple) and concept[0] == "and":
                for part in concept[1]:
                    if self.is_relevant(part):
                        new_concepts.add(part)
        if new_concepts - self.individuals[d]["concepts"]:
            self.individuals[d]["concepts"].update(new_concepts)
            return True
        return False

    def u_rule_2(self, d):
        concepts = self.individuals[d]["concepts"]
        for c1 in concepts:
            for c2 in concepts:
                conjunction = ("and", frozenset({c1, c2}))
                if c1 != c2 and self.is_relevant(conjunction) and conjunction not in concepts:
                    self.individuals[d]["concepts"].add(conjunction)
                    return True
        return False

    def existential_rule_1(self, d):
        new_roles = {}
        for concept in self.individuals[d]["concepts"]:
            if isinstance(concept, tuple) and concept[0] == "exists":
                role, filler = concept[1]
                if role in self.individuals[d]["roles"]:
                    for successor in self.individuals[d]["roles"][role]:
                        if filler in self.individuals[successor]["concepts"]:
                            return False
                elif self.is_relevant(filler):
                    new_roles[role] = filler
        if new_roles:
            for role, filler in new_roles.items():
                new_individual = f"new_{role}_{filler}"
                self.individuals[new_individual] = {"concepts": {filler}, "roles": {}}
                self.individuals[d]["roles"].setdefault(role, []).append(new_individual)
            return True
        return False

    def existential_rule_2(self, d):
        for role, successors in self.individuals[d]["roles"].items():
            for successor in successors:
                for concept in self.individuals[successor]["concepts"]:
                    existential = ("exists", (role, concept))
                    if self.is_relevant(existential) and existential not in self.individuals[d]["concepts"]:
                        self.individuals[d]["concepts"].add(existential)
                        return True
        return False

    def disjunction_rule(self, d):
        for c in self.individuals[d]["concepts"]:
            for axiom in self.ontology.tbox().getAxioms():
                axiom_type = axiom.getClass().getSimpleName()
                if axiom_type != "GeneralConceptInclusion":
                    continue
                try:
                    lhs = self.formatter.format(axiom.lhs())
                    rhs = self.formatter.format(axiom.rhs())
                    if lhs == c and self.is_relevant(rhs):
                        self.individuals[d]["concepts"].add(rhs)
                        return True
                except Exception:
                    continue
        return False

    def get_all_subsumers(self, concept_name):
        d0 = "d0"
        self.initialize_individual(d0, concept_name)
        self.run_completion()
        return self.individuals[d0]["concepts"]
