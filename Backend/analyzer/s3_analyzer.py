import logging
from Model.vulnerability import Vulnerability

logger = logging.getLogger(__name__)


class S3Analyzer:
    def analyze(self, buckets: list) -> list:
        vulnerabilities = []
        vulnerabilities.extend(self.check_public_access(buckets))
        vulnerabilities.extend(self.check_versioning(buckets))
        vulnerabilities.extend(self.check_encryption(buckets))
        return vulnerabilities


    def check_public_access(self, buckets) -> list:
        vulnerabilities = []
        logger.info(f"Checking public access for {len(buckets)} buckets")
        for bucket in buckets:
            logger.info(f"Analyzing bucket {bucket.name} with id {bucket.id}")
            logger.info(f"Bucket policy: {bucket.bucket_policy}")
            logger.info(f"Bucket public access settings: {bucket.public_access}")
            if self.isPublicAccess(bucket.public_access) and self.isPublicBucketPolicy(bucket.bucket_policy):
                vulnerabilities.append(
                    Vulnerability(
                        id=f"s3_{bucket.id}_public_access_policy_and_public_access",
                        name=f"Acceso Público al Bucket S3 {bucket.name}",
                        description=(
                            f"El bucket S3 '{bucket.name}' tiene una política de acceso público "
                            "y es accesible públicamente desde internet."
                        ),
                        severity="Critical",
                        resource_id=bucket.id,
                        resource_type="S3",
                    )
                )
            elif self.isPublicBucketPolicy(bucket.bucket_policy):
                vulnerabilities.append(
                    Vulnerability(
                        id=f"s3_{bucket.id}_public_policy_only",
                        name=f"Política Pública en el Bucket S3 {bucket.name}",
                        description=(
                            f"El bucket S3 '{bucket.name}' tiene una política de acceso público, "
                            "aunque no es accesible públicamente debido a la configuración del bucket."
                        ),
                        severity="Medium",
                        resource_id=bucket.id,
                        resource_type="S3",
                    )
                )
            elif self.isPublicAccess(bucket.public_access):
                vulnerabilities.append(
                    Vulnerability(
                        id=f"s3_{bucket.id}_public_access_only",
                        name=f"Acceso Público al Bucket S3 {bucket.name}",
                        description=(
                            f"El bucket S3 '{bucket.name}' es accesible públicamente "
                            "pero no tiene ninguna política de acceso público definida."
                        ),
                        severity="Medium",
                        resource_id=bucket.id,
                        resource_type="S3",
                    )
                )

        return vulnerabilities


    def check_versioning(self, buckets) -> list:
        Vulnerabilities = []
        for bucket in buckets:
            logger.info(f"Checking versioning for bucket {bucket.name} with versioning status: {bucket.versioning}")
            if not bucket.versioning or bucket.versioning == "Disabled":
                Vulnerabilities.append(
                    Vulnerability(
                        id=f"s3_{bucket.id}_versioning_disabled",
                        name=f"Versionado Deshabilitado en el Bucket S3 {bucket.name}",
                        description=(
                            f"El bucket S3 '{bucket.name}' no tiene el versionado habilitado, "
                            "lo que puede provocar pérdida irreversible de datos."
                        ),
                        severity="Low",
                        resource_id=bucket.id,
                        resource_type="S3",
                    )
                )
        return Vulnerabilities

    def check_encryption(self, buckets) -> list:
        Vulnerabilities = []
        for bucket in buckets:
            logger.info(f"Checking encryption for bucket {bucket.name} with encryption status: {bucket.encryption}")
            if not bucket.encryption:
                Vulnerabilities.append(
                    Vulnerability(
                        id=f"s3_{bucket.id}_encryption_disabled",
                        name=f"Cifrado Deshabilitado en el Bucket S3 {bucket.name}",
                        description=(
                            f"El bucket S3 '{bucket.name}' no tiene el cifrado habilitado, "
                            "lo que puede provocar brechas de seguridad y exposición de datos sensibles."
                        ),
                        severity="Medium",
                        resource_id=bucket.id,
                        resource_type="S3",
                    )
                )
        return Vulnerabilities

    def isPublicBucketPolicy(self, policy) -> bool:
        if not policy:
            return False
        logger.info(f"Analyzing bucket policy and going to statements: {policy}")
        policy_statements = policy.get("Statement", [])
        for statement in policy_statements:
            logger.info(f"Analyzing policy statement: {statement}")
            if statement.get("Effect") == "Allow":
                principal = statement.get("Principal", {})
                if principal == "*":
                    return True
                if isinstance(principal, dict):
                    if principal.get("AWS") == "*":
                        return True
        return False

    def isPublicAccess(self, public_access) -> bool:
        if not public_access:
            return True
        try:
            blockPublicAcls = public_access.get("BlockPublicAcls", False)
            ignorePublicAcls = public_access.get("IgnorePublicAcls", False)
            blockPublicPolicy = public_access.get("BlockPublicPolicy", False)
            restrictPublicBuckets = public_access.get("RestrictPublicBuckets", False)
        except Exception as e:
            logger.error(f"Error parsing public access settings: {e}")
            return True

        if not blockPublicAcls or not ignorePublicAcls or not blockPublicPolicy or not restrictPublicBuckets:
            logger.info(f"Bucket is publicly accessible due to settings: BlockPublicAcls={blockPublicAcls}, IgnorePublicAcls={ignorePublicAcls}, BlockPublicPolicy={blockPublicPolicy}, RestrictPublicBuckets={restrictPublicBuckets}")
            return True

        return False
