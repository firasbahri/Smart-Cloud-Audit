from datetime import datetime, timezone
import logging

from Model.vulnerability import Vulnerability

logger = logging.getLogger(__name__)


class IAMAnalyzer:
    def check_user_permissions(self, users):
        vulnerabilities = []
        for user in users:
            if self.isAdmin(user.managed_policies):
                logger.info(f"User {user.name} has AdministratorAccess managed policy")
                vulnerabilities.append(Vulnerability(
                    id=f"iam_user_{user.id}_managed_admin",
                    name="IAM User with AdministratorAccess Managed Policy",
                    description=(
                        f"The IAM user '{user.name}' has the 'AdministratorAccess' managed policy attached, "
                        "granting full access to all AWS services and resources."
                    ),
                    severity="Critical",
                    resource_id=user.id,
                    resource_type="IAM User",
                    origin="Static Analysis",
                ))

            wildCardPolicies= self.hasWildcardPermissions(user.inline_policies)
            if wildCardPolicies:
                for pName in wildCardPolicies:
                    logger.info(f"User {user.name} has inline policy {pName} with wildcard permissions")
                    vulnerabilities.append(Vulnerability(
                        id=f"iam_user_{user.id}_inline_{pName}_wildcard",
                        name=f"IAM User with Inline Policy {pName} Wildcard Permissions",
                        description=(
                            f"The IAM user '{user.name}' has an inline policy '{pName}' that allows wildcard permissions, "
                            "which can lead to excessive privileges and potential security risks."
                        ),
                        severity="Critical",
                        resource_id=user.id,
                        resource_type="IAM User",
                        origin="Static Analysis",
                    ))
              
        return vulnerabilities

    def check_group_permissions(self, groups):
        vulnerabilities = []
        logger.info(f"Checking permissions for {len(groups)} groups")
        for group in groups:
            logger.info(f"Checking group {group.name} with managed policies: {group.managed_policies} and inline policies: {group.inline_policies}")
            if self.isAdmin(group.managed_policies):
                logger.info(f"Group {group.name} has AdministratorAccess managed policy")
                vulnerabilities.append(Vulnerability(
                    id=f"iam_group_{group.id}_managed_admin",
                    name="IAM Group with AdministratorAccess Managed Policy",
                    description=(
                        f"The IAM group '{group.name}' has the 'AdministratorAccess' managed policy attached, "
                        "granting full access to all AWS services and resources for all users in the group."
                    ),
                    severity="Critical",
                    resource_id=group.id,
                    resource_type="IAM Group",
                    origin="Static Analysis",
                ))
            wildCardPolicies= self.hasWildcardPermissions(group.inline_policies)
            if wildCardPolicies:
                for pName in wildCardPolicies:
                    logger.info(f"Group {group.name} has inline policy {pName} with wildcard permissions")
                    vulnerabilities.append(Vulnerability(
                        id=f"iam_group_{group.id}_inline_{pName}_wildcard",
                        name=f"IAM Group with Inline Policy {pName} Wildcard Permissions",
                        description=(
                            f"The IAM group '{group.name}' has an inline policy '{pName}' that allows wildcard permissions, "
                        "which can lead to excessive privileges and potential security risks for all users in the group."
                    ),
                    severity="Critical",
                    resource_id=group.id,
                    resource_type="IAM Group",
                    origin="Static Analysis",
                ))

        return vulnerabilities

    def check_mfa(self, users):
        vulnerabilities = []
        for user in users:
            logger.info(f"for user {user.name}, mfa_enabled: {user.mfa_enabled} ")
            if not user.mfa_enabled:
                vulnerabilities.append(
                    Vulnerability(
                        id=f"iam_user_{user.id}_mfa_not_enabled",
                        name="IAM User without MFA Enabled",
                        description=(
                            f"The IAM user '{user.name}' does not have Multi-Factor "
                            "Authentication (MFA) enabled, which can increase the risk "
                            "of unauthorized access."
                        ),
                        severity="Medium",
                        resource_id=user.id,
                        resource_type="IAM User",
                        origin="Static Analysis",
                    )
                )
        return vulnerabilities

    def check_inactive_users(self, users):
        vulnerabilities = []

        for user in users:
            active_user = False
            days_password_active = False
            days_access_key_active = False

            if user.password_last_used:
                days_password = (datetime.now(timezone.utc) - user.password_last_used).days
                days_password_active = days_password > 90

            if user.access_keys:
                for access_key in user.access_keys:
                    if access_key.get("Status") != "Active":
                        continue

                    create_date = access_key.get("CreateDate")
                    if isinstance(create_date, str):
                        try:
                            create_date = datetime.fromisoformat(create_date.replace("Z", "+00:00"))
                        except ValueError:
                            create_date = None

                    active_user = True
                    if create_date:
                        days_access_key = (datetime.now(timezone.utc) - create_date).days
                        days_access_key_active = days_access_key > 90 or days_access_key_active

            if (days_password_active or days_access_key_active) and active_user:
                vulnerabilities.append(
                    Vulnerability(
                        id=f"iam_user_{user.id}_inactive",
                        name="Inactive IAM User",
                        description=(
                            f"The IAM user '{user.name}' has not used their password or "
                            "access keys for over 90 days, which may indicate that the "
                            "account is inactive and could be a security risk."
                        ),
                        severity="Low",
                        resource_id=user.id,
                        resource_type="IAM User",
                        origin="Static Analysis",
                    )
                )

        logger.info("check_inactive_users processed")
        return vulnerabilities

    def isAdmin(self, policies: list) -> bool:
        logger.info(f"Checking policies: {policies}")
        for policy in policies:
            logger.info(f"Checking policy: {policy}")
            if policy.get("policy_name") == "AdministratorAccess": 
                return True
        return False
    
    def hasWildcardPermissions(self, inline_policies: list) -> list:
        policiesWithWildcard = []
        logger.info(f"Checking inline policies for wildcards: {inline_policies}")
        for policy in inline_policies:
            effect = policy.get("effect")
            if effect != "Allow":
                continue
            action=policy.get("actions", [])
            resources=policy.get("resources", [])
            if "*" in action and "*" in resources:
                policiesWithWildcard.append(policy.get("policy_name"))
        return policiesWithWildcard
    
