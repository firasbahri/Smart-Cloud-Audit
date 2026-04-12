import logging
from Model.vulnerability import Vulnerability

logger = logging.getLogger(__name__)


class EC2Analyzer:
    def analyze(self, instances: list) -> list:
        vulnerabilities = []
        vulnerabilities.extend(self.check_public_ip(instances))
        vulnerabilities.extend(self.check_security_groups(instances))
        return vulnerabilities

    def check_public_ip(self, instances: list) -> list:
        vulnerabilities = []
        for instance in instances:
            if instance.public_ip is not None:
                vulnerabilities.append(Vulnerability(
                    id=f"ec2_{instance.id}_public_ip",
                    name="EC2 Instance with Public IP",
                    description=(
                        f"The EC2 instance '{instance.id}' has a public IP address ({instance.public_ip}), "
                        "which exposes it directly to the internet and increases the attack surface."
                    ),
                    severity="Medium",
                    resource_id=instance.id,
                    resource_type="EC2 Instance",
                    origin="Static Analysis",
                ))
        return vulnerabilities


    def check_security_groups(self, instances: list) -> list:
        Vulnerabilities = []
        for instance in instances:
            for sg in instance.security_groups:
                for rule in sg.rules:
                    if rule.protocol == "tcp" and rule.from_port == 22 and rule.to_port == 22:
                        for ip_range in rule.ip_ranges:
                            if ip_range == "0.0.0.0/0":
                                Vulnerabilities.append(Vulnerability(
                                    id=f"ec2_{instance.id}_sg_{sg.id}_open_ssh",
                                    name="EC2 Instance with Open SSH Port",
                                    description=(
                                        f"The EC2 instance '{instance.id}' has a security group '{sg.id}' that allows open SSH access from any IP address."
                                    ),
                                    severity="High",
                                    resource_id=instance.id,
                                    resource_type="EC2 Instance",
                                    origin="Static Analysis",
                                ))
                    if rule.protocol == "tcp" and rule.from_port == 3389 and rule.to_port == 3389:
                        for ip_range in rule.ip_ranges:
                            if ip_range == "0.0.0.0/0":
                                Vulnerabilities.append(Vulnerability(
                                    id=f"ec2_{instance.id}_sg_{sg.id}_open_rdp",
                                    name="EC2 Instance with Open RDP Port",
                                    description=(
                                        f"The EC2 instance '{instance.id}' has a security group '{sg.id}' that allows open RDP access from any IP address."
                                    ),
                                    severity="High",
                                    resource_id=instance.id,
                                    resource_type="EC2 Instance",
                                    origin="Static Analysis",
                                ))
        return Vulnerabilities  
