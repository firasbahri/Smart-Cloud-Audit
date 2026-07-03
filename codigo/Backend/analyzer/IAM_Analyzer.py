from datetime import datetime, timezone
import logging

from Model.vulnerability import Vulnerability

logger = logging.getLogger(__name__)


class IAMAnalyzer:
    """Reglas de seguridad estáticas para usuarios, grupos y roles IAM (permisos excesivos, MFA, inactividad...)."""

    def analyze(self, users: list, groups: list, roles: list) -> list:
        """Pasa usuarios, grupos y roles por todas las comprobaciones IAM y junta los hallazgos.

        Args:
            users (list): usuarios IAM ya convertidos al modelo de dominio (incluye el usuario root si se pudo leer).
            groups (list): grupos IAM del modelo de dominio.
            roles (list): roles IAM del modelo de dominio.

        Returns:
            list[Vulnerability]: todos los hallazgos de check_user_permissions, check_mfa, check_inactive_users,
            check_group_permissions y check_role_permissions juntos.
        """
        vulnerabilities = []
        vulnerabilities.extend(self.check_user_permissions(users))
        vulnerabilities.extend(self.check_mfa(users))
        vulnerabilities.extend(self.check_inactive_users(users))
        vulnerabilities.extend(self.check_group_permissions(groups))
        vulnerabilities.extend(self.check_role_permissions(roles))
        return vulnerabilities

    def check_user_permissions(self, users):
        """Marca usuarios con AdministratorAccess o con una política inline que combine acción y recurso en wildcard (*).

        Ambos casos se reportan como severidad Critical porque dan, en la práctica, control total de la cuenta.

        Args:
            users (list): usuarios IAM a revisar, cada uno con managed_policies e inline_policies.

        Returns:
            list[Vulnerability]: una entrada por cada usuario admin y otra por cada política inline con wildcard.
        """
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
        """Igual que check_user_permissions pero a nivel de grupo — el riesgo aquí afecta a todos los miembros del grupo a la vez.

        Args:
            groups (list): grupos IAM a revisar.

        Returns:
            list[Vulnerability]: hallazgos de AdministratorAccess o políticas inline con wildcard por grupo.
        """
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
        """Detecta usuarios sin autenticación multifactor habilitada (severidad Medium, no Critical, porque por sí sola no da acceso).

        Args:
            users (list): usuarios IAM con el campo mfa_enabled ya resuelto por el scanner.

        Returns:
            list[Vulnerability]: un hallazgo por cada usuario sin MFA.
        """
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
        """Busca usuarios que lleven más de 90 días sin usar su contraseña ni sus claves de acceso activas.

        Una cuenta válida pero que nadie usa desde hace meses es un objetivo fácil si sus credenciales se filtran,
        porque nadie va a notar actividad rara. Solo se marca si el usuario tiene al menos una clave de acceso activa
        (si no tiene ninguna, no hay nada que comprometer).

        Args:
            users (list): usuarios IAM con password_last_used y access_keys.

        Returns:
            list[Vulnerability]: severidad Low, un hallazgo por usuario inactivo detectado.
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
        """Revisa permisos excesivos en roles, igual que con usuarios y grupos, pero subiendo la severidad si el rol
        además es asumible por una entidad externa (trusted_entities) — ahí ya no es solo "permisos amplios dentro
        de la cuenta", es "alguien de fuera puede entrar con esos permisos".

        Args:
            roles (list): roles IAM con managed_policies, inline_policies y trusted_entities.

        Returns:
            list[Vulnerability]: Medium/High si el riesgo queda dentro de la cuenta, Critical si hay
            entidades de confianza externas de por medio.
        """
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
        """True si alguna política administrada de la lista es exactamente 'AdministratorAccess'."""
        logger.info(f"Checking policies: {policies}")
        for policy in policies:
            logger.info(f"Checking policy: {policy}")
            if policy.get("policy_name") == "AdministratorAccess":
                return True
        return False

    def hasWildcardPermissions(self, inline_policies: list) -> list:
        """Devuelve los nombres de las políticas inline que permiten ('Allow') acción '*' sobre recurso '*' a la vez.

        Args:
            inline_policies (list): políticas inline ya normalizadas (con effect, actions y resources).

        Returns:
            list[str]: nombres de las políticas que combinan wildcard en acción y en recurso. Vacía si ninguna lo hace.
        """
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
