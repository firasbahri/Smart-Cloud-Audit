import base64
import logging
import re
import zlib
from Model.vulnerability import Vulnerability

logger = logging.getLogger(__name__)

# port → (slug, display_name, risk_note)
# Logic adapted from Prowler's ec2_securitygroup_allow_ingress_from_internet_to_tcp_port_* checks (Apache 2.0).
_DANGEROUS_PORTS = {
    22:    ('ssh',           'SSH',           'remote shell access to the operating system'),
    23:    ('telnet',        'Telnet',        'unencrypted remote access — transmits credentials in plaintext'),
    25:    ('smtp',          'SMTP',          'mail relay — can enable spam and phishing abuse'),
    3389:  ('rdp',           'RDP',           'Windows Remote Desktop — direct GUI access to the OS'),
    1433:  ('mssql',         'MSSQL',         'Microsoft SQL Server database'),
    3306:  ('mysql',         'MySQL',         'MySQL / MariaDB database'),
    5432:  ('postgresql',    'PostgreSQL',    'PostgreSQL database'),
    6379:  ('redis',         'Redis',         'Redis cache/database — no authentication by default'),
    9200:  ('elasticsearch', 'Elasticsearch', 'Elasticsearch REST API — indexes may contain sensitive data'),
    27017: ('mongodb',       'MongoDB',       'MongoDB database — no authentication by default in older versions'),
}

# Patterns for common secrets in EC2 user data.
# Logic adapted from Prowler's ec2_instance_secrets_user_data (Apache 2.0).
_SECRET_PATTERNS = [
    re.compile(r'AKIA[0-9A-Z]{16}'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'(?i)(?:password|passwd|pwd)\s*=\s*\S+'),
    re.compile(r'(?i)(?:secret|token|api[_\-]?key)\s*=\s*[A-Za-z0-9/+]{20,}'),
]


class EC2Analyzer:
    """Static security rules for EC2 instances: public IP, open ports, unencrypted EBS, tagging,
    IMDSv2 enforcement, user-data secrets, detailed monitoring, and virtualization type."""

    def analyze(self, instances: list) -> list:
        """Run all checks against the given instances and return the combined findings.

        Args:
            instances (list): EC2 instances from the domain model, with security_groups and volumes resolved.

        Returns:
            list[Vulnerability]: union of all individual check results.
        """
        vulnerabilities = []
        vulnerabilities.extend(self.check_public_ip(instances))
        vulnerabilities.extend(self.check_security_groups(instances))
        vulnerabilities.extend(self.check_ebs_encryption(instances))
        vulnerabilities.extend(self.check_tags(instances))
        vulnerabilities.extend(self.check_imdsv2(instances))
        vulnerabilities.extend(self.check_user_data_secrets(instances))
        vulnerabilities.extend(self.check_detailed_monitoring(instances))
        vulnerabilities.extend(self.check_virtualization_type(instances))
        return vulnerabilities

    def check_public_ip(self, instances: list) -> list:
        """Marks instances that have a public IP assigned (severity Medium: widens the attack surface,
        though it does not by itself mean a port is open)."""
        vulnerabilities = []
        for instance in instances:
            if instance.public_ip is not None:
                vulnerabilities.append(Vulnerability(
                    id=f"ec2_{instance.id}_public_ip",
                    name="EC2 Instance with Public IP",
                    description=(
                        f"EC2 instance '{instance.id}' has a public IP address ({instance.public_ip}), "
                        "which exposes it directly to the internet and increases the attack surface."
                    ),
                    severity="Medium",
                    resource_id=instance.id,
                    resource_type="EC2 Instance",
                ))
        return vulnerabilities


    def check_security_groups(self, instances: list) -> list:
        """Scans security group inbound TCP rules for dangerous ports open to 0.0.0.0/0.

        Covers remote access ports (SSH, RDP, Telnet) and database ports (MySQL, PostgreSQL,
        Redis, MongoDB, MSSQL, Elasticsearch). A rule matches when the dangerous port falls
        anywhere within the rule's [from_port, to_port] range, so catch-all rules (0–65535)
        are also detected.

        Args:
            instances (list): EC2 instances with security_groups -> rules already resolved.

        Returns:
            list[Vulnerability]: severity High, one entry per (instance, sg, port) combination
            open to the internet.
        """
        vulnerabilities = []
        for instance in instances:
            for sg in instance.security_groups:
                for rule in sg.rules:
                    if rule.protocol != "tcp":
                        continue
                    if "0.0.0.0/0" not in rule.ip_ranges:
                        continue
                    try:
                        from_port = int(rule.from_port)
                        to_port = int(rule.to_port)
                    except (TypeError, ValueError):
                        continue
                    for port, (slug, service, risk_note) in _DANGEROUS_PORTS.items():
                        if from_port <= port <= to_port:
                            vulnerabilities.append(Vulnerability(
                                id=f"ec2_{instance.id}_sg_{sg.id}_open_{slug}",
                                name=f"EC2 Instance with {service} Port Open to the Internet",
                                description=(
                                    f"EC2 instance '{instance.id}' has security group '{sg.id}' "
                                    f"allowing inbound TCP port {port} ({service}) from any IP address (0.0.0.0/0). "
                                    f"This exposes {risk_note} directly to the internet."
                                ),
                                severity="High",
                                resource_id=instance.id,
                                resource_type="EC2 Instance",
                            ))
        return vulnerabilities


    def check_ebs_encryption(self, instances: list) -> list:
        """Detects unencrypted EBS volumes (Encrypted=False). If the physical volume is compromised
        or cloned, the data is readable without any credentials.

        Args:
            instances (list): EC2 instances with the volumes list already resolved (volume_id + encrypted).

        Returns:
            list[Vulnerability]: one entry per unencrypted volume found, severity Medium.
        """
        vulnerabilities = []
        for instance in instances:
            for volume in instance.volumes:
                logger.info(f"volumes of instance {instance.id}: {volume}")
                if volume["encrypted"] == False:
                    vulnerabilities.append(Vulnerability(
                        id=f"ec2_{instance.id}_ebs_{volume['volume_id']}_unencrypted",
                        name="EC2 Instance with Unencrypted EBS Volume",
                        description=(
                            f"EC2 instance '{instance.id}' has an attached EBS volume '{volume['volume_id']}' "
                            "that is not encrypted, which may lead to data exposure if the volume is compromised."
                        ),
                        severity="Medium",
                        resource_id=instance.id,
                        resource_type="EC2 Instance",
                    ))
        return vulnerabilities


    def check_imdsv2(self, instances: list) -> list:
        """Detects instances where the Instance Metadata Service (IMDS) does not enforce IMDSv2.

        The EC2 metadata endpoint (169.254.169.254) exposes temporary credentials for the IAM role
        attached to the instance. If http_tokens='optional', any application running inside the
        instance can read those credentials with a plain unauthenticated HTTP request.
        An attacker exploiting an SSRF vulnerability in the application can use those credentials
        to move laterally within the AWS account. With IMDSv2 (http_tokens='required'), the request
        requires a prior session token that cannot be obtained via SSRF, eliminating that attack vector.

        Instances where the field is not available (http_tokens=None) are skipped — they correspond
        to scans performed before this check was added.

        Args:
            instances (list): EC2 instances with the http_tokens field already resolved.

        Returns:
            list[Vulnerability]: severity High, one entry per instance without IMDSv2 enforced.
        """
        vulnerabilities = []
        for instance in instances:
            if instance.http_tokens is None:
                continue
            if instance.http_tokens != 'required':
                vulnerabilities.append(Vulnerability(
                    id=f"ec2_{instance.id}_imdsv2_not_required",
                    name="EC2 Instance without IMDSv2 Enforced",
                    description=(
                        f"EC2 instance '{instance.id}' has the Instance Metadata Service (IMDS) configured "
                        f"as '{instance.http_tokens}', allowing unauthenticated HTTP requests to the metadata "
                        "endpoint at 169.254.169.254 to retrieve the attached IAM role credentials. "
                        "An attacker exploiting an SSRF vulnerability in the application could use those "
                        "credentials to operate within the AWS account. "
                        "Setting http_tokens='required' enforces IMDSv2 and blocks this attack vector."
                    ),
                    severity="High",
                    resource_id=instance.id,
                    resource_type="EC2 Instance",
                ))
        return vulnerabilities

    def check_tags(self, instances: list) -> list:
        """Checks that each instance has the Name, Environment and Owner tags. Not a direct security
        risk, but without those tags it is easy to lose track of which resource belongs to whom (severity Low).
        """
        vulnerabilities = []
        REQUIRED_TAGS = ["Name", "Environment", "Owner"]
        for instance in instances:
            tags_keys = [tag['Key'] for tag in instance.tags]
            missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags_keys]
            if missing_tags:
                vulnerabilities.append(Vulnerability(
                    id=f"ec2_{instance.id}_missing_tags",
                    name="EC2 Instance with Missing Tags",
                    description=(
                        f"EC2 instance '{instance.id}' is missing required tags ({', '.join(missing_tags)}), "
                        "which may hinder effective resource management and identification."
                    ),
                    severity="Low",
                    resource_id=instance.id,
                    resource_type="EC2 Instance",
                ))
        return vulnerabilities

    def check_user_data_secrets(self, instances: list) -> list:
        """Scans the EC2 user-data script for hardcoded secrets using regex patterns.

        User data is the startup script passed to an instance at launch. It is retrievable via the
        AWS API by anyone with ec2:DescribeInstanceAttribute permissions and is often stored in
        plaintext, making hardcoded passwords, API keys or private keys easily extractable.
        The check base64-decodes the stored value (as returned by the AWS API) and decompresses
        it if GZIP-encoded before scanning.

        Terminated instances and instances with no user_data are skipped. Instances where
        user_data is None are also skipped (scans performed before this field was collected).

        Logic adapted from Prowler's ec2_instance_secrets_user_data (Apache 2.0).

        Args:
            instances (list): EC2 instances with the user_data field already resolved.

        Returns:
            list[Vulnerability]: severity High, one entry per instance where a secret pattern matches.
        """
        vulnerabilities = []
        for instance in instances:
            if instance.state == "terminated":
                continue
            if instance.user_data is None:
                continue

            try:
                raw = base64.b64decode(instance.user_data)
            except Exception:
                raw = instance.user_data.encode("utf-8", errors="replace")

            if raw[:2] == b"\x1f\x8b":
                try:
                    raw = zlib.decompress(raw, zlib.MAX_WBITS | 32)
                except Exception:
                    pass

            text = raw.decode("utf-8", errors="replace")

            matched_patterns = [p.pattern for p in _SECRET_PATTERNS if p.search(text)]
            if matched_patterns:
                vulnerabilities.append(Vulnerability(
                    id=f"ec2_{instance.id}_user_data_secrets",
                    name="EC2 Instance with Potential Secrets in User Data",
                    description=(
                        f"EC2 instance '{instance.id}' has a user-data script that matches patterns "
                        "associated with hardcoded secrets (e.g. AWS access keys, private keys, passwords "
                        "or API tokens). User data is retrievable by anyone with "
                        "ec2:DescribeInstanceAttribute permissions and should never contain credentials."
                    ),
                    severity="High",
                    resource_id=instance.id,
                    resource_type="EC2 Instance",
                ))
        return vulnerabilities

    def check_detailed_monitoring(self, instances: list) -> list:
        """Detects EC2 instances that do not have detailed CloudWatch monitoring enabled.

        Without detailed monitoring, CloudWatch collects metrics at 5-minute intervals instead of
        1-minute intervals. This reduces the resolution of security-relevant signals (CPU spikes,
        network anomalies) and makes it harder to detect and correlate incidents in real time.

        Instances where monitoring_state is None are skipped (scans performed before this
        field was collected).

        Logic adapted from Prowler's ec2_instance_detailed_monitoring_enabled (Apache 2.0).

        Args:
            instances (list): EC2 instances with the monitoring_state field already resolved.

        Returns:
            list[Vulnerability]: severity Medium, one entry per instance without detailed monitoring.
        """
        vulnerabilities = []
        for instance in instances:
            if instance.monitoring_state is None:
                continue
            if instance.monitoring_state != "enabled":
                vulnerabilities.append(Vulnerability(
                    id=f"ec2_{instance.id}_detailed_monitoring_disabled",
                    name="EC2 Instance without Detailed Monitoring",
                    description=(
                        f"EC2 instance '{instance.id}' has detailed CloudWatch monitoring in state "
                        f"'{instance.monitoring_state}'. Without it, metrics are collected every 5 minutes "
                        "instead of every minute, reducing the ability to detect and respond to security "
                        "incidents in real time."
                    ),
                    severity="Medium",
                    resource_id=instance.id,
                    resource_type="EC2 Instance",
                ))
        return vulnerabilities

    def check_virtualization_type(self, instances: list) -> list:
        """Detects EC2 instances using paravirtual (PV) virtualization instead of HVM.

        Paravirtual virtualization is a legacy type that relies on a modified guest OS and offers
        weaker hardware isolation than HVM. PV instances cannot benefit from enhanced networking,
        GPU, or NVMe instance types and receive fewer security patches from AWS. HVM is the
        current standard and should be used for all new workloads.

        Terminated instances and instances where virtualization_type is None are skipped.

        Logic adapted from Prowler's ec2_instance_paravirtual_type (Apache 2.0).

        Args:
            instances (list): EC2 instances with the virtualization_type field already resolved.

        Returns:
            list[Vulnerability]: severity Medium, one entry per PV instance found.
        """
        vulnerabilities = []
        for instance in instances:
            if instance.state == "terminated":
                continue
            if instance.virtualization_type is None:
                continue
            if instance.virtualization_type == "paravirtual":
                vulnerabilities.append(Vulnerability(
                    id=f"ec2_{instance.id}_paravirtual_type",
                    name="EC2 Instance Using Paravirtual Virtualization",
                    description=(
                        f"EC2 instance '{instance.id}' uses paravirtual (PV) virtualization, which is a "
                        "legacy type with weaker hardware isolation compared to HVM. PV instances do not "
                        "support enhanced networking or modern instance types and receive limited security "
                        "updates from AWS. Migrate to an HVM instance type."
                    ),
                    severity="Medium",
                    resource_id=instance.id,
                    resource_type="EC2 Instance",
                ))
        return vulnerabilities
