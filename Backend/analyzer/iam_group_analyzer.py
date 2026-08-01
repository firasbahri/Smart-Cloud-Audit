import logging

from Model.vulnerability import Vulnerability
from analyzer._iam_helpers import is_admin, has_wildcard_permissions

logger = logging.getLogger(__name__)


class IAMGroupAnalyzer:
    """Static security rules for IAM groups: excessive managed permissions and wildcard inline policies."""

    def analyze(self, groups: list) -> list:
        """Run all group checks and return the combined findings.

        Args:
            groups (list): IAM groups from the domain model.

        Returns:
            list[Vulnerability]: union of all individual check results.
        """
        vulnerabilities = []
        vulnerabilities.extend(self.check_group_permissions(groups))
        return vulnerabilities

    def check_group_permissions(self, groups: list) -> list:
        """Marks groups with AdministratorAccess or an inline policy that combines action and
        resource wildcards (*). Risk here affects every member of the group simultaneously.

        Args:
            groups (list): IAM groups with managed_policies and inline_policies already resolved.

        Returns:
            list[Vulnerability]: severity Critical, one entry per excessive-permission finding.
        """
        vulnerabilities = []
        logger.info(f"Checking permissions for {len(groups)} groups")
        for group in groups:
            logger.info(f"Group {group.name}: managed={group.managed_policies}, inline={group.inline_policies}")
            if is_admin(group.managed_policies):
                logger.info(f"Group {group.name} has AdministratorAccess managed policy")
                vulnerabilities.append(Vulnerability(
                    id=f"iam_group_{group.id}_managed_admin",
                    name="IAM Group with AdministratorAccess Managed Policy",
                    description=(
                        f"IAM group '{group.name}' has the 'AdministratorAccess' managed policy attached, "
                        "which grants full access to all AWS services and resources to all users in the group."
                    ),
                    severity="Critical",
                    resource_id=group.id,
                    resource_type="IAM Group",
                ))

            wildcard_policies = has_wildcard_permissions(group.inline_policies)
            for p_name in wildcard_policies:
                logger.info(f"Group {group.name} has inline policy {p_name} with wildcard permissions")
                vulnerabilities.append(Vulnerability(
                    id=f"iam_group_{group.id}_inline_{p_name}_wildcard",
                    name=f"IAM Group with Wildcard Permissions in Inline Policy {p_name}",
                    description=(
                        f"IAM group '{group.name}' has an inline policy '{p_name}' that allows wildcard permissions, "
                        "which may result in excessive privileges and security risks for all users in the group."
                    ),
                    severity="Critical",
                    resource_id=group.id,
                    resource_type="IAM Group",
                ))
        return vulnerabilities
