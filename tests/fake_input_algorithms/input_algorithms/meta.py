class Meta(object):
    def __init__(self, everything, path):
        self.path = path
        self.everything = everything

    def at(self, part):
        self.path.append(part)
        return self
