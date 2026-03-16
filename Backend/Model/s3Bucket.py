from Model.resource import Resource


class S3Bucket(Resource):
    def __init__(self, id, description, service, region, Creation_date, policies, versioning, encryption, public_access):
        super().__init__(id, description, service, region)
        self.Creation_date = Creation_date

        self.policies = policies
        self.versioning = versioning
        self.encryption = encryption
        self.public_access = public_access