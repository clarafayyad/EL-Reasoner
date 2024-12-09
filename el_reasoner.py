import copy
import re

from individual import Individual
from roles import Role


def extract_relation_and_successor(expression):
    # Remove double quotes if present
    exp = expression.replace('"', '')
    # Regular expression to match ∃r.C where r is the relation and C is the successor
    match = re.match(r"∃([\w]+)\.(.+)", exp)
    if match:
        relation = match.group(1)
        successor = match.group(2)
        return relation, successor
    return None, None


class ELReasoner:
    def __init__(self, ontology, formatter, debug=False):
        self.ontology = ontology
        self.formatter = formatter
        self.individuals = {}  # Dictionary mapping individuals to their concepts and roles.
        self.relevant_concepts = self.extract_relevant_concepts()
        self.debug = debug
        self.visualize_ontology()

    def visualize_ontology(self):
        if not self.debug:
            return
        axioms = self.ontology.tbox().getAxioms()
        print("Ontlogy:")
        for axiom in axioms:
            print(self.formatter.format(axiom))
        print()

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
                lhs, rhs = self.extract_lhs_rhs_from_axiom(axiom)
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
                lhs, rhs = self.extract_lhs_rhs_from_axiom(axiom)
                # Add nested concepts
                extract_nested_concepts(lhs)
                extract_nested_concepts(rhs)
            except Exception:
                continue

        return [concept.replace('"', '') for concept in relevant_concepts]

    def extract_lhs_rhs_from_axiom(self, axiom):
        try:
            lhs = self.formatter.format(axiom.lhs())
            clean_lhs = lhs.replace('"', '')
            rhs = self.formatter.format(axiom.rhs())
            clean_rhs = rhs.replace('"', '')
            return clean_lhs.strip(), clean_rhs.strip()
        except Exception:
            operators = ["⊑", "≡", "<=", "="]
            for op in operators:
                if op in axiom.toString():
                    lhs, rhs = axiom.toString().split(op, 1)
                    clean_lhs = lhs.replace('"', '')
                    clean_rhs = rhs.replace('"', '')
                    return clean_lhs.strip(), clean_rhs.strip()

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
                print("Added concept ⊤ to individual", ind_name) if self.debug else None
                changed = True
        return changed

    def conjunction_rule_1(self):
        # If d has C⊓D assigned, assign also C and D to d
        changed = False
        new_concepts = set()
        for ind_name, ind in self.individuals.items():
            for concept in ind.concepts:
                if '⊓' in concept or ' n ' in concept:
                    print("Found conjunction: ", concept) if self.debug else None
                    conjunction_op = '⊓'
                    if ' n ' in concept:
                        conjunction_op = ' n '
                    expression = concept.strip('()')
                    left, right = expression.split(conjunction_op, 1)
                    parts = [left.strip(), right.strip()]
                    for part in parts:
                        clean_part = part.replace('"', '')
                        if self.is_relevant(part):
                            new_concepts.add(clean_part)
            if new_concepts - ind.concepts:
                self.individuals[ind_name].concepts.update(new_concepts)
                print("Added these concepts to individual", ind_name, ":", new_concepts) if self.debug else None
                changed = True
        return changed

    def conjunction_rule_2(self):
        # If d has C and D assigned, assign also C⊓D to d.
        changed = False
        for ind_name, ind in self.individuals.items():
            concepts = ind.concepts
            for c1 in concepts:
                for c2 in concepts:
                    conjunction = c1 + "⊓" + c2
                    if c1 != c2 and self.is_relevant(conjunction) and conjunction not in concepts:
                        print("Found 2 concepts: ", c1, c2) if self.debug else None
                        self.individuals[ind_name].concepts.add(conjunction)
                        print("Added this concept to individual", ind_name, ":", conjunction) if self.debug else None
                        changed = True
        return changed

    def existential_rule_1(self):
        # Apply rule to all individuals
        changed = False
        individuals_copy = copy.deepcopy(self.individuals)
        for ind_name, ind in list(individuals_copy.items()):
            # For each individual, check if it has an existential concept ∃r.C
            for concept in ind.concepts:
                if '∃' in concept and not '⊓' in concept:
                    print("Found existential: ", concept) if self.debug else None
                    relation, target_concept = extract_relation_and_successor(concept)
                    # Look for an individual with the target concept as initial concept
                    for e_name, e_ind in self.individuals.items():
                        if target_concept == e_ind.initial_concept:
                            # If such an individual exists, make it the r-successor of ind
                            role = Role(relation, e_ind)
                            if not ind.has_role(relation, e_ind):
                                self.individuals[ind_name].roles.add(role)
                                print("Added this role to individual", ind_name, ":",
                                      role.relation) if self.debug else None
                                changed = True
                            break
                    else:
                        # If no such individual is found, collect new individual data
                        ind_count = len(self.individuals)
                        new_ind_name = "d" + str(ind_count)
                        new_ind = Individual(new_ind_name)
                        new_ind.initial_concept = target_concept
                        print("Created new individual", new_ind_name, "with initial concept",
                              target_concept) if self.debug else None
                        new_ind.concepts.add(target_concept)
                        self.individuals[new_ind_name] = new_ind
                        role = Role(relation, new_ind)
                        self.individuals[ind_name].roles.add(role)
                        print("Added this role to individual", ind_name, ":", role.relation) if self.debug else None
                        changed = True
        return changed

    def existential_rule_2(self):
        # If d has an r-successor with C assigned, add ∃r.C to d
        changed = False
        for ind_name, ind in self.individuals.items():
            new_concepts = set()
            for role in ind.roles:
                for concept in role.successor.concepts:
                    existential_concept = "∃" + role.relation + "." + concept
                    if self.is_relevant(existential_concept):
                        if existential_concept not in ind.concepts:
                            new_concepts.add(existential_concept)

            if new_concepts - ind.concepts:
                self.individuals[ind_name].concepts.update(new_concepts)
                print("Added these concepts to individual", ind_name, ":", new_concepts) if self.debug else None
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
                        # print("Found GCI: ", axiom.toString()) if self.debug else None
                        lhs, rhs = self.extract_lhs_rhs_from_axiom(axiom)
                        if lhs == c and self.is_relevant(rhs):
                            new_concepts.add(rhs)
                    except Exception:
                        continue

            # After the loop finishes, update the individual's concepts
            if new_concepts - ind.concepts:
                self.individuals[ind_name].concepts.update(new_concepts)
                print("Added this concept to individual", ind_name, ":", new_concepts) if self.debug else None
                changed = True

        return changed

    def process_t_box(self):
        changed = False
        axioms = self.ontology.tbox().getAxioms()
        for axiom in axioms:
            axiom_type = axiom.getClass().getSimpleName()
            if axiom_type == "GeneralConceptInclusion" or axiom_type == "EquivalenceAxiom":
                # print("Found GCI or equivalence: ", axiom.toString()) if self.debug else None
                try:
                    lhs, rhs = self.extract_lhs_rhs_from_axiom(axiom)
                    for ind_name, ind in self.individuals.items():
                        ind_concepts = ind.concepts
                        new_concepts = set()
                        if lhs in ind_concepts and self.is_relevant(rhs):
                            new_concepts.add(rhs)
                        if new_concepts - ind.concepts:
                            self.individuals[ind_name].concepts.update(new_concepts)
                            changed = True
                except Exception as e:
                    continue
            if axiom_type == "EquivalenceAxiom":
                # print("Found equivalence: ", axiom.toString()) if self.debug else None
                try:
                    lhs, rhs = self.extract_lhs_rhs_from_axiom(axiom)
                    for ind_name, ind in self.individuals.items():
                        ind_concepts = ind.concepts
                        new_concepts = set()
                        if rhs in ind_concepts and self.is_relevant(lhs):
                            new_concepts.add(lhs)
                        if new_concepts - ind.concepts:
                            self.individuals[ind_name].concepts.update(new_concepts)
                            print("Added these concepts to individual", ind_name, ":",
                                  new_concepts) if self.debug else None
                            changed = True
                except Exception:
                    continue
        return changed

    def get_all_subsumers(self, concept_name):
        d0 = "d0"
        self.initialize_individual(d0, concept_name)
        self.run_completion()
        return self.clean_concepts(self.individuals[d0].concepts)

    def clean_concepts(self, concepts):
        cleaned_concepts = set()
        for concept in concepts:
            if concept[0] not in ['⊤', '⩾', '⩽', '(']:
                cleaned_concepts.add(concept)
        return cleaned_concepts