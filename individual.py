class Individual(object):
    def __init__(self, name):
        self.name = name
        self.initial_concept = None
        self.concepts = set()
        self.roles = set()

    def has_role(self, relation, successor):
        for role in self.roles:
            if role.relation != relation:
                continue
            if role.successor.name == successor.name:
                return True
        return False

