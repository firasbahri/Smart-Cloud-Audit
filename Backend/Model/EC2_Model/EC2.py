

from ..resource import Resource

class EC2(Resource):
    def __init__(self,id,name,service,region,date,instance_type ,state,security_groups,volumes):
        super().__init__(id,name,service,region,date)
        self.instance_type = instance_type
        self.state = state
        self.security_groups = security_groups
        self.volumes = volumes