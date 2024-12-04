import re

from individual import Individual
from roles import Role


def extract_relation_and_successor(expression):
    # Regular expression to match ∃r.C
    match = re.match(r"∃([\w]+)\.([\w]+)", expression)
    if match:
        relation = match.group(1)
        successor = match.group(2)
        return relation, successor
    return None, None


class ELReasoner:
    def __init__(self, ontology, formatter):
        self.ontology = ontology
        self.formatter = formatter
        self.individuals = {}  # Dictionary mapping individuals to their concepts and roles.
        self.relevant_concepts = self.extract_relevant_concepts()

    def initialize_individual(self, d0, C0):
        new_individual = Individual(d0)
        new_individual.initial_concept = C0
        new_individual.concepts.add(C0)
        self.individuals[d0] = new_individual

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
            if '⊓' in concept:
                expression = concept.strip('()')
                left, right = expression.split('⊓', 1)
                subconcepts = [left.strip(), right.strip()]
                for sub_concept in subconcepts:
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
            if self.top_rule(): changes = True
            if self.conjunction_rule_1(): changes = True
            if self.conjunction_rule_2(): changes = True
            if self.existential_rule_1(): changes = True
            if self.existential_rule_2(): changes = True
            if self.concept_inclusion_rule(): changes = True
            if self.process_t_box(): changes = True

    def is_entailment(self, d0, D0):
        return D0 in self.individuals[d0].concepts

    def top_rule(self):
        changed = False
        for ind_name, ind in self.individuals.items():
            if "⊤" not in ind.concepts:
                self.individuals[ind_name].concepts.add("⊤")
                changed = True
        return changed

    def conjunction_rule_1(self):
        # If d has C⊓D assigned, assign also C and D to d
        changed = False
        new_concepts = set()
        for ind_name, ind in self.individuals.items():
            for concept in ind.concepts:
                if '⊓' in concept:
                    expression = concept.strip('()')
                    left, right = expression.split('⊓', 1)
                    parts = [left.strip(), right.strip()]
                    for part in parts:
                        if self.is_relevant(part):
                            new_concepts.add(part)
            if new_concepts - ind.concepts:
                self.individuals[ind_name].concepts.update(new_concepts)
                changed = True
        return changed

    def conjunction_rule_2(self):
        # If d has C and D assigned, assign also C⊓D to d.
        changed = False
        for ind_name, ind in self.individuals.items():
            concepts = ind.concepts
            for c1 in concepts:
                for c2 in concepts:
                    conjunction = ("and", frozenset({c1, c2}))
                    if c1 != c2 and self.is_relevant(conjunction) and conjunction not in concepts:
                        self.individuals[ind_name].concepts.add(conjunction)
                        changed = True
        return changed

    def existential_rule_1(self):
        # Apply rule to all individuals
        changed = False
        new_individuals = []  # Collect new individuals to add later

        for ind_name, ind in list(self.individuals.items()):  # Iterate over a copy of the dictionary
            # For each individual, check if it has an existential concept ∃r.C
            for concept in ind.concepts:
                if '∃' in concept and not '⊓' in concept:
                    relation, target_concept = extract_relation_and_successor(concept)
                    # Look for an individual with the target concept
                    for e_name, e_ind in self.individuals.items():
                        if target_concept == e_ind.initial_concept:
                            # If such an individual exists, make it the r-successor of ind
                            role = Role(relation, target_concept, e_name)
                            if not ind.has_role(role):
                                ind.roles.add(role)
                                changed = True
                            break
                    else:
                        # If no such individual is found, collect new individual data
                        ind_count = len(self.individuals)
                        new_ind_name = "d" + str(ind_count)
                        new_ind = Individual(new_ind_name)
                        new_ind.initial_concept = target_concept
                        new_ind.concepts.add(target_concept)
                        new_individuals.append(new_ind)
                        role = Role(relation, target_concept, new_ind_name)
                        ind.roles.add(role)
                        changed = True

        # Add new individuals after the iteration
        for new_ind in new_individuals:
            self.individuals[new_ind.name] = new_ind

        return changed

    def existential_rule_2(self):
        # If d has an r-successor with C assigned, add ∃r.C to d
        changed = False
        for ind_name, ind in self.individuals.items():
            for role in ind.roles:
                existential_concept = "∃" + role.relation + "." + role.successor
                if self.is_relevant(existential_concept):
                    if existential_concept not in ind.concepts:
                        ind.concepts.add(existential_concept)
                        changed = True
        return changed

    def concept_inclusion_rule(self):
        # If d has C assigned and C ⊑ D, then also assign D to d
        changed = False
        for ind_name, ind in self.individuals.items():
            ind_concepts = ind.concepts
            new_concepts = set()  # Set to collect new concepts to add

            for c in ind_concepts:
                for axiom in self.ontology.tbox().getAxioms():
                    axiom_type = axiom.getClass().getSimpleName()
                    if axiom_type != "GeneralConceptInclusion":
                        continue
                    try:
                        lhs = self.formatter.format(axiom.lhs())
                        rhs = self.formatter.format(axiom.rhs())
                        if lhs == c and self.is_relevant(rhs):
                            new_concepts.add(rhs)  # Collect the new concept to add
                    except Exception:
                        continue

            # After the loop finishes, update the individual's concepts
            if new_concepts - ind.concepts:
                self.individuals[ind_name].concepts.update(new_concepts)
                changed = True

        return changed

    def process_t_box(self):
        changed = False
        axioms = self.ontology.tbox().getAxioms()
        for axiom in axioms:
            axiom_type = axiom.getClass().getSimpleName()
            if axiom_type == "GeneralConceptInclusion" or axiom_type == "EquivalenceAxiom":
                try:
                    lhs = self.formatter.format(axiom.lhs())
                    rhs = self.formatter.format(axiom.rhs())
                    for ind_name, ind in self.individuals.items():
                        ind_concepts = ind.concepts
                        new_concepts = set()
                        if lhs in ind_concepts and self.is_relevant(rhs):
                            new_concepts.add(rhs)
                        if new_concepts - ind.concepts:
                            self.individuals[ind_name].concepts.update(new_concepts)
                            changed = True
                except Exception:
                    continue
            if axiom_type == "EquivalenceAxiom":
                try:
                    lhs = self.formatter.format(axiom.lhs())
                    rhs = self.formatter.format(axiom.rhs())
                    for ind_name, ind in self.individuals.items():
                        ind_concepts = ind.concepts
                        new_concepts = set()
                        if rhs in ind_concepts and self.is_relevant(lhs):
                            new_concepts.add(lhs)
                        if new_concepts - ind.concepts:
                            self.individuals[ind_name].concepts.update(new_concepts)
                            changed = True
                except Exception:
                    continue
        return changed

    def get_all_subsumers(self, concept_name):
        d0 = "d0"
        self.initialize_individual(d0, concept_name)
        self.run_completion()
        return self.individuals[d0].concepts
