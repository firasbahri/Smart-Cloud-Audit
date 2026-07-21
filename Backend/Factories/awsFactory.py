from Model.IAM_Model.IAMUser import IAMUser
from Model.IAM_Model.IAMGroup import IAMGroup
from Model.IAM_Model.IAMRole import IAMRole
from Model.EC2_Model.EC2 import EC2
from Model.s3Bucket import S3Bucket
from Model.EC2_Model.SecurityGroup import SecurityGroup
from Model.EC2_Model.Rule import Rule
import logging

logger = logging.getLogger(__name__)

class AWSFactory:
    """Convierte las respuestas crudas de boto3 (diccionarios con claves en PascalCase, tal como las devuelve
    la API de AWS) en los modelos de dominio que usa el resto de la app. No hace llamadas a AWS, solo traduce datos."""

    @staticmethod
    def create_users(usersRaw):
        """Convierte usuarios IAM crudos a IAMUser, normalizando las políticas inline al formato interno
        (policy_name/actions/resources/effect) y tratando al usuario root como un caso especial sin políticas.

        Args:
            usersRaw (list[dict]): usuarios tal como los devuelve scan_users(), con los campos extra ya añadidos.

        Returns:
            list[IAMUser]: un IAMUser por cada entrada de usersRaw.
        """
        users = []
        for u in usersRaw:

            if u['UserName'] == 'root':
                logger.info("Creating root user")
                userRoot = IAMUser(
                    id=u['UserId'],
                    name=u['UserName'],
                    service='IAM',
                    region='global',
                    access_keys=u.get('AccessKeyMetadata', []),
                    date=u.get('CreateDate', ''),
                    managed_policies=[],
                    inline_policies=[],
                    mfa_enabled=u.get('Mfa_enabled'),
                    password_last_used=u.get('PasswordLastUsed', None)
                )
                users.append(userRoot)

            else:
                inline_policies_normalized = []
                for p in u.get('InlinePolicies', []):
                    for s in p.get('PolicyDocument', {}).get('Statement', []):
                        logger.info(f"Normalizing inline policy {p['PolicyName']} for user {u['UserName']}")
                        inline_policies_normalized.append({
                            "policy_name": p["PolicyName"],
                            "actions": s.get("Action") if isinstance(s.get("Action"), list) else [s.get("Action")],
                            "resources": s.get("Resource") if isinstance(s.get("Resource"), list) else [s.get("Resource")],
                            "effect": s.get("Effect")
                        })

                user = IAMUser(
                    id=u['UserId'],
                    name=u['UserName'],
                    service='IAM',
                    region='global',
                    access_keys=u.get('AccessKeyMetadata', []),
                    date=u.get('CreateDate', ''),
                    managed_policies=[{"policy_name": p["PolicyName"]} for p in u.get('AttachedManagedPolicies', [])],
                    inline_policies=inline_policies_normalized,
                    mfa_enabled=u.get('Mfa_enabled', False),
                    password_last_used=u.get('PasswordLastUsed', None),
                    console_access=u.get('ConsoleAccess'),
                    mfa_devices=u.get('MfaDevices', []),
                    tags=u.get('Tags', []),
                )
                logger.info(f"access_keys for user {user.name}: {user.access_keys}")
                users.append(user)
        return users

    @staticmethod
    def create_groups(groupsRaw):
        """Convierte grupos IAM crudos a IAMGroup, con la misma normalización de políticas inline que create_users.

        Args:
            groupsRaw (list[dict]): grupos tal como los devuelve scan_groups().

        Returns:
            list[IAMGroup]
        """
        groups = []
        for g in groupsRaw:
            inline_policies_normalized = []
            for policy in g.get('InlinePolicies', []):
                for statement in policy.get('PolicyDocument', {}).get('Statement', []):
                    logger.info(f"Normalizing inline policy {policy['PolicyName']} for group {g['GroupName']}")
                    inline_policies_normalized.append({
                        "policy_name": policy["PolicyName"],
                        "actions": statement.get("Action") if isinstance(statement.get("Action"), list) else [statement.get("Action")],
                        "resources": statement.get("Resource") if isinstance(statement.get("Resource"), list) else [statement.get("Resource")],
                        "effect": statement.get("Effect")
                    })
            group = IAMGroup(
                id=g.get('GroupId', ''),
                name=g.get('GroupName', ''),
                service='IAM',
                region='global',
                Creation_date=g.get('CreateDate'),
                users=g.get('Users', []),
                managed_policies=[{"policy_name": p["PolicyName"]} for p in g.get('AttachedManagedPolicies', [])],
                inline_policies=inline_policies_normalized
            )
            groups.append(group)
        return groups

    @staticmethod
    def create_roles(rolesRaw):
        """Convierte roles IAM crudos a IAMRole. Además de las políticas, extrae quién puede asumir el rol
        (trusted_entities) a partir de su trust policy — eso es lo que usa IAM_Analyzer para detectar roles
        privilegiados accesibles desde fuera de la cuenta.

        Args:
            rolesRaw (list[dict]): roles tal como los devuelve scan_roles().

        Returns:
            list[IAMRole]
        """
        roles = []
        for r in rolesRaw:
            inline_policies_normalized = []
            for policy in r.get('InlinePolicies', []):
                for statement in policy.get('PolicyDocument', {}).get('Statement', []):
                    inline_policies_normalized.append({
                        "policy_name": policy["PolicyName"],
                        "actions": statement.get("Action") if isinstance(statement.get("Action"), list) else [statement.get("Action")],
                        "resources": statement.get("Resource") if isinstance(statement.get("Resource"), list) else [statement.get("Resource")],
                        "effect": statement.get("Effect")
                    })
            trust_policy = r.get('TrustPolicy', {})
            # is_service_role: True si TODOS los principals de la trust policy son servicios AWS
            service_principals = [
                p
                for stmt in trust_policy.get('Statement', [])
                for p in ([stmt.get('Principal', {}).get('Service', [])]
                           if isinstance(stmt.get('Principal', {}).get('Service'), str)
                           else stmt.get('Principal', {}).get('Service', []))
            ]
            aws_principals = [
                p
                for stmt in trust_policy.get('Statement', [])
                for p in ([stmt.get('Principal', {}).get('AWS', [])]
                           if isinstance(stmt.get('Principal', {}).get('AWS'), str)
                           else stmt.get('Principal', {}).get('AWS', []))
            ]
            is_service_role = bool(service_principals) and not bool(aws_principals)

            role = IAMRole(
                id=r.get('RoleId', ''),
                name=r.get('RoleName', ''),
                service='IAM',
                region='global',
                Creation_date=r.get('CreateDate',''),
                assume_role_policy=r.get('AssumeRolePolicyDocument'),
                managed_policies=[{"policy_name": p["PolicyName"]} for p in r.get('AttachedManagedPolicies', [])],
                inline_policies=inline_policies_normalized,
                trusted_entities=extract_trusted_entities(trust_policy),
                permissions_boundary=r.get('PermissionsBoundary'),
                is_service_role=is_service_role,
                tags=r.get('Tags', []),
            )
            roles.append(role)
        return roles

    @staticmethod
    def create_security_groups(securityGroupsRaw):
        """Convierte grupos de seguridad EC2 crudos a SecurityGroup, delegando las reglas de entrada/salida a create_rules.

        Args:
            securityGroupsRaw (list[dict]): grupos de seguridad tal como vienen en instance['SecurityGroupsDetails'].

        Returns:
            list[SecurityGroup]
        """
        security_groups = []
        for sg in securityGroupsRaw:
            logger.info(f"Creating security group ,{sg} ")
            rules_created = AWSFactory.create_rules(sg.get('IpPermissions', []))
            security_group = SecurityGroup(
                id=sg['GroupId'],
                rules=rules_created
            )
            security_groups.append(security_group)
        return security_groups

    @staticmethod
    def create_ec2(instancesRaw):
        """Convierte instancias EC2 crudas a EC2, incluyendo sus grupos de seguridad ya convertidos.

        Args:
            instancesRaw (list[dict]): instancias tal como las devuelve scan_ec2() (ya con volumes,
                SecurityGroupsDetails y public_ip añadidos).

        Returns:
            list[EC2]
        """
        instances = []
        for i in instancesRaw:
            instance = EC2(
                id=i.get('InstanceId', ''),
                name=i.get('InstanceType', ''),
                service='EC2',
                region=i.get('Placement', {}).get('AvailabilityZone', ''),
                date=i.get('LaunchTime'),
                instance_type=i.get('InstanceType', ''),
                public_ip=i.get('PublicIpAddress', None),
                state=i.get('State', {}).get('Name', ''),
                security_groups=AWSFactory.create_security_groups(i.get('SecurityGroupsDetails', [])),
                volumes=i.get('volumes') or [],
                tags=i.get('Tags', []),
                http_tokens=i.get('http_tokens'),
                http_endpoint=i.get('http_endpoint'),
                instance_profile=i.get('instance_profile'),
                user_data=i.get('user_data'),
                monitoring_state=i.get('monitoring_state'),
                virtualization_type=i.get('virtualization_type'),
                private_ip=i.get('private_ip'),
                subnet_id=i.get('subnet_id'),
            )
            instances.append(instance)
        return instances


    @staticmethod
    def create_rules(rulesRaw):
      """Convierte reglas de un grupo de seguridad (IpPermissions de boto3) a objetos Rule, quedándose solo
      con protocolo, rango de puertos y los CIDR permitidos.

      Args:
          rulesRaw (list[dict]): entradas de IpPermissions tal como las devuelve describe_security_groups.

      Returns:
          list[Rule]
      """
      rules = []
      for r in rulesRaw:
          rule = Rule(
              protocol=r.get('IpProtocol', ''),
              from_port=r.get('FromPort'),
              to_port=r.get('ToPort'),
              ip_ranges=[ip.get('CidrIp', '') for ip in r.get('IpRanges', [])]
            )
          rules.append(rule)
      return rules

    @staticmethod
    def create_buckets(bucketsRaw):
        """Convierte buckets S3 crudos a S3Bucket.

        Args:
            bucketsRaw (list[dict]): buckets tal como los devuelve scan_s3().

        Returns:
            list[S3Bucket]
        """
        buckets = []
        for b in bucketsRaw:
            bucket = S3Bucket(
                id=b.get('Name', ''),
                name=b.get('Name', ''),
                service='S3',
                region=b.get('Region', ''),
                Creation_date=b.get('CreationDate', ''),
                public_access=b.get('PublicAccess'),
                versioning=b.get('Versioning'),
                encryption=b.get('Encryption'),
                bucket_policy=b.get('Policies'),
                block_public_acls=b.get('BlockPublicAcls'),
                ignore_public_acls=b.get('IgnorePublicAcls'),
                block_public_policy=b.get('BlockPublicPolicy'),
                restrict_public_buckets=b.get('RestrictPublicBuckets'),
                acl_grantees=b.get('AclGrantees', []),
                logging=b.get('Logging', False),
                logging_target_bucket=b.get('LoggingTargetBucket'),
                object_lock=b.get('ObjectLock', False),
                mfa_delete=b.get('MFADelete', False),
                lifecycle=b.get('Lifecycle', []),
                replication_rules=b.get('ReplicationRules', []),
                notification_config=b.get('NotificationConfig', {}),
            )
            buckets.append(bucket)
        return buckets


def extract_trusted_entities(trust_policy):
    """Saca de una trust policy de IAM (el AssumeRolePolicyDocument de un rol) qué cuentas/usuarios AWS o qué
    servicios AWS pueden asumir ese rol.

    Recorre los statements de la policy y junta los principals de tipo "AWS" (cuentas/usuarios/roles externos)
    y "Service" (servicios AWS como ec2.amazonaws.com), aceptando que cada uno puede venir como string suelto
    o como lista.

    Args:
        trust_policy (dict): documento de confianza del rol, con la forma {"Statement": [...]}.

    Returns:
        list[str]: ARNs o nombres de servicio que pueden asumir el rol. Vacía si no hay ninguno o el dict viene vacío.

    Example:
        >>> extract_trusted_entities({"Statement": [{"Principal": {"AWS": "arn:aws:iam::123456789012:root"}}]})
        ['arn:aws:iam::123456789012:root']
    """
    trusted_entities = []
    for statement in trust_policy.get('Statement', []):
        principal = statement.get('Principal', {})
        if 'AWS' in principal:
            aws_principals = principal['AWS']
            if isinstance(aws_principals, str):
                trusted_entities.append(aws_principals)
            elif isinstance(aws_principals, list):
                trusted_entities.extend(aws_principals)
        if 'Service' in principal:
            service_principals = principal['Service']
            if isinstance(service_principals, str):
                trusted_entities.append(service_principals)
            elif isinstance(service_principals, list):
                trusted_entities.extend(service_principals)
    return trusted_entities
