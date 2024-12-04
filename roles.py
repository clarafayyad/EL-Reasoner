class Role (object):
    def __init__(self, relation, successor, individual):
        self.relation = relation
        self.successor = successor
        self.individual = individual

    def __str__(self):
        return "∃" + self.relation + "." + self.successor