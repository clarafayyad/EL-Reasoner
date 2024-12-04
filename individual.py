class Individual(object):
    def __init__(self, name):
        self.name = name
        self.initial_concept = None
        self.concepts = set()
        self.roles = set()

