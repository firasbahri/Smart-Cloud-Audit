from Model.resource import Resource


class S3Bucket(Resource):
    def __init__(self, id, name, service, region, Creation_date, bucket_policy, versioning, encryption, public_access):
        super().__init__(id, name, service, region, Creation_date)
        self.bucket_policy = bucket_policy
        self.versioning = versioning
        self.encryption = encryption
        self.public_access = public_access