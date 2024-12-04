class Individual(object):
    def __init__(self, name):
        self.name = name
        self.initial_concept = None
        self.concepts = set()
        self.roles = set()

    def has_role(self, role):
        for r in self.roles:
            if role.relation == r.relation and role.successor == r.successor and role.individual == r.individual:
                return True
        return False
