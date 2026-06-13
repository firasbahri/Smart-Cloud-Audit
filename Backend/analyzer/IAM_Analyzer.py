from datetime import datetime, timezone
import logging

from Model.vulnerability import Vulnerability

logger = logging.getLogger(__name__)


class IAMAnalyzer:
    def analyze(self, users: list, groups: list, roles: list) -> list:
        vulnerabilities = []
        vulnerabilities.extend(self.check_user_permissions(users))
        vulnerabilities.extend(self.check_mfa(users))
        vulnerabilities.extend(self.check_inactive_users(users))
        vulnerabilities.extend(self.check_group_permissions(groups))
        vulnerabilities.extend(self.check_role_permissions(roles))
        return vulnerabilities

    def check_user_permissions(self, users):
        vulnerabilities = []
        for user in users:
            if self.isAdmin(user.managed_policies):
                logger.info(f"User {user.name} has AdministratorAccess managed policy")
                vulnerabilities.append(Vulnerability(
                    id=f"iam_user_{user.id}_managed_admin",
                    name="Usuario IAM con Política Administrada AdministratorAccess",
                    description=(
                        f"El usuario IAM '{user.name}' tiene la política administrada 'AdministratorAccess' adjunta, "
                        "lo que le otorga acceso completo a todos los servicios y recursos de AWS."
                    ),
                    severity="Critical",
                    resource_id=user.id,
                    resource_type="IAM User",
                ))

            wildCardPolicies = self.hasWildcardPermissions(user.inline_policies)
            if wildCardPolicies:
                for pName in wildCardPolicies:
                    logger.info(f"User {user.name} has inline policy {pName} with wildcard permissions")
                    vulnerabilities.append(Vulnerability(
                        id=f"iam_user_{user.id}_inline_{pName}_wildcard",
                        name=f"Usuario IAM con Permisos Comodín en la Política Inline {pName}",
                        description=(
                            f"El usuario IAM '{user.name}' tiene una política inline '{pName}' que permite permisos comodín, "
                            "lo que puede generar privilegios excesivos y riesgos de seguridad."
                        ),
                        severity="Critical",
                        resource_id=user.id,
                        resource_type="IAM User",
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
                    name="Grupo IAM con Política Administrada AdministratorAccess",
                    description=(
                        f"El grupo IAM '{group.name}' tiene la política administrada 'AdministratorAccess' adjunta, "
                        "lo que otorga acceso completo a todos los servicios y recursos de AWS a todos los usuarios del grupo."
                    ),
                    severity="Critical",
                    resource_id=group.id,
                    resource_type="IAM Group",
                ))
            wildCardPolicies = self.hasWildcardPermissions(group.inline_policies)
            if wildCardPolicies:
                for pName in wildCardPolicies:
                    logger.info(f"Group {group.name} has inline policy {pName} with wildcard permissions")
                    vulnerabilities.append(Vulnerability(
                        id=f"iam_group_{group.id}_inline_{pName}_wildcard",
                        name=f"Grupo IAM con Permisos Comodín en la Política Inline {pName}",
                        description=(
                            f"El grupo IAM '{group.name}' tiene una política inline '{pName}' que permite permisos comodín, "
                            "lo que puede generar privilegios excesivos y riesgos de seguridad para todos los usuarios del grupo."
                        ),
                        severity="Critical",
                        resource_id=group.id,
                        resource_type="IAM Group",
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
                        name="Usuario IAM sin Autenticación Multifactor (MFA)",
                        description=(
                            f"El usuario IAM '{user.name}' no tiene habilitada la autenticación multifactor (MFA), "
                            "lo que puede aumentar el riesgo de acceso no autorizado a la cuenta."
                        ),
                        severity="Medium",
                        resource_id=user.id,
                        resource_type="IAM User",
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
                        name="Usuario IAM Inactivo",
                        description=(
                            f"El usuario IAM '{user.name}' no ha utilizado su contraseña ni sus claves de acceso "
                            "durante más de 90 días, lo que puede indicar que la cuenta está inactiva y representa un riesgo de seguridad."
                        ),
                        severity="Low",
                        resource_id=user.id,
                        resource_type="IAM User",
                    )
                )

        logger.info("check_inactive_users processed")
        return vulnerabilities


    def check_role_permissions(self, roles):
        vulnerabilities = []
        for role in roles:
            if self.isAdmin(role.managed_policies):
                if role.trusted_entities:
                    logger.info(f"Role {role.name} has AdministratorAccess managed policy and trusted entities: {role.trusted_entities}")
                    vulnerabilities.append(Vulnerability(
                        id=f"iam_role_{role.id}_managed_admin_trusted",
                        name="Rol IAM con Política Administrada AdministratorAccess y Entidades de Confianza",
                        description=(
                            f"El rol IAM '{role.name}' tiene la política administrada 'AdministratorAccess' adjunta "
                            f"y es de confianza para las entidades {role.trusted_entities}, "
                            "lo que les otorga acceso completo a todos los servicios y recursos de AWS."
                        ),
                        severity="Critical",
                        resource_id=role.id,
                        resource_type="IAM Role",
                    ))
                else:
                    vulnerabilities.append(Vulnerability(
                        id=f"iam_role_{role.id}_managed_admin",
                        name="Rol IAM con Política Administrada AdministratorAccess",
                        description=(
                            f"El rol IAM '{role.name}' tiene la política administrada 'AdministratorAccess' adjunta, "
                            "lo que otorga acceso completo a todos los servicios y recursos de AWS."
                        ),
                        severity="Medium",
                        resource_id=role.id,
                        resource_type="IAM Role",
                    ))

            wildCardPolicies = self.hasWildcardPermissions(role.inline_policies)
            if wildCardPolicies:
                for pName in wildCardPolicies:
                    logger.info(f"Role {role.name} has inline policy {pName} with wildcard permissions")
                    if role.trusted_entities:
                        logger.info(f"Role {role.name} with inline policy {pName} has trusted entities: {role.trusted_entities}")
                        vulnerabilities.append(Vulnerability(
                            id=f"iam_role_{role.id}_inline_{pName}_wildcard_trusted",
                            name=f"Rol IAM con Permisos Comodín en la Política Inline {pName} y Entidades de Confianza",
                            description=(
                                f"El rol IAM '{role.name}' tiene una política inline '{pName}' que permite permisos comodín "
                                f"y es de confianza para las entidades {role.trusted_entities}, "
                                "lo que puede generar privilegios excesivos y riesgos de seguridad para dichas entidades."
                            ),
                            severity="Critical",
                            resource_id=role.id,
                            resource_type="IAM Role",
                        ))
                    else:
                        vulnerabilities.append(Vulnerability(
                            id=f"iam_role_{role.id}_inline_{pName}_wildcard",
                            name=f"Rol IAM con Permisos Comodín en la Política Inline {pName}",
                            description=(
                                f"El rol IAM '{role.name}' tiene una política inline '{pName}' que permite permisos comodín, "
                                "lo que puede generar privilegios excesivos y riesgos de seguridad."
                            ),
                            severity="High",
                            resource_id=role.id,
                            resource_type="IAM Role",
                        ))

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
            action = policy.get("actions", [])
            resources = policy.get("resources", [])
            if "*" in action and "*" in resources:
                policiesWithWildcard.append(policy.get("policy_name"))
        return policiesWithWildcard
