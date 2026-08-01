import logging

from Model.vulnerability import Vulnerability
from analyzer._iam_helpers import is_admin, has_wildcard_permissions

logger = logging.getLogger(__name__)

# IAM actions that enable privilege escalation when applied to resource "*".
# A role with any of these actions and no permissions boundary can create new
# admin roles/policies, effectively bypassing its own permission limits.
_IAM_ESCALATION_ACTIONS = {
    'iam:*', '*',
    'iam:CreateRole', 'iam:AttachRolePolicy', 'iam:PutRolePolicy',
    'iam:CreateUser', 'iam:AddUserToGroup',
    'iam:CreatePolicyVersion', 'iam:SetDefaultPolicyVersion', 'iam:PutUserPolicy',
}


class IAMRoleAnalyzer:
    """Static security rules for IAM roles: excessive permissions, trusted-entity escalation,
    and privilege escalation via missing permissions boundaries."""

    def analyze(self, roles: list) -> list:
        """Run all role checks and return the combined findings.

        Args:
            roles (list): IAM roles from the domain model.

        Returns:
            list[Vulnerability]: union of all individual check results.
        """
        vulnerabilities = []
        vulnerabilities.extend(self.check_role_permissions(roles))
        vulnerabilities.extend(self.check_role_privilege_escalation_no_boundary(roles))
        return vulnerabilities

    def check_role_permissions(self, roles: list) -> list:
        """Checks for excessive permissions in IAM roles, escalating severity when the role
        is assumable by an external entity (trusted_entities).

        An externally-assumable admin role means someone outside the account can enter with
        full permissions — it is no longer just "broad internal permissions" but a direct
        external attack surface.

        Args:
            roles (list): IAM roles with managed_policies, inline_policies, and trusted_entities
                          already resolved.

        Returns:
            list[Vulnerability]: Medium/High for internal-only roles, Critical if external
            trusted entities are involved.
        """
        vulnerabilities = []
        for role in roles:
            if is_admin(role.managed_policies):
                if role.trusted_entities:
                    logger.info(f"Role {role.name} has AdministratorAccess and trusted entities: {role.trusted_entities}")
                    vulnerabilities.append(Vulnerability(
                        id=f"iam_role_{role.id}_managed_admin_trusted",
                        name="IAM Role with AdministratorAccess Managed Policy and Trusted Entities",
                        description=(
                            f"IAM role '{role.name}' has the 'AdministratorAccess' managed policy attached "
                            f"and trusts the following entities: {role.trusted_entities}, "
                            "granting them full access to all AWS services and resources."
                        ),
                        severity="Critical",
                        resource_id=role.id,
                        resource_type="IAM Role",
                    ))
                else:
                    vulnerabilities.append(Vulnerability(
                        id=f"iam_role_{role.id}_managed_admin",
                        name="IAM Role with AdministratorAccess Managed Policy",
                        description=(
                            f"IAM role '{role.name}' has the 'AdministratorAccess' managed policy attached, "
                            "which grants full access to all AWS services and resources."
                        ),
                        severity="Medium",
                        resource_id=role.id,
                        resource_type="IAM Role",
                    ))

            wildcard_policies = has_wildcard_permissions(role.inline_policies)
            for p_name in wildcard_policies:
                logger.info(f"Role {role.name} has inline policy {p_name} with wildcard permissions")
                if role.trusted_entities:
                    logger.info(f"Role {role.name} / {p_name} has trusted entities: {role.trusted_entities}")
                    vulnerabilities.append(Vulnerability(
                        id=f"iam_role_{role.id}_inline_{p_name}_wildcard_trusted",
                        name=f"IAM Role with Wildcard Permissions in Inline Policy {p_name} and Trusted Entities",
                        description=(
                            f"IAM role '{role.name}' has an inline policy '{p_name}' that allows wildcard permissions "
                            f"and trusts the following entities: {role.trusted_entities}, "
                            "which may result in excessive privileges and security risks for those entities."
                        ),
                        severity="Critical",
                        resource_id=role.id,
                        resource_type="IAM Role",
                    ))
                else:
                    vulnerabilities.append(Vulnerability(
                        id=f"iam_role_{role.id}_inline_{p_name}_wildcard",
                        name=f"IAM Role with Wildcard Permissions in Inline Policy {p_name}",
                        description=(
                            f"IAM role '{role.name}' has an inline policy '{p_name}' that allows wildcard permissions, "
                            "which may result in excessive privileges and security risks."
                        ),
                        severity="High",
                        resource_id=role.id,
                        resource_type="IAM Role",
                    ))
        return vulnerabilities

    def check_role_privilege_escalation_no_boundary(self, roles: list) -> list:
        """Detects IAM roles that have IAM write permissions but no permissions boundary.

        A permissions boundary caps the maximum effective permissions of a role regardless of
        what policies are later attached to it. Without one, a role that can perform IAM write
        actions (iam:CreateRole, iam:AttachRolePolicy, etc.) can create a new role with
        AdministratorAccess and assume it — effectively bypassing its own permission limits and
        achieving full account takeover (Rhino Security Labs privilege escalation technique, 2018).

        Flags roles that have BOTH conditions:
        1. AdministratorAccess OR any inline policy allowing an IAM escalation action on resource *.
        2. No permissions_boundary set.

        Args:
            roles (list): IAM roles with managed_policies, inline_policies, and permissions_boundary
                          already resolved.

        Returns:
            list[Vulnerability]: severity High, one entry per role that can escalate privileges
            without a boundary cap.
        """
        vulnerabilities = []
        for role in roles:
            if role.permissions_boundary is not None:
                continue

            has_admin = is_admin(role.managed_policies)
            has_iam_write = self._has_iam_escalation_permissions(role.inline_policies)

            if not (has_admin or has_iam_write):
                continue

            reason = "AdministratorAccess managed policy" if has_admin else "IAM write permissions in inline policies"
            vulnerabilities.append(Vulnerability(
                id=f"iam_role_{role.id}_escalation_no_boundary",
                name="IAM Role with Privilege Escalation Potential and No Permissions Boundary",
                description=(
                    f"IAM role '{role.name}' has {reason} and no permissions boundary. "
                    "Without a boundary, this role can create new IAM roles or users with "
                    "AdministratorAccess, bypassing its own permission limits and achieving "
                    "full account control. A permissions boundary caps the maximum effective "
                    "permissions regardless of what policies are attached to child identities."
                ),
                severity="High",
                resource_id=role.id,
                resource_type="IAM Role",
            ))
        return vulnerabilities

    def _has_iam_escalation_permissions(self, inline_policies: list) -> bool:
        """Returns True if any Allow inline policy grants an IAM escalation action on resource *.

        Args:
            inline_policies (list): normalized inline policies (effect, actions, resources).

        Returns:
            bool: True if at least one policy could enable privilege escalation.
        """
        for policy in inline_policies:
            if policy.get('effect') != 'Allow':
                continue
            actions = set(policy.get('actions') or [])
            resources = policy.get('resources') or []
            if '*' not in resources:
                continue
            if actions & _IAM_ESCALATION_ACTIONS:
                return True
        return False
