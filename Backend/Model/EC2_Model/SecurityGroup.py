
class SecurityGroup:
    def __init__(self,id, rules):
        self.id = id
        self.rules = rules

    def get_id(self):
        return self.id