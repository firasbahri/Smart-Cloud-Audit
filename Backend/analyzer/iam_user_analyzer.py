from datetime import datetime, timezone
import logging

from Model.vulnerability import Vulnerability
from analyzer._iam_helpers import is_admin, has_wildcard_permissions

logger = logging.getLogger(__name__)


class IAMUserAnalyzer:
    """Static security rules for IAM users: root hardening, MFA, permissions, inactivity,
    access-key hygiene, and virtual-MFA quality for high-privilege accounts."""

    def analyze(self, users: list) -> list:
        """Run all user checks and return the combined findings.

        Args:
            users (list): IAM users from the domain model (root user is expected at index 0).

        Returns:
            list[Vulnerability]: union of all individual check results.
        """
        vulnerabilities = []
        vulnerabilities.extend(self.check_root_access_keys(users))
        vulnerabilities.extend(self.check_root_mfa(users))
        vulnerabilities.extend(self.check_user_permissions(users))
        vulnerabilities.extend(self.check_mfa(users))
        vulnerabilities.extend(self.check_inactive_users(users))
        vulnerabilities.extend(self.check_virtual_mfa_high_privilege(users))
        vulnerabilities.extend(self.check_two_active_access_keys(users))
        vulnerabilities.extend(self.check_access_key_rotation(users))
        return vulnerabilities

    def check_root_access_keys(self, users: list) -> list:
        """Detects if the AWS root account has active access keys.

        The root account has unrestricted access to every resource in the AWS account
        and cannot be limited by IAM policies or Service Control Policies. Using access
        keys tied to root means any credential leak — from a compromised CI pipeline,
        a leaked .env file, or a phishing attack — gives an attacker irrevocable,
        unloggable-without-CloudTrail control over the entire account.
        AWS explicitly recommends never creating root access keys; all programmatic
        operations should use IAM users or roles with least-privilege policies.

        Root access keys are detected via the 'AccountAccessKeysPresent' field from
        get_account_summary, stored as synthetic {'Status': 'Active'} entries in the
        root user's access_keys list by awsFactory.

        Logic adapted from Prowler's iam_no_root_access_key (Apache 2.0).

        Args:
            users (list): IAM users including the synthetic root user entry.

        Returns:
            list[Vulnerability]: severity Critical if the root account has any active key.
        """
        vulnerabilities = []
        if not users or users[0].name != 'root':
            return vulnerabilities
        user = users[0]
        active_keys = [k for k in (user.access_keys or []) if k.get('Status') == 'Active']
        if active_keys:
            vulnerabilities.append(Vulnerability(
                id="iam_root_access_key_present",
                name="AWS Root Account Has Active Access Keys",
                description=(
                    "The AWS root account has one or more active access keys. "
                    "Root credentials cannot be restricted by IAM policies — any key compromise "
                    "grants the attacker complete, unrestricted control over the entire account, "
                    "including the ability to delete all resources, create shadow admin accounts, "
                    "and cover their tracks. Delete root access keys immediately and use IAM roles "
                    "with least-privilege permissions for all programmatic operations."
                ),
                severity="Critical",
                resource_id="root",
                resource_type="IAM User",
            ))
        return vulnerabilities

    def check_root_mfa(self, users: list) -> list:
        """Detects if the AWS root account does not have MFA enabled.

        The root account has unconditional access to every AWS service and resource,
        cannot be restricted by any IAM policy, and bypasses Service Control Policies
        in AWS Organizations. Without MFA, an attacker who obtains the root password
        (via phishing, credential stuffing, or a breach of the email account associated
        with the AWS account) gains immediate, unrevocable control of the entire account.
        AWS requires MFA on root as a baseline control (CIS AWS Foundations Benchmark 1.5).

        Root MFA status is read from AccountMFAEnabled in get_account_summary, stored
        as mfa_enabled on the synthetic root user entry.

        Logic adapted from Prowler's iam_root_mfa_enabled (Apache 2.0).

        Args:
            users (list): IAM users including the synthetic root user entry.

        Returns:
            list[Vulnerability]: severity Critical if root has no MFA device.
        """
        vulnerabilities = []
        if not users or users[0].name != 'root':
            return vulnerabilities
        user = users[0]
        if user.mfa_enabled is None:
            return vulnerabilities  # field not collected in this scan
        if not user.mfa_enabled:
            vulnerabilities.append(Vulnerability(
                id="iam_root_mfa_not_enabled",
                name="AWS Root Account Has No MFA",
                description=(
                    "The AWS root account does not have multi-factor authentication enabled. "
                    "Root has unrestricted access to all AWS services and cannot be limited by "
                    "any IAM policy — a compromised root password alone is sufficient for a "
                    "complete account takeover. Enable MFA on the root account immediately; "
                    "AWS recommends a hardware security key (FIDO2/U2F) for this account "
                    "(CIS AWS Foundations Benchmark 1.5)."
                ),
                severity="Critical",
                resource_id="root",
                resource_type="IAM User",
            ))
        return vulnerabilities

    def check_user_permissions(self, users: list) -> list:
        """Marks users with AdministratorAccess or an inline policy that combines action and
        resource wildcards (*), both of which effectively grant full account control.

        Args:
            users (list): IAM users with managed_policies and inline_policies already resolved.

        Returns:
            list[Vulnerability]: severity Critical, one entry per excessive-permission finding.
        """
        vulnerabilities = []
        for user in users:
            if is_admin(user.managed_policies):
                logger.info(f"User {user.name} has AdministratorAccess managed policy")
                vulnerabilities.append(Vulnerability(
                    id=f"iam_user_{user.id}_managed_admin",
                    name="IAM User with AdministratorAccess Managed Policy",
                    description=(
                        f"IAM user '{user.name}' has the 'AdministratorAccess' managed policy attached, "
                        "which grants full access to all AWS services and resources."
                    ),
                    severity="Critical",
                    resource_id=user.id,
                    resource_type="IAM User",
                ))

            wildcard_policies = has_wildcard_permissions(user.inline_policies)
            for p_name in wildcard_policies:
                logger.info(f"User {user.name} has inline policy {p_name} with wildcard permissions")
                vulnerabilities.append(Vulnerability(
                    id=f"iam_user_{user.id}_inline_{p_name}_wildcard",
                    name=f"IAM User with Wildcard Permissions in Inline Policy {p_name}",
                    description=(
                        f"IAM user '{user.name}' has an inline policy '{p_name}' that allows wildcard permissions, "
                        "which may result in excessive privileges and security risks."
                    ),
                    severity="Critical",
                    resource_id=user.id,
                    resource_type="IAM User",
                ))
        return vulnerabilities

    def check_mfa(self, users: list) -> list:
        """Detects IAM users without MFA, with severity adjusted by whether they have console access.

        All users without MFA are a risk, but the specific exposure differs:
        - Console users (console_access=True): an attacker who obtains the password via phishing,
          credential stuffing, or brute force gains immediate interactive access to the AWS console
          with no second factor required. Severity High.
        - Programmatic-only users or scans where console_access was not collected (False or None):
          access keys do not use MFA at all, so the risk is a weaker credential-theft scenario
          with no direct console path. Severity Medium.

        The vulnerability ID (iam_user_{id}_mfa_not_enabled) is the same in both cases so that
        existing audit records from before the console_access field was introduced are not
        duplicated when re-auditing the same account.

        Logic adapted from Prowler's iam_user_mfa_enabled_console_access (Apache 2.0).

        Args:
            users (list): IAM users with mfa_enabled and console_access already resolved.

        Returns:
            list[Vulnerability]: one entry per user without MFA; severity High if console
            access is confirmed, Medium otherwise.
        """
        vulnerabilities = []
        for user in users:
            if user.name == 'root':
                continue  # root MFA is handled by check_root_mfa with Critical severity
            logger.info(f"User {user.name}: mfa_enabled={user.mfa_enabled}, console_access={user.console_access}")
            if not user.mfa_enabled:
                if user.console_access:
                    severity = "High"
                    description = (
                        f"IAM user '{user.name}' has a console login profile but no MFA device registered. "
                        "An attacker who obtains the password — through phishing, credential stuffing, or brute force — "
                        "gains immediate interactive access to the AWS console with no second factor to block them. "
                        "Enable MFA on all users with console access."
                    )
                else:
                    severity = "Medium"
                    description = (
                        f"IAM user '{user.name}' does not have multi-factor authentication (MFA) enabled, "
                        "which increases the risk of unauthorized access to the account."
                    )
                vulnerabilities.append(Vulnerability(
                    id=f"iam_user_{user.id}_mfa_not_enabled",
                    name="IAM User without Multi-Factor Authentication (MFA)",
                    description=description,
                    severity=severity,
                    resource_id=user.id,
                    resource_type="IAM User",
                ))
        return vulnerabilities

    def check_inactive_users(self, users: list) -> list:
        """Finds users inactive for more than 90 days (no password use and no active key activity).

        A valid but long-unused account is an easy target if credentials are ever leaked —
        no one will notice anomalous activity. Only flagged if the user has at least one active
        access key (no active key means nothing to compromise).

        Args:
            users (list): IAM users with password_last_used and access_keys already resolved.

        Returns:
            list[Vulnerability]: severity Low, one entry per inactive user detected.
        """
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
                vulnerabilities.append(Vulnerability(
                    id=f"iam_user_{user.id}_inactive",
                    name="Inactive IAM User",
                    description=(
                        f"IAM user '{user.name}' has not used their password or active access keys "
                        "for more than 90 days, indicating the account may be inactive and representing a security risk."
                    ),
                    severity="Low",
                    resource_id=user.id,
                    resource_type="IAM User",
                ))
        logger.info("check_inactive_users processed")
        return vulnerabilities

    def check_virtual_mfa_high_privilege(self, users: list) -> list:
        """Detects high-privilege IAM users whose only MFA devices are virtual (TOTP apps).

        Virtual MFA (authenticator apps) is weaker than hardware tokens (YubiKey, etc.) for
        administrative accounts because TOTP seeds can be extracted from a compromised phone,
        and phishing kits can perform real-time TOTP relay (AiTM attacks), bypassing virtual MFA.
        Hardware tokens require physical possession of the device and cannot be remotely cloned.
        AWS recommends hardware MFA for root and admin users (CIS AWS Foundations Benchmark 1.6).

        Users with no MFA devices at all are skipped (caught by check_mfa).
        Non-admin users are skipped; virtual MFA is acceptable for lower-privilege accounts.

        Logic adapted from Prowler's iam_user_hardware_mfa_enabled (Apache 2.0).

        Args:
            users (list): IAM users with managed_policies and mfa_devices already resolved.

        Returns:
            list[Vulnerability]: severity Medium, one entry per high-privilege user with only virtual MFA.
        """
        vulnerabilities = []
        for user in users:
            if user.mfa_devices is None:
                continue
            if not user.mfa_devices:
                continue
            if not is_admin(user.managed_policies):
                continue
            if all(d.get('type') == 'virtual' for d in user.mfa_devices):
                vulnerabilities.append(Vulnerability(
                    id=f"iam_user_{user.id}_virtual_mfa_only",
                    name="High-Privilege IAM User with Virtual MFA Only",
                    description=(
                        f"IAM user '{user.name}' has AdministratorAccess and uses only virtual MFA devices "
                        f"({', '.join(d['serial_number'] for d in user.mfa_devices)}). "
                        "Virtual MFA (TOTP apps) can be bypassed via real-time phishing relay (AiTM) or seed extraction "
                        "from a compromised device. For accounts with full administrative access, "
                        "a hardware security key (FIDO2/U2F) provides the physical possession guarantee "
                        "that virtual tokens cannot."
                    ),
                    severity="Medium",
                    resource_id=user.id,
                    resource_type="IAM User",
                ))
        return vulnerabilities

    def check_two_active_access_keys(self, users: list) -> list:
        """Detects IAM users who have two or more access keys in Active status simultaneously.

        AWS allows two keys per user specifically to facilitate zero-downtime rotation —
        the second key should be Active only transiently during the rotation window, then
        the old key should be deactivated and deleted. Both permanently active means
        doubled attack surface: a leaked key cannot be revoked without disruption.

        Logic adapted from Prowler's iam_user_two_active_access_keys (Apache 2.0).

        Args:
            users (list): IAM users with access_keys already resolved.

        Returns:
            list[Vulnerability]: severity High, one entry per user with 2+ active keys.
        """
        vulnerabilities = []
        for user in users:
            if user.name == 'root':
                continue
            if user.access_keys is None:
                continue
            active_keys = [k for k in user.access_keys if k.get('Status') == 'Active']
            if len(active_keys) >= 2:
                vulnerabilities.append(Vulnerability(
                    id=f"iam_user_{user.id}_two_active_access_keys",
                    name="IAM User with Two Active Access Keys",
                    description=(
                        f"IAM user '{user.name}' has {len(active_keys)} active access keys simultaneously. "
                        "AWS allows two keys per user to facilitate zero-downtime rotation, but both should "
                        "never be active for longer than the rotation window. Keeping two permanent active keys "
                        "doubles the credential attack surface — a leaked key cannot be revoked without disruption. "
                        "Complete the rotation and deactivate the old key."
                    ),
                    severity="High",
                    resource_id=user.id,
                    resource_type="IAM User",
                ))
        return vulnerabilities

    def check_access_key_rotation(self, users: list) -> list:
        """Detects IAM users with active access keys older than 90 days that have not been rotated.

        Long-lived credentials accumulate exposure: if a key was leaked at any point in those
        90+ days the attacker has had undetected access for the entire period. Regular rotation
        limits the blast radius of any single key compromise.
        CIS AWS Foundations Benchmark 1.14 recommends 90-day rotation.

        Only Active keys are checked. The root user and keys without CreateDate are skipped.

        Logic adapted from Prowler's iam_user_accesskey_unused (Apache 2.0).

        Args:
            users (list): IAM users with access_keys (including CreateDate) already resolved.

        Returns:
            list[Vulnerability]: severity Medium, one entry per stale active key found.
        """
        vulnerabilities = []
        for user in users:
            if user.name == 'root':
                continue
            if user.access_keys is None:
                continue
            for key in user.access_keys:
                if key.get('Status') != 'Active':
                    continue
                create_date = key.get('CreateDate')
                if not create_date:
                    continue
                if isinstance(create_date, str):
                    try:
                        create_date = datetime.fromisoformat(create_date.replace('Z', '+00:00'))
                    except ValueError:
                        continue
                age_days = (datetime.now(timezone.utc) - create_date).days
                if age_days > 90:
                    key_id = key.get('AccessKeyId', 'unknown')
                    vulnerabilities.append(Vulnerability(
                        id=f"iam_user_{user.id}_key_{key_id}_not_rotated",
                        name="IAM User Access Key Not Rotated in 90+ Days",
                        description=(
                            f"IAM user '{user.name}' has access key '{key_id}' that was created "
                            f"{age_days} days ago and has never been rotated. "
                            "Long-lived credentials increase the window of opportunity for an "
                            "undetected compromise — a key leaked at any point in that period "
                            "grants an attacker persistent access. Rotate the key and deactivate "
                            "the old one (CIS AWS Foundations Benchmark 1.14)."
                        ),
                        severity="Medium",
                        resource_id=user.id,
                        resource_type="IAM User",
                    ))
        return vulnerabilities
