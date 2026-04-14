import logging
from Model.vulnerability import Vulnerability

logger = logging.getLogger(__name__)


class S3Analyzer:
    def analyze(self, buckets: list) -> list:
        vulnerabilities = []
        vulnerabilities.extend(self.check_public_access(buckets))
        return vulnerabilities




    def check_public_access(self, buckets) -> list:
        vulnerabilities = []
        for bucket in buckets:
            if self.isPublicAccess(bucket) and self.isPublicBucketPolicy(bucket.bucket_policy):
                vulnerabilities.append(
                    Vulnerability(
                        id=f"s3_{bucket.id}_public_access_policy_and_public_access",
                        name=f"Public Access to S3 Bucket {bucket.name}",
                        description=f"The S3 bucket {bucket.name} has a public access policy and is publicly accessible.",
                        severity="Critical",
                        resource_id=bucket.id,
                        service="S3",
                        region=bucket.region,
                    )
                )
            elif self.isPublicBucketPolicy(bucket.bucket_policy):
                vulnerabilities.append(
                    Vulnerability(
                        id=f"s3_{bucket.id}_public_policy_only",
                        name=f"Public Policy on S3 Bucket {bucket.name}",
                        description=f"The S3 bucket {bucket.name} has a public access policy but is not publicly accessible due to bucket settings.",
                        severity="Medium",
                        resource_id=bucket.id,
                        service="S3",
                        region=bucket.region,
                    )
                )
            elif self.isPublicAccess(bucket):
                vulnerabilities.append(
                    Vulnerability(
                        id=f"s3_{bucket.id}_public_access_only",
                        name=f"Public Access to S3 Bucket {bucket.name}",
                        description=f"The S3 bucket {bucket.name} is publicly accessible but does not have a public access policy.",
                        severity="Medium",
                        resource_id=bucket.id,
                        service="S3",
                        region=bucket.region,
                    )
                )
        return vulnerabilities
    

    def isPublicBucketPolicy(self, policy) -> bool:
        policy_statements = policy.get("Statement", [])
        for statement in policy_statements:
            if statement.get("Effect") == "Allow":
                principal = statement.get("Principal", {})
                if principal == "*" :
                    return True
                if isinstance(principal, dict):
                    if principal.get("AWS") == "*" :
                        return True
        return False
    
    def isPublicAccess(self, bucket) -> bool:
        if not bucket.public_access:
            return True
        
        blockPublicAcls = bucket.public_access.get("BlockPublicAcls", False)
        ignorePublicAcls = bucket.public_access.get("IgnorePublicAcls", False)
        blockPublicPolicy = bucket.public_access.get("BlockPublicPolicy", False)
        restrictPublicBuckets = bucket.public_access.get("RestrictPublicBuckets", False)

        if not blockPublicAcls or not ignorePublicAcls or not blockPublicPolicy or not restrictPublicBuckets:
            return True
        
        return False

    