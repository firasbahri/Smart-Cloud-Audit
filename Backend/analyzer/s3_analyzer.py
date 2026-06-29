import logging
from Model.vulnerability import Vulnerability

logger = logging.getLogger(__name__)


class S3Analyzer:
    """Reglas de seguridad estáticas para buckets S3: acceso público, versionado y cifrado."""

    def analyze(self, buckets: list) -> list:
        """Pasa los buckets por las tres comprobaciones y junta los resultados.

        Args:
            buckets (list): buckets S3 del modelo de dominio.

        Returns:
            list[Vulnerability]: unión de check_public_access, check_versioning y check_encryption.
        """
        vulnerabilities = []
        vulnerabilities.extend(self.check_public_access(buckets))
        vulnerabilities.extend(self.check_versioning(buckets))
        vulnerabilities.extend(self.check_encryption(buckets))
        return vulnerabilities


    def check_public_access(self, buckets) -> list:
        """Cruza la configuración de "block public access" con la política del bucket para decidir si está
        realmente expuesto, y con qué gravedad.

        Hay tres combinaciones posibles y cada una se reporta distinto:
        - política pública + nada de block public access -> Critical (ya es accesible desde fuera).
        - solo política pública, pero el bucket bloquea el acceso público -> Medium (la política sobra y es un riesgo
          latente si algún día se quita el bloqueo).
        - solo configuración de acceso público sin política explícita -> Medium.

        Args:
            buckets (list): buckets S3 con bucket_policy y public_access ya resueltos.

        Returns:
            list[Vulnerability]: como mucho un hallazgo por bucket (el caso más grave que aplique).
        """
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
        """Marca los buckets sin versionado habilitado (severidad Low: no es una puerta de entrada, pero sin
        versiones anteriores un borrado o sobrescritura accidental — o malintencionada — es irreversible)."""
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
        """Marca los buckets sin cifrado en reposo habilitado (severidad Medium)."""
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
        """True si la política del bucket tiene un statement 'Allow' con Principal "*" (o {"AWS": "*"}) — es decir,
        cualquiera, sin autenticar, puede hacer lo que ese statement permita.

        Args:
            policy (dict | None): documento de política del bucket (formato IAM policy), o None si no tiene.

        Returns:
            bool: False también si policy es None.
        """
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
        """True si falta cualquiera de los 4 bloqueos de "Block Public Access" de S3.

        Si public_access viene vacío/None se asume el peor caso (público) porque, sin esa info, no hay garantía
        de que el bucket esté protegido.

        Args:
            public_access (dict | None): BlockPublicAcls, IgnorePublicAcls, BlockPublicPolicy, RestrictPublicBuckets.

        Returns:
            bool: True si el bucket queda expuesto por al menos uno de los cuatro flags.
        """
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
