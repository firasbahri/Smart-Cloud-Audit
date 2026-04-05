from datetime import datetime, timezone
import logging

from Model.vulnerability import Vulnerability

logger = logging.getLogger(__name__)


class IAMAnalyzer:
    def check_user_permissions(self, users):
        vulnerabilities = []
        for user in users:
            if self.isAdmin(user.policies):
                logger.info(f"User {user.name} has admin permissions")
                vulnerability = Vulnerability(
                    id=f"iam_user_{user.id}_admin_permissions",
                    name="IAM User with Admin Permissions",
                    description=(
                        f"The IAM user '{user.name}' has administrative permissions, "
                        "which can pose a significant risk if the account is compromised."
                    ),
                    severity="High",
                    resource_id=user.id,
                    resource_type="IAM User",
                    origin="Static Analysis",
                )
                vulnerabilities.append(vulnerability)
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
        for policy in policies:
            if policy.get("PolicyName") == "AdministratorAccess":
                return True
        return False
