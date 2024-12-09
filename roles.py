from individual import Individual


class Role(object):
    def __init__(self, relation, successor: Individual):
        self.relation = relation
        self.successor = successor
