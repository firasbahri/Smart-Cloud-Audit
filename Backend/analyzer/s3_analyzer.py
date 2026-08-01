import logging
from Model.vulnerability import Vulnerability

logger = logging.getLogger(__name__)

# AWS canonical URIs for public ACL grantee groups.
# Logic adapted from Prowler's s3_bucket_public_list_acl and s3_bucket_public_write_acl (Apache 2.0).
_PUBLIC_GROUP_URIS = {
    "http://acs.amazonaws.com/groups/global/AllUsers",
    "http://acs.amazonaws.com/groups/global/AuthenticatedUsers",
}
_WRITE_PERMISSIONS = {"WRITE", "WRITE_ACP", "FULL_CONTROL"}
_READ_PERMISSIONS = {"READ", "READ_ACP"}


class S3Analyzer:
    """Static security rules for S3 buckets: public access, versioning, encryption,
    ACL public grants, server access logging, object lock, and MFA delete."""

    def analyze(self, buckets: list) -> list:
        """Run all checks against the given buckets and return the combined findings.

        Args:
            buckets (list): S3 buckets from the domain model.

        Returns:
            list[Vulnerability]: union of all individual check results.
        """
        vulnerabilities = []
        vulnerabilities.extend(self.check_public_access(buckets))
        vulnerabilities.extend(self.check_versioning(buckets))
        vulnerabilities.extend(self.check_encryption(buckets))
        vulnerabilities.extend(self.check_acl_public_access(buckets))
        vulnerabilities.extend(self.check_logging_enabled(buckets))
        vulnerabilities.extend(self.check_object_lock(buckets))
        vulnerabilities.extend(self.check_mfa_delete(buckets))
        vulnerabilities.extend(self.check_secure_transport_policy(buckets))
        vulnerabilities.extend(self.check_replication_enabled(buckets))
        vulnerabilities.extend(self.check_lifecycle_configuration_enabled(buckets))
        vulnerabilities.extend(self.check_event_notifications_enabled(buckets))
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
                        name=f"S3 Bucket with Public Access and Public Policy: {bucket.name}",
                        description=(
                            f"S3 bucket '{bucket.name}' has a public bucket policy "
                            "and is publicly accessible from the internet."
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
                        name=f"S3 Bucket with Public Bucket Policy: {bucket.name}",
                        description=(
                            f"S3 bucket '{bucket.name}' has a public bucket policy, "
                            "although it is not publicly accessible due to the bucket's Block Public Access settings. "
                            "The policy is a latent risk if those settings are ever removed."
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
                        name=f"S3 Bucket with Public Access Enabled: {bucket.name}",
                        description=(
                            f"S3 bucket '{bucket.name}' has one or more Block Public Access controls disabled "
                            "and no explicit bucket policy restricting access, leaving it potentially exposed to the internet."
                        ),
                        severity="Medium",
                        resource_id=bucket.id,
                        resource_type="S3",
                    )
                )

        return vulnerabilities


    def check_versioning(self, buckets) -> list:
        """Marks buckets without versioning enabled (severity Low: not an entry point, but without
        previous versions an accidental or malicious deletion or overwrite is irreversible)."""
        Vulnerabilities = []
        for bucket in buckets:
            logger.info(f"Checking versioning for bucket {bucket.name} with versioning status: {bucket.versioning}")
            if not bucket.versioning or bucket.versioning == "Disabled":
                Vulnerabilities.append(
                    Vulnerability(
                        id=f"s3_{bucket.id}_versioning_disabled",
                        name=f"S3 Bucket Versioning Disabled: {bucket.name}",
                        description=(
                            f"S3 bucket '{bucket.name}' does not have versioning enabled, "
                            "which may result in irreversible data loss if objects are accidentally or maliciously deleted or overwritten."
                        ),
                        severity="Low",
                        resource_id=bucket.id,
                        resource_type="S3",
                    )
                )
        return Vulnerabilities

    def check_encryption(self, buckets) -> list:
        """Marks buckets without server-side encryption enabled at rest (severity Medium)."""
        Vulnerabilities = []
        for bucket in buckets:
            logger.info(f"Checking encryption for bucket {bucket.name} with encryption status: {bucket.encryption}")
            if not bucket.encryption:
                Vulnerabilities.append(
                    Vulnerability(
                        id=f"s3_{bucket.id}_encryption_disabled",
                        name=f"S3 Bucket Encryption Disabled: {bucket.name}",
                        description=(
                            f"S3 bucket '{bucket.name}' does not have server-side encryption enabled, "
                            "which may lead to data breaches and exposure of sensitive information if the storage layer is compromised."
                        ),
                        severity="Medium",
                        resource_id=bucket.id,
                        resource_type="S3",
                    )
                )
        return Vulnerabilities

    def check_acl_public_access(self, buckets: list) -> list:
        """Detects buckets whose ACL grants read or write access to public AWS groups.

        S3 bucket ACLs can grant permissions directly to the AWS canonical groups AllUsers
        (any unauthenticated internet user) and AuthenticatedUsers (any AWS account holder).
        These grants bypass the bucket policy and Block Public Access settings, meaning a bucket
        that appears locked down via policy can still be publicly readable or writable via ACL.
        Write access (WRITE, WRITE_ACP, FULL_CONTROL) allows anyone to upload or delete objects
        without any credentials, making it an immediate data-integrity and supply-chain risk.
        Read access (READ, READ_ACP) allows any internet user to list and download bucket contents.

        Buckets where acl_grantees is None are skipped (scans performed before this field was collected).

        Logic adapted from Prowler's s3_bucket_public_list_acl, s3_bucket_public_write_acl,
        and s3_bucket_acl_prohibited (Apache 2.0).

        Args:
            buckets (list): S3 buckets with the acl_grantees field already resolved.

        Returns:
            list[Vulnerability]: one entry per bucket — Critical if write access is granted,
            High if read-only access is granted to a public group.
        """
        vulnerabilities = []
        for bucket in buckets:
            if bucket.acl_grantees is None:
                continue

            has_public_write = False
            has_public_read = False
            write_perms_found = []
            read_perms_found = []

            for grantee in bucket.acl_grantees:
                if not isinstance(grantee, dict):
                    continue
                if grantee.get('type') != 'Group':
                    continue
                if grantee.get('uri') not in _PUBLIC_GROUP_URIS:
                    continue

                perm = grantee.get('permission', '')
                if perm in _WRITE_PERMISSIONS:
                    has_public_write = True
                    write_perms_found.append(perm)
                elif perm in _READ_PERMISSIONS:
                    has_public_read = True
                    read_perms_found.append(perm)

            if has_public_write:
                vulnerabilities.append(Vulnerability(
                    id=f"s3_{bucket.id}_acl_public_write",
                    name=f"S3 Bucket ACL Grants Public Write Access: {bucket.name}",
                    description=(
                        f"S3 bucket '{bucket.name}' has an ACL that grants write permissions "
                        f"({', '.join(write_perms_found)}) to a public AWS group. "
                        "Any internet user can upload, overwrite, or delete objects without authentication, "
                        "bypassing the bucket policy and Block Public Access settings. "
                        "This is an immediate data-integrity risk and a potential vector for malware distribution."
                    ),
                    severity="Critical",
                    resource_id=bucket.id,
                    resource_type="S3",
                ))
            elif has_public_read:
                vulnerabilities.append(Vulnerability(
                    id=f"s3_{bucket.id}_acl_public_read",
                    name=f"S3 Bucket ACL Grants Public Read Access: {bucket.name}",
                    description=(
                        f"S3 bucket '{bucket.name}' has an ACL that grants read permissions "
                        f"({', '.join(read_perms_found)}) to a public AWS group. "
                        "Any internet user can list and download bucket contents without authentication, "
                        "bypassing the bucket policy and Block Public Access settings."
                    ),
                    severity="High",
                    resource_id=bucket.id,
                    resource_type="S3",
                ))
        return vulnerabilities

    def check_logging_enabled(self, buckets: list) -> list:
        """Detects S3 buckets that do not have server access logging enabled.

        Server access logging records all requests made against the bucket, including the requester,
        operation, response status, and object key. Without it there is no audit trail to investigate
        data exfiltration, unauthorized access, or accidental deletions — making incident response
        and compliance audits (CIS AWS Foundations Benchmark 2.6) significantly harder.

        Buckets where logging is None are skipped (scans performed before this field was collected).

        Logic adapted from Prowler's s3_bucket_server_access_logging_enabled (Apache 2.0).

        Args:
            buckets (list): S3 buckets with the logging field already resolved.

        Returns:
            list[Vulnerability]: severity Medium, one entry per bucket without logging.
        """
        vulnerabilities = []
        for bucket in buckets:
            if bucket.logging is None:
                continue
            if not bucket.logging:
                vulnerabilities.append(Vulnerability(
                    id=f"s3_{bucket.id}_logging_disabled",
                    name=f"S3 Bucket Server Access Logging Disabled: {bucket.name}",
                    description=(
                        f"S3 bucket '{bucket.name}' does not have server access logging enabled. "
                        "Without it, there is no record of who accessed or modified objects, "
                        "which prevents forensic investigation after a data breach and fails "
                        "the CIS AWS Foundations Benchmark control 2.6."
                    ),
                    severity="Medium",
                    resource_id=bucket.id,
                    resource_type="S3",
                ))
        return vulnerabilities

    def check_object_lock(self, buckets: list) -> list:
        """Detects S3 buckets that do not have Object Lock enabled.

        Object Lock enforces a WORM (Write Once, Read Many) retention policy that prevents objects
        from being deleted or overwritten for a defined period, even by the bucket owner.
        Without it, a ransomware attack or a set of compromised credentials can permanently destroy
        all bucket contents — including backups — with no recovery path.

        Buckets where object_lock is None are skipped (scans performed before this field was collected).

        Logic adapted from Prowler's s3_bucket_object_lock (Apache 2.0).

        Args:
            buckets (list): S3 buckets with the object_lock field already resolved.

        Returns:
            list[Vulnerability]: severity Medium, one entry per bucket without Object Lock.
        """
        vulnerabilities = []
        for bucket in buckets:
            if bucket.object_lock is None:
                continue
            if not bucket.object_lock:
                vulnerabilities.append(Vulnerability(
                    id=f"s3_{bucket.id}_object_lock_disabled",
                    name=f"S3 Bucket Object Lock Not Enabled: {bucket.name}",
                    description=(
                        f"S3 bucket '{bucket.name}' does not have Object Lock enabled. "
                        "Without WORM protection, objects can be permanently deleted or overwritten "
                        "by anyone with write access to the bucket, including ransomware acting on "
                        "compromised credentials. Enabling Object Lock with Compliance mode prevents "
                        "deletion even by privileged users during the retention period."
                    ),
                    severity="Medium",
                    resource_id=bucket.id,
                    resource_type="S3",
                ))
        return vulnerabilities

    def check_mfa_delete(self, buckets: list) -> list:
        """Detects versioned S3 buckets that do not require MFA to permanently delete object versions.

        When versioning is enabled, deleting an object only creates a delete marker — the previous
        versions remain recoverable. However, permanently removing a version requires a separate API
        call. Without MFA Delete, any set of compromised AWS credentials can permanently purge the
        entire version history of the bucket, eliminating the recovery layer that versioning provides.
        With MFA Delete enabled, that API call additionally requires a hardware or virtual MFA token,
        so a credential compromise alone is insufficient to cause irreversible data loss.

        This check only applies when versioning is actively enabled ('Enabled'). Suspended or
        disabled versioning buckets are skipped, matching Prowler's condition.

        Buckets where mfa_delete is None are skipped (scans performed before this field was collected).

        Logic adapted from Prowler's s3_bucket_no_mfa_delete (Apache 2.0).

        Args:
            buckets (list): S3 buckets with the versioning and mfa_delete fields already resolved.

        Returns:
            list[Vulnerability]: severity High, one entry per versioned bucket without MFA Delete.
        """
        vulnerabilities = []
        for bucket in buckets:
            if bucket.versioning != "Enabled":
                continue
            if bucket.mfa_delete is None:
                continue
            if not bucket.mfa_delete:
                vulnerabilities.append(Vulnerability(
                    id=f"s3_{bucket.id}_mfa_delete_disabled",
                    name=f"S3 Bucket MFA Delete Not Enabled: {bucket.name}",
                    description=(
                        f"S3 bucket '{bucket.name}' has versioning enabled but does not require MFA "
                        "to permanently delete object versions. "
                        "Compromised AWS credentials are sufficient to irreversibly purge all version history, "
                        "negating the data recovery guarantee that versioning is meant to provide. "
                        "Enabling MFA Delete requires a second authentication factor for permanent deletions."
                    ),
                    severity="High",
                    resource_id=bucket.id,
                    resource_type="S3",
                ))
        return vulnerabilities

    def check_secure_transport_policy(self, buckets: list) -> list:
        """Detects S3 buckets that do not enforce HTTPS-only access via their bucket policy.

        Without a policy that denies requests over plain HTTP (aws:SecureTransport: false),
        data in transit is unencrypted if a client chooses not to use TLS. This enables
        man-in-the-middle attacks that intercept credentials or object contents in transit.
        The canonical fix is a bucket policy statement with Effect: Deny,
        Action: s3:*, Principal: *, Condition: {Bool: {aws:SecureTransport: false}}.

        Buckets without a policy, or whose policy contains no reference to SecureTransport,
        are flagged. Buckets where bucket_policy is None are skipped.

        Logic adapted from Prowler's s3_bucket_policy_ssl_requests_only (Apache 2.0).

        Args:
            buckets (list): S3 buckets with the bucket_policy field already resolved.

        Returns:
            list[Vulnerability]: severity Medium, one entry per bucket lacking a secure-transport policy.
        """
        vulnerabilities = []
        for bucket in buckets:
            if bucket.bucket_policy is None:
                continue

            has_secure_transport = False
            policy = bucket.bucket_policy if isinstance(bucket.bucket_policy, dict) else {}
            for statement in policy.get('Statement', []):
                condition = statement.get('Condition', {})
                for condition_op in condition.values():
                    if isinstance(condition_op, dict):
                        for key in condition_op:
                            if 'aws:securetransport' in key.lower():
                                has_secure_transport = True
                                break
                if has_secure_transport:
                    break

            if not has_secure_transport:
                vulnerabilities.append(Vulnerability(
                    id=f"s3_{bucket.id}_no_secure_transport_policy",
                    name=f"S3 Bucket Does Not Enforce HTTPS: {bucket.name}",
                    description=(
                        f"S3 bucket '{bucket.name}' does not have a bucket policy that enforces "
                        "HTTPS-only access (aws:SecureTransport condition). "
                        "Clients can access the bucket over plain HTTP, exposing data in transit "
                        "to interception via man-in-the-middle attacks. "
                        "Add a Deny statement with Condition: {Bool: {aws:SecureTransport: false}}."
                    ),
                    severity="Medium",
                    resource_id=bucket.id,
                    resource_type="S3",
                ))
        return vulnerabilities

    def check_replication_enabled(self, buckets: list) -> list:
        """Detects S3 buckets that have no cross-region or same-region replication rules configured.

        Replication creates copies of objects in one or more destination buckets, providing
        geographic redundancy and disaster recovery. Without it, a regional outage, accidental
        deletion, or ransomware attack on the source bucket leaves data with no replica to recover
        from in another location. This is particularly relevant for buckets that store backups or
        critical application state.

        Buckets where replication_rules is None are skipped (scans performed before this
        field was collected).

        Logic adapted from Prowler's s3_bucket_replication_enabled (Apache 2.0).

        Args:
            buckets (list): S3 buckets with the replication_rules field already resolved.

        Returns:
            list[Vulnerability]: severity Low, one entry per bucket with no replication rules.
        """
        vulnerabilities = []
        for bucket in buckets:
            if bucket.replication_rules is None:
                continue
            if not bucket.replication_rules:
                vulnerabilities.append(Vulnerability(
                    id=f"s3_{bucket.id}_replication_disabled",
                    name=f"S3 Bucket Replication Not Configured: {bucket.name}",
                    description=(
                        f"S3 bucket '{bucket.name}' has no replication rules configured. "
                        "Without cross-region or same-region replication, the bucket has no "
                        "geographic redundancy — a regional incident or ransomware event targeting "
                        "this bucket would result in unrecoverable data loss."
                    ),
                    severity="Low",
                    resource_id=bucket.id,
                    resource_type="S3",
                ))
        return vulnerabilities

    def check_lifecycle_configuration_enabled(self, buckets: list) -> list:
        """Detects S3 buckets that have no lifecycle configuration rules.

        Lifecycle rules automate transitions (e.g. moving objects to Glacier) and expiration of
        objects and incomplete multipart uploads. Without lifecycle rules, buckets accumulate
        objects indefinitely — including stale temporary files, old log entries, or incomplete
        multipart uploads (which incur storage cost but are invisible in object listings).
        Stale data also increases the blast radius if the bucket is compromised: an attacker
        can exfiltrate years of data rather than just recent content.

        Buckets where lifecycle is None are skipped (scans performed before this field was collected).

        Logic adapted from Prowler's s3_bucket_lifecycle_configuration_enabled (Apache 2.0).

        Args:
            buckets (list): S3 buckets with the lifecycle field already resolved.

        Returns:
            list[Vulnerability]: severity Low, one entry per bucket without lifecycle rules.
        """
        vulnerabilities = []
        for bucket in buckets:
            if bucket.lifecycle is None:
                continue
            if not bucket.lifecycle:
                vulnerabilities.append(Vulnerability(
                    id=f"s3_{bucket.id}_no_lifecycle_policy",
                    name=f"S3 Bucket Has No Lifecycle Configuration: {bucket.name}",
                    description=(
                        f"S3 bucket '{bucket.name}' has no lifecycle rules configured. "
                        "Without lifecycle management, objects and incomplete multipart uploads "
                        "accumulate indefinitely, increasing storage costs and the volume of "
                        "data exposed if the bucket is ever compromised."
                    ),
                    severity="Low",
                    resource_id=bucket.id,
                    resource_type="S3",
                ))
        return vulnerabilities

    def check_event_notifications_enabled(self, buckets: list) -> list:
        """Detects S3 buckets that have no event notification configuration.

        Event notifications alert downstream systems (Lambda, SNS, SQS) when specific operations
        occur on a bucket (e.g. object creation, deletion, restore). Without them there is no
        mechanism to trigger automated detection or response workflows for potentially malicious
        operations — such as an unexpected large-scale object deletion or an upload of an
        executable — reducing the ability to detect incidents in real time.

        Buckets where notification_config is None are skipped (scans performed before this
        field was collected).

        Logic adapted from Prowler's s3_bucket_event_notifications_enabled (Apache 2.0).

        Args:
            buckets (list): S3 buckets with the notification_config field already resolved.

        Returns:
            list[Vulnerability]: severity Low, one entry per bucket without event notifications.
        """
        vulnerabilities = []
        for bucket in buckets:
            if bucket.notification_config is None:
                continue
            config = bucket.notification_config
            if not isinstance(config, dict):
                continue
            has_any_notification = (
                config.get('LambdaFunctionConfigurations')
                or config.get('QueueConfigurations')
                or config.get('TopicConfigurations')
            )
            if not has_any_notification:
                vulnerabilities.append(Vulnerability(
                    id=f"s3_{bucket.id}_no_event_notifications",
                    name=f"S3 Bucket Has No Event Notifications: {bucket.name}",
                    description=(
                        f"S3 bucket '{bucket.name}' has no event notification configuration. "
                        "Without notifications, there is no real-time signal when objects are "
                        "created, deleted, or modified — making it impossible to trigger automated "
                        "detection or response workflows for suspicious operations on this bucket."
                    ),
                    severity="Low",
                    resource_id=bucket.id,
                    resource_type="S3",
                ))
        return vulnerabilities

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
